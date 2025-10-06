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
            logger.info("🔗 Subscribing to Nifty spot for real-time data...")
            
            # Start WebSocket with Nifty token
            broker_api.start_websocket([self.nifty_token], self._on_tick)
            
            # Register candle completion callbacks
            candle_aggregator.register_5min_callback(self._on_5min_candle_complete)
            
            self.websocket_started = True
            logger.info("✅ WebSocket started - receiving Nifty ticks")
            
        except Exception as e:
            logger.error(f"Error subscribing to Nifty: {e}")
            if settings.TRADING_PHASE == 1:
                logger.info("📝 Phase 1: Continuing with mock data")
                self.websocket_started = True  # Allow mock mode to continue
    
    def _on_tick(self, ticks):
        """Handle incoming WebSocket ticks"""
        for tick in ticks:
            token = tick['instrument_token']
            ltp = tick['last_price']
            timestamp = tick.get('timestamp', datetime.now())
            
            # Add to candle aggregator
            candle_aggregator.add_tick(token, ltp, timestamp)
    
    def _on_5min_candle_complete(self, token: int, candle: Dict):
        """Callback when 5-min candle completes"""
        logger.info(f"📊 5-min candle complete for token {token}: {candle}")
        
        # Check if we need to process this candle for entry/management
        current_time = get_current_time()
        
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
                
                # Step 1: Calculate reference levels (10:00-10:15)
                if not self.reference_levels_set and is_between_times('10:15', '10:16'):
                    self._calculate_reference_levels_from_candles()
                
                # Step 2: Select strikes at 10:15
                if self.reference_levels_set and not self.strikes_selected:
                    if current_time.time() >= dt_time(10, 15):
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
        """Calculate reference levels from aggregated candles (10:00-10:15)"""
        logger.info("⏰ Calculating reference levels from 10:00-10:15 candles...")
        
        try:
            current_date = get_current_time().date()
            start_time = datetime.combine(current_date, dt_time(10, 0))
            end_time = datetime.combine(current_date, dt_time(10, 15))
            
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
        """Select Call and Put strikes at 10:15"""
        logger.info("🎯 Selecting strikes at 10:15...")
        
        try:
            # Get Nifty spot price from latest tick
            nifty_data = broker_api.get_tick_data(self.nifty_token)
            if not nifty_data:
                nifty_spot = broker_api.get_ltp(self.nifty_token)
            else:
                nifty_spot = nifty_data['ltp']
            
            if not nifty_spot:
                logger.error("Could not fetch Nifty spot price")
                return
            
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
            # Add Call and Put to existing WebSocket subscription
            new_tokens = [self.call_token, self.put_token]
            
            if settings.is_using_real_data():
                # KiteConnect: Add tokens to existing WebSocket
                if broker_api.kws:
                    broker_api.kws.subscribe(new_tokens)
                    broker_api.kws.set_mode(broker_api.kws.MODE_FULL, new_tokens)
                    
                    # Update tracked tokens
                    broker_api.subscribed_tokens.extend(new_tokens)
                    
                    logger.info(f"✅ Added {len(new_tokens)} option instruments to WebSocket")
                else:
                    logger.warning("WebSocket not running, cannot add options")
            else:
                # Phase 1: Mock mode
                broker_api.subscribed_tokens.extend(new_tokens)
                logger.info(f"📝 Mock: Added {len(new_tokens)} instruments")
            
        except Exception as e:
            logger.error(f"Error subscribing to options: {e}")
    
    def _recalculate_with_option_data(self):
        """Recalculate reference levels with actual option candle data"""
        try:
            current_time = get_current_time()
            current_date = current_time.date()
            start_time = datetime.combine(current_date, dt_time(10, 0))
            ref_end_time = datetime.combine(current_date, dt_time(10, 15))
            
            # Use current time as fetch end (not fixed 10:15) to account for processing delay
            fetch_end_time = current_time
            
            # Get Nifty candles from aggregator (already filtered by get_candles_for_period)
            nifty_df = candle_aggregator.get_candles_for_period(
                self.nifty_token, start_time, ref_end_time, '1min'
            )
            
            # For options: Fetch historical data since we subscribed late
            if settings.is_using_real_data():
                logger.info(f"📥 Fetching historical option data from 10:00 to {fetch_end_time.strftime('%H:%M:%S')}...")
                
                # Fetch Call historical data (from 10:00 to current time)
                call_df = broker_api.get_historical_data(
                    token=self.call_token,
                    from_datetime=start_time,
                    to_datetime=fetch_end_time,
                    interval='1minute'
                )
                
                # Fetch Put historical data (from 10:00 to current time)
                put_df = broker_api.get_historical_data(
                    token=self.put_token,
                    from_datetime=start_time,
                    to_datetime=fetch_end_time,
                    interval='1minute'
                )
                
                if not call_df.empty and not put_df.empty:
                    # Filter to exact 10:00-10:15 window for reference calculation
                    call_ref = call_df[(call_df.index >= start_time) & (call_df.index <= ref_end_time)]
                    put_ref = put_df[(put_df.index >= start_time) & (put_df.index <= ref_end_time)]
                    
                    # Calculate reference with 10:00-10:15 data only
                    reference_calculator.calculate_from_candle(nifty_df, call_ref, put_ref)
                    logger.info("✅ Reference levels recalculated with historical option data")
                    logger.info(f"   Call: {len(call_ref)} candles, Put: {len(put_ref)} candles")
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
            
            # Check if this is a Nifty candle
            if candle['token'] == self.nifty_token:
                # Decide side
                nifty_series = pd.Series({
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close']
                })
                
                side = breakout_detector.decide_side(nifty_series, levels.RN, levels.GN)
                if side == 'NONE':
                    return
            
            # Check if this is the option candle we're watching
            current_side = breakout_detector.get_current_side()
            if current_side == 'NONE':
                return
            
            option_token = self.call_token if current_side == 'CALL' else self.put_token
            
            if candle['token'] == option_token:
                option_series = pd.Series({
                    'open': candle['open'],
                    'high': candle['high'],
                    'low': candle['low'],
                    'close': candle['close']
                })
                
                ref_high = levels.RC if current_side == 'CALL' else levels.RP
                
                # Check for breakout
                if breakout_detector.check_breakout(option_series, ref_high, current_side):
                    logger.info(f"🔔 Breakout detected on {current_side} side")
                    return
                
                # Check for confirmation
                if breakout_detector.check_confirmation(option_series, ref_high, current_side):
                    call_inst, put_inst = strike_selector.get_instruments()
                    instrument = call_inst if current_side == 'CALL' else put_inst
                    self._enter_trade(current_side, candle['close'], instrument, levels)
        
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
            breakout_detector.reset_all()
            
        except Exception as e:
            logger.error(f"Error exiting trade: {e}", exc_info=True)
    
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