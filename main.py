"""
Main trading bot - Live/Paper trading with WebSocket
"""
import time
import signal
import sys
from datetime import datetime, time as dt_time
from typing import Optional, Dict
import pandas as pd

from config.settings import settings
from utils.logger import setup_logger, get_logger
from utils.helpers import get_current_time, is_market_open, is_between_times, generate_trade_id
from utils.candle_aggregator import candle_aggregator
from utils.data_storage import data_storage
from data.broker_api import broker_api
from data.instruments import instrument_manager
from strategy.reference_levels import reference_calculator
from strategy.strike_selector import strike_selector
from strategy.breakout_logic import breakout_detector
from strategy.stop_loss import stop_loss_manager
from strategy.indicators import get_latest_rsi, track_rsi_peak, check_rsi_exit_condition
from execution.order_manager import order_manager
from execution.paper_trading import paper_trading_manager

# Setup logger
logger = setup_logger('TradingBot', settings.LOG_FILE_PATH, settings.LOG_LEVEL)

class TradingBot:
    """Main trading bot orchestrator with WebSocket support"""
    
    def __init__(self):
        self.running = False
        self.reference_levels_set = False
        self.strikes_selected = False
        self.in_position = False
        self.current_trade_id: Optional[str] = None
        self.current_side: Optional[str] = None
        self.entry_price: Optional[float] = None
        self.rsi_peak: Optional[float] = None
        
        # Instrument tokens
        self.nifty_token: Optional[int] = None
        self.call_token: Optional[int] = None
        self.put_token: Optional[int] = None
        
        # Daily P&L tracking
        self.daily_pnl = 0.0
        
        # WebSocket subscribed flag
        self.websocket_started = False
        
        # Late start tracking - if script starts after 10:00 AM
        self.started_after_10am = False
        self.neutral_zone_validated = False  # Track if last 5-min candle closed between RN/GN
        
        # Tick tracking for debugging
        self.tick_count = 0
        self.nifty_tick_count = 0
        self.last_tick_log_time = None
    
    def start(self):
        """Start the trading bot"""
        logger.info("\n" + "="*80)
        logger.info("🚀 NIFTY OPTIONS TRADING BOT STARTING...")
        logger.info("="*80)
        
        # Validate configuration
        if not settings.validate():
            logger.error("Configuration validation failed. Exiting.")
            return
        
        settings.print_config()
        
        # Connect to broker
        try:
            broker_api.connect()
        except Exception as e:
            logger.error(f"Failed to connect to broker: {e}")
            return
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Get Nifty token early
        self.nifty_token = instrument_manager.get_nifty_token()
        if not self.nifty_token:
            logger.error("❌ Nifty token not found in instruments.csv")
            return
        
        logger.info(f"📊 Nifty Token: {self.nifty_token}")
        
        # Register Nifty instrument name in candle aggregator
        candle_aggregator.register_instrument_name(self.nifty_token, "NIFTY50")
        
        # Subscribe to Nifty from the start
        self._subscribe_nifty()
        
        self.running = True
        
        # Main trading loop
        try:
            self._trading_loop()
        except Exception as e:
            logger.error(f"Fatal error in trading loop: {e}", exc_info=True)
        finally:
            self._shutdown()
    
    def _subscribe_nifty(self):
        """Subscribe to Nifty spot from market open"""
        try:
            logger.info("=" * 80)
            logger.info("🔗 SUBSCRIBING TO NIFTY 50 WEBSOCKET")
            logger.info("=" * 80)
            logger.info(f"📊 Nifty Token: {self.nifty_token}")
            logger.info(f"📡 Starting WebSocket connection...")
            
            # Start WebSocket with Nifty token
            broker_api.start_websocket([self.nifty_token], self._on_tick)
            broker_api.subscribed_tokens = []
            broker_api.add_tokens([self.nifty_token])
            
            # Register candle completion callbacks
            candle_aggregator.register_5min_callback(self._on_5min_candle_complete)
            
            self.websocket_started = True
            logger.info("✅ WebSocket started successfully")
            logger.info("✅ Waiting for Nifty ticks...")
            logger.info("=" * 80)
            
            # If started after 9:45, fetch historical data from 9:15 to now
            current_time = get_current_time()
            if current_time.time() >= dt_time(9, 45):
                self._fetch_historical_data_on_start(current_time)
            
        except Exception as e:
            logger.error(f"❌ Error subscribing to Nifty: {e}", exc_info=True)
            if settings.TRADING_PHASE == 1:
                logger.info("📝 Phase 1: Continuing with mock data")
                self.websocket_started = True  # Allow mock mode to continue
    
    def _fetch_historical_data_on_start(self, current_time):
        """Fetch historical data from 9:15 to current time when starting late"""
        try:
            logger.info(f"⏰ Script started at {current_time.strftime('%H:%M:%S')} - fetching historical data from 9:15...")
            
            current_date = current_time.date()
            
            # Fetch from 9:15 to current time
            start_time = settings.TIMEZONE.localize(datetime.combine(current_date, dt_time(9, 15)))
            end_time = current_time
            
            logger.info(f"📥 Fetching Nifty historical data from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}...")
            nifty_df = broker_api.get_historical_data(
                token=self.nifty_token,
                from_datetime=start_time,
                to_datetime=end_time,
                interval='1minute'
            )
            
            if nifty_df.empty:
                logger.warning("No Nifty historical data available")
                return
            
            logger.info(f"✅ Got {len(nifty_df)} Nifty candles from 9:15 to {end_time.strftime('%H:%M')}")
            
            # Feed historical data to candle aggregator for continuity
            # Use add_historical_candle to preserve OHLC data
            # IMPORTANT: Set trigger_callbacks=False to prevent historical candles from triggering trades
            for idx, row in nifty_df.iterrows():
                candle_aggregator.add_historical_candle(
                    self.nifty_token,
                    {
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close']
                    },
                    idx,  # timestamp from index
                    trigger_callbacks=False  # Don't trigger trades on historical data
                )
            
            # If current time >= 10:00 AM, calculate reference levels and select strikes immediately
            if current_time.time() >= dt_time(10, 0):
                logger.info("⚡ Current time >= 10:00 AM - calculating reference levels and selecting strikes...")
                
                # Mark that we started after 10:00 AM
                self.started_after_10am = True
                
                # Extract 9:45-10:00 window for reference calculation
                ref_start = settings.TIMEZONE.localize(datetime.combine(current_date, dt_time(9, 45)))
                ref_end = settings.TIMEZONE.localize(datetime.combine(current_date, dt_time(10, 0)))
                
                # Filter dataframe for reference window
                ref_df = nifty_df[(nifty_df.index >= ref_start) & (nifty_df.index <= ref_end)]
                
                if not ref_df.empty:
                    logger.info(f"📊 Using {len(ref_df)} candles from 9:45-10:00 for reference levels")
                    
                    # Calculate reference levels
                    reference_calculator.calculate_from_candle(
                        nifty_df=ref_df,
                        call_df=ref_df.copy(),  # Temporary - will recalculate
                        put_df=ref_df.copy()    # Temporary - will recalculate
                    )
                    
                    self.reference_levels_set = True
                    logger.info("✅ Reference levels calculated from historical data")
                    
                    # Immediately select strikes
                    self._select_strikes()
                else:
                    logger.warning("No data available in 9:45-10:00 window for reference calculation")
            
        except Exception as e:
            logger.error(f"Error fetching historical data on start: {e}", exc_info=True)
    
    def _on_tick(self, ticks):
        """Handle incoming WebSocket ticks"""
        if not ticks:
            logger.debug("⚠️ Received empty ticks list")
            return
        
        for tick in ticks:
            try:
                # Validate tick data
                if 'instrument_token' not in tick:
                    logger.warning(f"⚠️ Tick missing 'instrument_token': {tick}")
                    continue
                
                if 'last_price' not in tick:
                    logger.warning(f"⚠️ Tick missing 'last_price' for token {tick.get('instrument_token')}: {tick}")
                    continue
                
                token = tick['instrument_token']
                ltp = tick['last_price']
                timestamp = tick.get('timestamp', datetime.now())
                
           # Increment tick counters
                self.tick_count += 1
                if token == self.nifty_token:
                    self.nifty_tick_count += 1
                
                # Get instrument name
                instrument_name = self._get_instrument_name(token)
                
                # Log first Nifty tick to confirm reception
                if token == self.nifty_token and self.nifty_tick_count == 1:
                    logger.info("=" * 80)
                    logger.info("✅ FIRST NIFTY TICK RECEIVED!")
                    logger.info("=" * 80)
                    logger.info(f"📊 Token: {token}")
                    logger.info(f"💰 LTP: ₹{ltp:.2f}")
                    logger.info(f"⏰ Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(f"📝 Instrument: {instrument_name}")
                    logger.info("=" * 80)
                
                # Periodic logging every 100 Nifty ticks
                if token == self.nifty_token and self.nifty_tick_count % 100 == 0:
                    logger.info(f"📊 Nifty Tick Count: {self.nifty_tick_count} | Latest LTP: ₹{ltp:.2f}")
                
                # Save tick to CSV
                data_storage.save_tick(token, ltp, timestamp, instrument_name)
                
                # Add to candle aggregator
                candle_aggregator.add_tick(token, ltp, timestamp)
                
            except Exception as e:
                logger.error(f"❌ Error processing tick: {e}", exc_info=True)
                logger.error(f"   Tick data: {tick}")
    
    def _on_5min_candle_complete(self, token: int, candle: Dict):
        """Callback when 5-min candle completes"""
        current_time = get_current_time()
        
        # Log detailed OHLC for Nifty 50 candles
        if token == self.nifty_token:
            candle_start = candle['timestamp']
            # Candle window: start time to (start + 4 min 59 sec)
            # Example: 10:15:00 candle covers 10:15:00 to 10:19:59
            candle_end = candle_start + pd.Timedelta(minutes=4, seconds=59)
            
            logger.info("=" * 80)
            logger.info("📊 NIFTY 50 - 5 MINUTE CANDLE COMPLETED")
            logger.info("=" * 80)
            logger.info(f"⏰ Current Time:        {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"🕐 Candle Time Window:  {candle_start.strftime('%H:%M:%S')} - {candle_end.strftime('%H:%M:%S')}")
            logger.info(f"📈 Open:                ₹{candle['open']:.2f}")
            logger.info(f"📈 High:                ₹{candle['high']:.2f}")
            logger.info(f"📉 Low:                 ₹{candle['low']:.2f}")
            logger.info(f"📊 Close:               ₹{candle['close']:.2f}")
            logger.info("=" * 80)
        else:
            # For other tokens (options), keep simple logging
            logger.info(f"📊 5-min candle complete for token {token}: {candle}")
        
        # Check if we need to process this candle for entry/management
        # After strikes are selected, monitor for entry
        if self.strikes_selected and not self.in_position:
            if current_time.time() >= dt_time(10, 15):
                self._check_entry_from_candle(candle)
        
        # If in position, manage it
        if self.in_position:
            self._manage_position_from_candle(candle)
    
    def _trading_loop(self):
        """Main trading loop"""
        while self.running:
            try:
                current_time = get_current_time()
                
                # Check if market is open
                if not is_market_open():
                    logger.info("Market is closed. Waiting...")
                    time.sleep(60)
                    continue
                
                # Step 1: Calculate reference levels (09:45-10:00)
                # Only process if not already handled by late start logic
                if not self.reference_levels_set:
                    if is_between_times('10:00', '10:01'):
                        # Normal flow - use aggregated candles
                        self._calculate_reference_levels_from_candles()
                
                # Step 2: Select strikes at 10:00
                # Only process if not already handled by late start logic
                if self.reference_levels_set and not self.strikes_selected:
                    if current_time.time() >= dt_time(10, 0):
                        self._select_strikes()
                
                # Hard exit at 3:15 PM
                if current_time.time() >= dt_time(15, 15) and self.in_position:
                    current_price = self._get_current_option_price()
                    if current_price:
                        self._exit_trade(current_price, 'HARD_EXIT')
                
                # Check daily loss limit
                if abs(self.daily_pnl) >= settings.DAILY_LOSS_LIMIT:
                    logger.warning(f"Daily loss limit reached: ₹{self.daily_pnl:,.2f}. Stopping trading.")
                    self.running = False
                
                # Sleep for 1 second
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("Received shutdown signal...")
                break
            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                time.sleep(5)
    
    def _calculate_reference_levels_from_candles(self):
        """Calculate reference levels from aggregated candles (09:45-10:00)"""
        logger.info("⏰ Calculating reference levels from 09:45-10:00 candles...")
        
        try:
            current_date = get_current_time().date()
            
            # Create timezone-aware datetime objects
            start_time = settings.TIMEZONE.localize(datetime.combine(current_date, dt_time(9, 45)))
            end_time = settings.TIMEZONE.localize(datetime.combine(current_date, dt_time(10, 0)))
            
            # Get Nifty candles from aggregator
            nifty_df = candle_aggregator.get_candles_for_period(
                self.nifty_token, 
                start_time, 
                end_time, 
                interval='1min'
            )
            
            if nifty_df.empty:
                logger.warning("No Nifty candles available for reference window")
                return
            
            logger.info(f"Got {len(nifty_df)} Nifty candles for reference calculation")
            
            # For now, calculate with just Nifty data (will update after strike selection)
            reference_calculator.calculate_from_candle(
                nifty_df=nifty_df,
                call_df=nifty_df.copy(),  # Temporary - will recalculate
                put_df=nifty_df.copy()    # Temporary - will recalculate
            )
            
            self.reference_levels_set = True
            logger.info("✅ Reference levels calculated (will refine after strike selection)")
            
        except Exception as e:
            logger.error(f"Error calculating reference levels: {e}", exc_info=True)
    
    def _select_strikes(self):
        """Select Call and Put strikes at 10:00 using RN (high) from 9:45-10:00 window"""
        logger.info("🎯 Selecting strikes at 10:00...")
        
        try:
            # Get Nifty spot price from RN (high of 9:45-10:00 window)
            current_date = get_current_time().date()
            ref_start = settings.TIMEZONE.localize(datetime.combine(current_date, dt_time(9, 45)))
            ref_end = settings.TIMEZONE.localize(datetime.combine(current_date, dt_time(10, 0)))
            
            # Try to get from candle aggregator first
            nifty_df = candle_aggregator.get_candles_for_period(
                self.nifty_token,
                ref_start,
                ref_end,
                interval='1min'
            )
            
            if not nifty_df.empty:
                # Use RN (high) from the 9:45-10:00 window - same as reference level calculation
                nifty_spot = nifty_df['high'].max()
                logger.info(f"📊 Using Nifty RN (high) from 9:45-10:00 window: ₹{nifty_spot:.2f}")
            else:
                # Fallback to current LTP if candle data not available
                logger.warning("No candle data available for 9:45-10:00, using current LTP")
                nifty_data = broker_api.get_tick_data(self.nifty_token)
                if not nifty_data:
                    nifty_spot = broker_api.get_ltp(self.nifty_token)
                else:
                    nifty_spot = nifty_data['ltp']
                logger.info(f"📊 Using current Nifty LTP: ₹{nifty_spot:.2f}")
            
            if not nifty_spot:
                logger.error("Could not fetch Nifty spot price")
                return
            
            logger.info(f"🎯 Selecting strikes based on Nifty RN (high): ₹{nifty_spot:.2f}")
            
            # Select strikes
            call_inst, put_inst = strike_selector.select_strikes(nifty_spot)
            
            if not call_inst or not put_inst:
                logger.error("Failed to select strikes")
                return
            
            self.call_token = call_inst['token']
            self.put_token = put_inst['token']
            
            logger.info(f"✅ Strikes selected:")
            logger.info(f"   Call: {call_inst['symbol']} (Token: {call_inst['token']})")
            logger.info(f"   Put: {put_inst['symbol']} (Token: {put_inst['token']})")
            
            # Register instrument names in candle aggregator
            candle_aggregator.register_instrument_name(self.call_token, call_inst.get('tradingsymbol', call_inst['symbol']))
            candle_aggregator.register_instrument_name(self.put_token, put_inst.get('tradingsymbol', put_inst['symbol']))
            
            # Subscribe to option tokens
            self._subscribe_options()
            
            # Recalculate reference levels with option data
            self._recalculate_with_option_data()
            
            self.strikes_selected = True
            
        except Exception as e:
            logger.error(f"Error selecting strikes: {e}", exc_info=True)
    
    def _subscribe_options(self):
        """Subscribe to selected option tokens"""
        try:
            new_tokens = [self.call_token, self.put_token]
            new_tokens = [int(t) for t in new_tokens if t is not None]
            new_tokens = list(set(new_tokens))
            if not new_tokens:
                logger.warning("No option tokens to subscribe")
                return

            if settings.is_using_real_data():
                logger.info(f"🔗 Requesting WS add for option tokens: {new_tokens}")
                ok = broker_api.add_tokens(new_tokens)
                if ok:
                    logger.info(f"✅ Options subscribed (now): {new_tokens}")
                else:
                    logger.info("Queued options; will subscribe on next WS connect")
            else:
                # Phase 1 mock
                broker_api.add_tokens(new_tokens)

        except Exception as e:
            logger.error(f"Error subscribing to options: {e}")
            logger.info("Will rely on REST fallback until WS is healthy")
    
    def _recalculate_with_option_data(self):
        """Recalculate reference levels with actual option candle data"""
        try:
            current_time = get_current_time()
            current_date = current_time.date()
            
            # Create timezone-aware datetime objects for comparison
            start_time = settings.TIMEZONE.localize(datetime.combine(current_date, dt_time(9, 45)))
            ref_end_time = settings.TIMEZONE.localize(datetime.combine(current_date, dt_time(10, 0)))
            
            # Use current time as fetch end (not fixed 10:00) to account for processing delay
            fetch_end_time = current_time
            
            # Get Nifty candles from aggregator (already filtered by get_candles_for_period)
            nifty_df = candle_aggregator.get_candles_for_period(
                self.nifty_token, start_time, ref_end_time, '1min'
            )
            
            # If aggregator doesn't have Nifty data (started after 10 AM), fetch historical
            if nifty_df.empty and settings.is_using_real_data():
                logger.info("📥 Fetching Nifty historical data for reference recalculation...")
                nifty_df = broker_api.get_historical_data(
                    token=self.nifty_token,
                    from_datetime=start_time,
                    to_datetime=ref_end_time,
                    interval='1minute'
                )
            
            # For options: Fetch historical data since we subscribed late
            if settings.is_using_real_data():
                logger.info(f"📥 Fetching historical option data from 09:45 to {fetch_end_time.strftime('%H:%M:%S')}...")
                
                # Fetch Call historical data (from 09:45 to current time)
                call_df = broker_api.get_historical_data(
                    token=self.call_token,
                    from_datetime=start_time,
                    to_datetime=fetch_end_time,
                    interval='1minute'
                )
                
                # Fetch Put historical data (from 09:45 to current time)
                put_df = broker_api.get_historical_data(
                    token=self.put_token,
                    from_datetime=start_time,
                    to_datetime=fetch_end_time,
                    interval='1minute'
                )
                
                if not call_df.empty and not put_df.empty:
                    # Filter to exact 09:45-10:00 window for reference calculation
                    # Make sure index is timezone-aware for comparison
                    if call_df.index.tz is None:
                        call_df.index = call_df.index.tz_localize(settings.TIMEZONE)
                    if put_df.index.tz is None:
                        put_df.index = put_df.index.tz_localize(settings.TIMEZONE)
                    
                    call_ref = call_df[(call_df.index >= start_time) & (call_df.index <= ref_end_time)]
                    put_ref = put_df[(put_df.index >= start_time) & (put_df.index <= ref_end_time)]
                    
                    # Feed historical option data to candle aggregator for continuity
                    # IMPORTANT: Set trigger_callbacks=False to prevent historical candles from triggering trades
                    logger.info(f"📥 Feeding {len(call_df)} Call and {len(put_df)} Put historical candles to aggregator...")
                    for idx, row in call_df.iterrows():
                        candle_aggregator.add_historical_candle(
                            self.call_token,
                            {
                                'open': row['open'],
                                'high': row['high'],
                                'low': row['low'],
                                'close': row['close']
                            },
                            idx,
                            trigger_callbacks=False  # Don't trigger trades on historical data
                        )
                    
                    for idx, row in put_df.iterrows():
                        candle_aggregator.add_historical_candle(
                            self.put_token,
                            {
                                'open': row['open'],
                                'high': row['high'],
                                'low': row['low'],
                                'close': row['close']
                            },
                            idx,
                            trigger_callbacks=False  # Don't trigger trades on historical data
                        )
                    
                    # Calculate reference with 09:45-10:00 data only
                    reference_calculator.calculate_from_candle(nifty_df, call_ref, put_ref)
                    logger.info("✅ Reference levels recalculated with historical option data")
                    logger.info(f"   Nifty: {len(nifty_df)} candles, Call: {len(call_ref)} candles, Put: {len(put_ref)} candles")
                else:
                    logger.warning("Could not fetch complete historical option data")
            else:
                # Phase 1: Use mock data (already filtered by get_candles_for_period)
                call_df = candle_aggregator.get_candles_for_period(
                    self.call_token, start_time, ref_end_time, '1min'
                )
                put_df = candle_aggregator.get_candles_for_period(
                    self.put_token, start_time, ref_end_time, '1min'
                )
                
                if not call_df.empty and not put_df.empty:
                    reference_calculator.calculate_from_candle(nifty_df, call_df, put_df)
                    logger.info("✅ Reference levels recalculated with option data")
                else:
                    logger.warning("Waiting for option candle data to accumulate...")
            
        except Exception as e:
            logger.error(f"Error recalculating reference levels: {e}")
    
    def _check_entry_from_candle(self, candle: Dict):
        """Check for entry signals from completed candle"""
        try:
            levels = reference_calculator.get_levels()
            if not levels:
                return
            
            # Check if this is a Nifty 5-minute candle
            if candle['token'] == self.nifty_token:
                close_price = candle['close']
                
                # SPECIAL CHECK: If script started after 10:00 AM, we need to validate
                # that the last completed 5-min Nifty candle closed between RN and GN
                # before we start checking for entry signals
                if self.started_after_10am and not self.neutral_zone_validated:
                    if levels.GN <= close_price <= levels.RN:
                        self.neutral_zone_validated = True
                        logger.info("=" * 80)
                        logger.info("✅ NEUTRAL ZONE VALIDATION PASSED (Late Start)")
                        logger.info("=" * 80)
                        logger.info(f"📊 Last 5-min Nifty candle closed at ₹{close_price:.2f}")
                        logger.info(f"📊 GN (Support): ₹{levels.GN:.2f}")
                        logger.info(f"📊 RN (Resistance): ₹{levels.RN:.2f}")
                        logger.info(f"✅ Price is in neutral zone - ready to check for entry signals")
                        logger.info("=" * 80)
                    else:
                        logger.warning("=" * 80)
                        logger.warning("⚠️  NEUTRAL ZONE VALIDATION FAILED (Late Start)")
                        logger.warning("=" * 80)
                        logger.warning(f"📊 Last 5-min Nifty candle closed at ₹{close_price:.2f}")
                        logger.warning(f"📊 GN (Support): ₹{levels.GN:.2f}")
                        logger.warning(f"📊 RN (Resistance): ₹{levels.RN:.2f}")
                        logger.warning(f"❌ Price NOT in neutral zone - waiting for next candle")
                        logger.warning("=" * 80)
                        return
                
                # If we started after 10 AM and haven't validated neutral zone yet, skip entry check
                if self.started_after_10am and not self.neutral_zone_validated:
                    return
                
                # IMPORTANT: Check if candle close is between RN and GN
                # Only check for entry if price is in the neutral zone
                if not (levels.GN <= close_price <= levels.RN):
                    logger.debug(f"Nifty close {close_price:.2f} not between GN ({levels.GN:.2f}) and RN ({levels.RN:.2f}) - skipping entry check")
                    return
                
                logger.info(f"✅ Nifty close {close_price:.2f} is between GN ({levels.GN:.2f}) and RN ({levels.RN:.2f}) - checking for entry signal")
                
                # Create Nifty candle series with timestamp
                nifty_series = pd.Series({
                    'timestamp': candle.get('timestamp', datetime.now()),
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close']
                })
                
                # Decide side based on two-candle confirmation on Nifty
                side = breakout_detector.decide_side(nifty_series, levels.RN, levels.GN)
                
                if side != 'NONE':
                    # Entry signal confirmed! Get current option price and enter
                    logger.info(f"✅ Entry signal confirmed on Nifty 5-min chart: {side}")
                    
                    # Get the option instrument and current price
                    call_inst, put_inst = strike_selector.get_instruments()
                    instrument = call_inst if side == 'CALL' else put_inst
                    
                    # Get current option price
                    option_token = self.call_token if side == 'CALL' else self.put_token
                    option_price = broker_api.get_ltp(option_token)
                    
                    if option_price:
                        self._enter_trade(side, option_price, instrument, levels)
                    else:
                        logger.error(f"Could not fetch option price for {side} entry")
        
        except Exception as e:
            logger.error(f"Error checking entry: {e}", exc_info=True)
    
    def _manage_position_from_candle(self, candle: Dict):
        """Manage position from completed candle"""
        try:
            current_side_token = self.call_token if self.current_side == 'CALL' else self.put_token
            
            if candle['token'] != current_side_token:
                return
            
            current_price = candle['close']
            current_low = candle['low']
            
            # Update stop loss
            if not stop_loss_manager.is_breakeven_reached():
                stop_loss_manager.update_progressive_sl(current_price)
            else:
                stop_loss_manager.update_trailing_sl(current_price)
            
            # Check stop loss hit
            if stop_loss_manager.check_stop_loss_hit(current_low):
                sl = stop_loss_manager.get_current_sl()
                self._exit_trade(sl, 'SL_HIT')
                return
            
            # Check RSI exit
            call_inst, put_inst = strike_selector.get_instruments()
            token = self.call_token if self.current_side == 'CALL' else self.put_token
            
            # Get recent candles for RSI
            recent_df = candle_aggregator.get_candles(token, '5min', count=20)
            if len(recent_df) >= 15:
                rsi = get_latest_rsi(recent_df, 'close', 14)
                if rsi:
                    self.rsi_peak = track_rsi_peak(rsi, self.rsi_peak)
                    if check_rsi_exit_condition(rsi, self.rsi_peak, settings.RSI_EXIT_DROP):
                        self._exit_trade(current_price, 'RSI_EXIT')
        
        except Exception as e:
            logger.error(f"Error managing position: {e}", exc_info=True)
    
    def _get_current_option_price(self) -> Optional[float]:
        """Get current option price"""
        token = self.call_token if self.current_side == 'CALL' else self.put_token
        tick_data = broker_api.get_tick_data(token)
        if tick_data:
            return tick_data['ltp']
        return broker_api.get_ltp(token)
    
    def _enter_trade(self, side: str, entry_price: float, instrument: Dict, levels):
        """Enter a trade"""
        try:
            trade_id = generate_trade_id(side, entry_price)
            
            ref_low = levels.GC if side == 'CALL' else levels.GP
            ref_mid = levels.BC if side == 'CALL' else levels.BP
            ref_high = levels.RC if side == 'CALL' else levels.RP
            
            stop_loss_manager.initialize(entry_price, ref_low, ref_mid, ref_high)
            
            if settings.is_live_trading():
                logger.info("🔴 LIVE TRADING: Placing real order...")
                response = order_manager.place_entry_order(
                    symbol=instrument['symbol'],
                    qty=instrument['lot_size'],
                    entry_price=entry_price,
                    trade_id=trade_id,
                    side='BUY'
                )
            else:
                logger.info(f"📝 PHASE {settings.TRADING_PHASE}: Simulating order...")
                response = paper_trading_manager.log_entry(
                    trade_id=trade_id,
                    symbol=instrument['symbol'],
                    side=side,
                    qty=instrument['lot_size'],
                    entry_price=entry_price,
                    stop_loss=ref_low
                )
            
            self.in_position = True
            self.current_trade_id = trade_id
            self.current_side = side
            self.entry_price = entry_price
            self.rsi_peak = None
            
            logger.info(f"✅ ENTERED {side} TRADE: {instrument['symbol']} @ ₹{entry_price:.2f}")
            
        except Exception as e:
            logger.error(f"Error entering trade: {e}", exc_info=True)
    
    def _exit_trade(self, exit_price: float, exit_reason: str):
        """Exit current trade"""
        try:
            call_inst, put_inst = strike_selector.get_instruments()
            instrument = call_inst if self.current_side == 'CALL' else put_inst
            
            if settings.is_live_trading():
                logger.info("🔴 LIVE TRADING: Placing exit order...")
                response = order_manager.place_exit_order(
                    symbol=instrument['symbol'],
                    qty=instrument['lot_size'],
                    exit_price=exit_price,
                    trade_id=self.current_trade_id,
                    exit_reason=exit_reason,
                    side='SELL'
                )
            else:
                logger.info(f"📝 PHASE {settings.TRADING_PHASE}: Simulating exit...")
                response = paper_trading_manager.log_exit(
                    trade_id=self.current_trade_id,
                    exit_price=exit_price,
                    exit_reason=exit_reason
                )
            
            pnl = (exit_price - self.entry_price) * instrument['lot_size']
            self.daily_pnl += pnl
            
            logger.info(f"🚪 EXITED {self.current_side} TRADE @ ₹{exit_price:.2f}")
            logger.info(f"   Reason: {exit_reason}")
            logger.info(f"   P&L: ₹{pnl:,.2f}")
            logger.info(f"   Daily P&L: ₹{self.daily_pnl:,.2f}")
            
            self.in_position = False
            self.current_trade_id = None
            self.current_side = None
            self.entry_price = None
            self.rsi_peak = None
            
            stop_loss_manager.reset()
            breakout_detector.notify_position_closed()  # Re-arm for next entry
            
        except Exception as e:
            logger.error(f"Error exiting trade: {e}", exc_info=True)
    
    def _get_instrument_name(self, token: int) -> str:
        """Get instrument name for a token"""
        if token == self.nifty_token:
            return "NIFTY50"
        elif token == self.call_token:
            call_inst, _ = strike_selector.get_instruments()
            if call_inst:
                return call_inst.get('tradingsymbol', f'CALL_{token}')
        elif token == self.put_token:
            _, put_inst = strike_selector.get_instruments()
            if put_inst:
                return put_inst.get('tradingsymbol', f'PUT_{token}')
        return f'TOKEN_{token}'
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.running = False
    
    def _shutdown(self):
        """Cleanup and shutdown"""
        logger.info("\n🛑 Shutting down trading bot...")
        
        if self.in_position:
            logger.warning("Closing open position before shutdown...")
            current_price = self._get_current_option_price()
            if current_price:
                self._exit_trade(current_price, 'SHUTDOWN')
        
        # Close all data storage files
        data_storage.close_all_files()
        
        broker_api.disconnect()
        
        if not settings.is_live_trading():
            paper_trading_manager.print_summary()
        
        logger.info("✅ Shutdown complete. Goodbye!")

def main():
    """Main entry point"""
    bot = TradingBot()
    bot.start()

if __name__ == '__main__':
    main()