"""
Broker API with KiteConnect integration - Phase support
Phase 1: Mock data
Phase 2 & 3: Real KiteConnect data
"""
import pandas as pd
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
import time
from config.settings import settings
from utils.logger import setup_logger
from utils.helpers import get_current_time

logger = setup_logger('BrokerAPI', level='INFO')

class BrokerAPI:
    """Broker API wrapper with KiteConnect and Mock support"""
    
    def __init__(self):
        self.connected = False
        self.kite = None
        self.kws = None
        self.subscribed_tokens = []
        self.tick_callbacks = []
        self.latest_ticks = {}  # Store latest ticks from WebSocket
        self.kws_connected = False
        self.pending_tokens = []



    def _safe_subscribe(self, ws, tokens):
        tokens = [int(t) for t in tokens if t is not None]
        if not tokens:
            return
        # de-dupe against what we *believe* is already subscribed
        current = set(self.subscribed_tokens or [])
        to_add = [t for t in tokens if t not in current]
        if not to_add:
            return
        ws.subscribe(to_add)
        try:
            ws.set_mode(ws.MODE_FULL, to_add)  # set mode only for the new tokens
        except Exception as e:
            logger.error(f"set_mode failed for {to_add}: {e}")
        # track after success
        self.subscribed_tokens = list(current.union(to_add))
        logger.info(f"✅ Subscribed new tokens: {to_add}")

    def connect(self):
        """Connect to broker based on phase"""
        try:
            if settings.is_using_real_data():
                # Phase 2 & 3: Real KiteConnect
                from kiteconnect import KiteConnect
                
                self.kite = KiteConnect(api_key=settings.KITE_API_KEY)
                self.kite.set_access_token(settings.KITE_ACCESS_TOKEN)
                
                # Test connection
                profile = self.kite.profile()
                logger.info(f"✅ Connected to KiteConnect - User: {profile.get('user_name', 'N/A')}")
                
            else:
                # Phase 1: Mock mode
                logger.info("✅ Connected in MOCK mode (Phase 1)")
            
            self.connected = True
            
        except ImportError:
            logger.error("❌ kiteconnect library not installed. Run: pip install kiteconnect")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from broker"""
        if self.kws:
            try:
                self.kws.close()
            except:
                pass
        
        self.connected = False
        logger.info("Disconnected from broker")
    def add_tokens(self, tokens):
        """Add tokens now if connected; otherwise queue for next on_connect."""
        tokens = [int(t) for t in tokens if t is not None]
        if not tokens:
            logger.warning("No tokens to add")
            return False

        if not settings.is_using_real_data():
            # mock
            self.subscribed_tokens = list(set((self.subscribed_tokens or []) + tokens))
            logger.info(f"📝 Mock: Added tokens {tokens}")
            return True

        if not self.kws:
            logger.warning("WS not created yet; queuing tokens")
            self.pending_tokens = list(set((self.pending_tokens or []) + tokens))
            return False

        if not self.kws_connected:
            logger.info("WS not connected; queuing tokens for next on_connect")
            self.pending_tokens = list(set((self.pending_tokens or []) + tokens))
            return False

        # Connected: subscribe immediately
        try:
            self._safe_subscribe(self.kws, tokens)
            return True
        except Exception as e:
            logger.error(f"Add tokens failed: {e}")
            # queue for retry on reconnect
            self.pending_tokens = list(set((self.pending_tokens or []) + tokens))
            return False

    def _get_exchange_for_token(self, token: int) -> str:
        """
        Determine exchange (NSE/NFO) for a given token by looking up instruments.csv
        
        Args:
            token: Instrument token
            
        Returns:
            'NSE' for equity/index, 'NFO' for options
        """
        try:
            from data.instruments import instrument_manager
            
            # Look up token in instruments dataframe
            instrument = instrument_manager.instruments_df[
                instrument_manager.instruments_df['token'] == token
            ]
            
            if not instrument.empty:
                option_type = instrument.iloc[0]['option_type']
                # EQ = Equity/Index on NSE, CE/PE = Options on NFO
                if option_type == 'EQ':
                    return 'NSE'
                elif option_type in ['CE', 'PE']:
                    return 'NFO'
            
            # Default to NFO if not found (most instruments are options)
            logger.warning(f"Could not determine exchange for token {token}, defaulting to NFO")
            return 'NFO'
            
        except Exception as e:
            logger.warning(f"Error determining exchange for token {token}: {e}, defaulting to NFO")
            return 'NFO'
    
    def get_historical_data(
        self,
        token: int,
        from_datetime: datetime,
        to_datetime: datetime,
        interval: str = '1minute'
    ) -> pd.DataFrame:
        """Fetch historical OHLC data"""
        
        if settings.is_using_real_data():
            # Phase 2 & 3: Real KiteConnect data
            try:
                # Map interval to Kite format
                kite_intervals = {
                    '1minute': 'minute',
                    '5minute': '5minute',
                    '15minute': '15minute'
                }
                kite_interval = kite_intervals.get(interval, 'minute')
                
                data = self.kite.historical_data(
                    instrument_token=token,
                    from_date=from_datetime,
                    to_date=to_datetime,
                    interval=kite_interval
                )
                
                if not data:
                    logger.warning(f"No historical data returned for token {token}")
                    return pd.DataFrame()
                
                df = pd.DataFrame(data)
                df['datetime'] = pd.to_datetime(df['date'])
                df.set_index('datetime', inplace=True)
                df.drop('date', axis=1, inplace=True)
                
                logger.info(f"Fetched {len(df)} candles for token {token}")
                return df
                
            except Exception as e:
                logger.error(f"Error fetching historical data: {e}")
                return pd.DataFrame()
        
        else:
            # Phase 1: Mock data
            logger.info(f"Using MOCK historical data for token {token}")
            dates = pd.date_range(from_datetime, to_datetime, freq='1min')
            df = pd.DataFrame({
                'datetime': dates,
                'open': 100.0,
                'high': 105.0,
                'low': 95.0,
                'close': 102.0,
                'volume': 1000
            })
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            return df
    
    def start_websocket(self, tokens: List[int], on_tick: Callable):
        """Start WebSocket for real-time data"""
        
        if settings.is_using_real_data():
            # Phase 2 & 3: Real KiteConnect WebSocket
            try:
                from kiteconnect import KiteTicker
                
                self.kws = KiteTicker(
                    api_key=settings.KITE_API_KEY,
                    access_token=settings.KITE_ACCESS_TOKEN
                )
                
                def on_ticks_wrapper(ws, ticks):
                    """Process incoming ticks"""
                    if not ticks:
                        logger.debug("⚠️ Received empty ticks from WebSocket")
                        return
                    
                    logger.debug(f"📡 WebSocket received {len(ticks)} tick(s)")
                    
                    for tick in ticks:
                        token = tick['instrument_token']
                        self.latest_ticks[token] = {
                            'ltp': tick['last_price'],
                            'open': tick.get('ohlc', {}).get('open', tick['last_price']),
                            'high': tick.get('ohlc', {}).get('high', tick['last_price']),
                            'low': tick.get('ohlc', {}).get('low', tick['last_price']),
                            'close': tick['last_price'],
                            'volume': tick.get('volume', 0),
                            'timestamp': tick.get('timestamp', datetime.now())
                        }
                    
                    # Call user callback
                    try:
                        on_tick(ticks)
                    except Exception as e:
                        logger.error(f"❌ Error in tick callback: {e}", exc_info=True)
                
                def on_connect_wrapper(ws, response):
                    self.kws_connected = True
                    logger.info("=" * 80)
                    logger.info("✅ KITE WEBSOCKET CONNECTED")
                    logger.info("=" * 80)
                    logger.info(f"📡 Response: {response}")
                    
                    # (Re)subscribe base + any queued tokens
                    base = [int(t) for t in (self.subscribed_tokens or [])]
                    queued = [int(t) for t in (self.pending_tokens or [])]
                    want = list(set(base + queued))
                    
                    logger.info(f"📊 Tokens to subscribe: {want}")
                    
                    if want:
                        self._safe_subscribe(ws, want)
                    # clear queue after attempting
                    self.pending_tokens = []
                    logger.info(f"✅ Subscribed to {len(self.subscribed_tokens)} instruments")
                    logger.info("=" * 80)

                def on_close_wrapper(ws, code, reason):
                    self.kws_connected = False
                    logger.warning(f"WebSocket closed: {code} - {reason}")

                def on_error_wrapper(ws, code, reason):
                    logger.error(f"WebSocket error: {code} - {reason}")
                
                self.kws.on_ticks = on_ticks_wrapper
                self.kws.on_connect = on_connect_wrapper
                self.kws.on_close = on_close_wrapper
                self.kws.on_error = on_error_wrapper
                
                self.kws.connect(threaded=True)
                self.subscribed_tokens = tokens
                logger.info("🔗 KiteConnect WebSocket started")
                
            except ImportError:
                logger.error("kiteconnect library not installed")
                raise
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                raise
        
        else:
            # Phase 1: Mock WebSocket (just store callback)
            self.subscribed_tokens = tokens
            self.tick_callbacks.append(on_tick)
            logger.info(f"📝 Mock WebSocket started for {len(tokens)} tokens")
    
    def stop_websocket(self):
        """Stop WebSocket connection"""
        if self.kws:
            try:
                self.kws.close()
            except:
                pass
        
        self.subscribed_tokens = []
        self.tick_callbacks = []
        logger.info("WebSocket stopped")
    
    def get_ltp(self, token: int) -> Optional[float]:
        """Get Last Traded Price"""
        
        if settings.is_using_real_data():
            # Phase 2 & 3: Real KiteConnect data
            
            # First try from WebSocket ticks (faster)
            if token in self.latest_ticks:
                return self.latest_ticks[token]['ltp']
            
            # Fallback to REST API using trading symbol
            try:
                from data.instruments import instrument_manager
                
                # Get trading symbol (e.g., 'NSE:NIFTY 50' or 'NFO:NIFTY25O0725000CE')
                trading_symbol = instrument_manager.get_trading_symbol(token)
                
                if not trading_symbol:
                    logger.error(f"Could not find trading symbol for token {token}")
                    return None
                
                ltp_data = self.kite.ltp([trading_symbol])
                return ltp_data[trading_symbol]['last_price']
            except Exception as e:
                logger.error(f"Error fetching LTP for token {token}: {e}")
                return None
        
        else:
            # Phase 1: Mock LTP
            return 100.0 + (token % 100)  # Some variation based on token
    
    def get_quote(self, token: int) -> Optional[Dict]:
        """Get full quote (OHLC, LTP, volume)"""
        
        if settings.is_using_real_data():
            # Phase 2 & 3: Real KiteConnect data
            
            # Try from WebSocket first
            if token in self.latest_ticks:
                tick = self.latest_ticks[token]
                return {
                    'last_price': tick['ltp'],
                    'ohlc': {
                        'open': tick['open'],
                        'high': tick['high'],
                        'low': tick['low'],
                        'close': tick['close']
                    },
                    'volume': tick['volume']
                }
            
            # Fallback to REST API using trading symbol
            try:
                from data.instruments import instrument_manager
                
                # Get trading symbol (e.g., 'NSE:NIFTY 50' or 'NFO:NIFTY25O0725000CE')
                trading_symbol = instrument_manager.get_trading_symbol(token)
                
                if not trading_symbol:
                    logger.error(f"Could not find trading symbol for token {token}")
                    return None
                
                quote = self.kite.quote([trading_symbol])
                return quote[trading_symbol]
            except Exception as e:
                logger.error(f"Error fetching quote for token {token}: {e}")
                return None
        
        else:
            # Phase 1: Mock quote
            return {
                'last_price': 100.0,
                'ohlc': {
                    'open': 98.0,
                    'high': 105.0,
                    'low': 95.0,
                    'close': 102.0
                },
                'volume': 10000
            }
    
    def get_tick_data(self, token: int) -> Optional[Dict]:
        """Get latest tick from WebSocket cache"""
        return self.latest_ticks.get(token)

# Global instance
broker_api = BrokerAPI()