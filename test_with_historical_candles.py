"""
Test bot logic with historical 1-minute candles
Feed candles directly (not ticks) to test the strategy
"""
import pandas as pd
import time
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from config.settings import settings
from utils.logger import setup_logger
from utils.candle_aggregator import candle_aggregator
from data.broker_api import broker_api
from data.instruments import instrument_manager
from strategy.reference_levels import reference_calculator
from strategy.strike_selector import strike_selector
from strategy.breakout_logic import breakout_detector
from strategy.stop_loss import stop_loss_manager
from strategy.indicators import get_latest_rsi, track_rsi_peak, check_rsi_exit_condition
from execution.paper_trading import paper_trading_manager
from utils.helpers import generate_trade_id

logger = setup_logger('HistoricalTest', './logs/historical_test.log', 'INFO')

class HistoricalTester:
    """Test bot with historical 1-minute candles"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.data = None
        
        # Bot state
        self.reference_levels_set = False
        self.strikes_selected = False
        self.in_position = False
        self.current_trade_id = None
        self.current_side = None
        self.entry_price = None
        self.rsi_peak = None
        self.daily_pnl = 0.0
        
        # Tokens
        self.nifty_token = 256265
        self.call_token = None
        self.put_token = None
        
    def load_data(self):
        """Load historical CSV"""
        logger.info(f"Loading data from {self.csv_path}...")
        self.data = pd.read_csv(self.csv_path)
        self.data['datetime'] = pd.to_datetime(self.data['datetime'])
        self.data = self.data.sort_values('datetime')
        logger.info(f"Loaded {len(self.data)} candles")
        logger.info(f"Date range: {self.data['datetime'].min()} to {self.data['datetime'].max()}")
    
    def run_test(self):
        """Run test with historical candles"""
        if self.data is None:
            self.load_data()
        
        logger.info("\n" + "="*80)
        logger.info("🧪 TESTING WITH HISTORICAL 1-MINUTE CANDLES")
        logger.info("="*80)
        
        # Process each 1-min candle
        for idx, row in self.data.iterrows():
            candle_time = row['datetime']
            
            # Add Nifty candle to aggregator
            nifty_candle = {
                'open': row['nifty_open'],
                'high': row['nifty_high'],
                'low': row['nifty_low'],
                'close': row['nifty_close'],
                'timestamp': candle_time,
                'token': self.nifty_token
            }
            
            # Store in aggregator (as completed 1-min candle)
            candle_aggregator.completed_1min_candles[self.nifty_token].append(nifty_candle)
            
            # Update broker latest ticks
            broker_api.latest_ticks[self.nifty_token] = {
                'ltp': row['nifty_close'],
                'open': row['nifty_open'],
                'high': row['nifty_high'],
                'low': row['nifty_low'],
                'close': row['nifty_close'],
                'timestamp': candle_time
            }
            
            # Check if we should calculate reference levels
            if not self.reference_levels_set:
                if candle_time.time() >= pd.Timestamp('10:15').time():
                    self._calculate_reference_levels()
            
            # Select strikes at 10:15
            if self.reference_levels_set and not self.strikes_selected:
                if candle_time.time() >= pd.Timestamp('10:15').time():
                    self._select_strikes(row)
            
            # If strikes selected, add option candles
            if self.strikes_selected:
                # Add Call candle
                call_candle = {
                    'open': row['call_open'],
                    'high': row['call_high'],
                    'low': row['call_low'],
                    'close': row['call_close'],
                    'timestamp': candle_time,
                    'token': self.call_token
                }
                candle_aggregator.completed_1min_candles[self.call_token].append(call_candle)
                
                broker_api.latest_ticks[self.call_token] = {
                    'ltp': row['call_close'],
                    'open': row['call_open'],
                    'high': row['call_high'],
                    'low': row['call_low'],
                    'close': row['call_close'],
                    'timestamp': candle_time
                }
                
                # Add Put candle
                put_candle = {
                    'open': row['put_open'],
                    'high': row['put_high'],
                    'low': row['put_low'],
                    'close': row['put_close'],
                    'timestamp': candle_time,
                    'token': self.put_token
                }
                candle_aggregator.completed_1min_candles[self.put_token].append(put_candle)
                
                broker_api.latest_ticks[self.put_token] = {
                    'ltp': row['put_close'],
                    'open': row['put_open'],
                    'high': row['put_high'],
                    'low': row['put_low'],
                    'close': row['put_close'],
                    'timestamp': candle_time
                }
                
                # Build 5-min candles and check signals every 5 minutes
                if candle_time.minute % 5 == 0:
                    self._process_5min_candle(candle_time)
            
            # Hard exit at 3:15
            if candle_time.time() >= pd.Timestamp('15:15').time() and self.in_position:
                self._exit_trade(row['call_close'] if self.current_side == 'CALL' else row['put_close'], 'HARD_EXIT')
            
            # Progress (every 5 minutes = 5 candles)
            if idx % 5 == 0:
                progress_pct = (idx / len(self.data)) * 100
                logger.info(f"Progress: {progress_pct:.1f}% - {candle_time}")
        
        logger.info("\n✅ Test complete!")
        paper_trading_manager.print_summary()
    
    def _calculate_reference_levels(self):
        """Calculate reference from 10:00-10:15"""
        logger.info("⏰ Calculating reference levels...")
        
        # Get first candle date and timezone
        first_date = self.data['datetime'].iloc[0]
        tz = first_date.tz  # Preserve timezone from data
        
        # Create timestamps with same timezone as data
        start_time = pd.Timestamp(f"{first_date.date()} 10:00:00", tz=tz)
        end_time = pd.Timestamp(f"{first_date.date()} 10:15:00", tz=tz)
        
        # Get Nifty candles
        nifty_df = candle_aggregator.get_candles_for_period(
            self.nifty_token, start_time, end_time, '1min'
        )
        
        if not nifty_df.empty:
            # Calculate with Nifty only (will recalculate with options later)
            reference_calculator.calculate_from_candle(nifty_df, nifty_df.copy(), nifty_df.copy())
            self.reference_levels_set = True
            logger.info("✅ Reference levels calculated")
    
    def _select_strikes(self, row):
        """Select strikes"""
        logger.info("🎯 Selecting strikes...")
        
        nifty_spot = row['nifty_close']
        
        logger.info(f"✅ Selected Call token: {self.call_token}, Put token: {self.put_token}")
        
        # Recalculate reference with option data
        self._recalculate_reference()
        
        self.strikes_selected = True
    
    def _recalculate_reference(self):
        """Recalculate with option data"""
        # Get first candle date and timezone
        first_date = self.data['datetime'].iloc[0]
        tz = first_date.tz
        
        start_time = pd.Timestamp(f"{first_date.date()} 10:00:00", tz=tz)
        end_time = pd.Timestamp(f"{first_date.date()} 10:15:00", tz=tz)
        
        nifty_df = candle_aggregator.get_candles_for_period(self.nifty_token, start_time, end_time, '1min')
        call_df = candle_aggregator.get_candles_for_period(self.call_token, start_time, end_time, '1min')
        put_df = candle_aggregator.get_candles_for_period(self.put_token, start_time, end_time, '1min')
        
        if not call_df.empty and not put_df.empty:
            reference_calculator.calculate_from_candle(nifty_df, call_df, put_df)
            logger.info("✅ Reference recalculated with option data")
    
    def _process_5min_candle(self, candle_time):
        """Process every 5 minutes"""
        # Build 5-min candle from last 5 1-min candles
        # Use timezone-aware timestamp
        start_time = candle_time - pd.Timedelta(minutes=5)
        
        levels = reference_calculator.get_levels()
        if not levels:
            return
        
        # Get 5-min candle for Nifty
        nifty_candles = candle_aggregator.get_candles_for_period(
            self.nifty_token, start_time, candle_time, '1min'
        )
        
        if len(nifty_candles) > 0:
            nifty_5min = {
                'open': nifty_candles.iloc[0]['open'],
                'high': nifty_candles['high'].max(),
                'low': nifty_candles['low'].min(),
                'close': nifty_candles.iloc[-1]['close']
            }
            
            # Decide side
            if not self.in_position:
                side = breakout_detector.decide_side(pd.Series(nifty_5min), levels.RN, levels.GN)
                
                if side != 'NONE':
                    # Check option candle
                    option_token = self.call_token if side == 'CALL' else self.put_token
                    option_candles = candle_aggregator.get_candles_for_period(
                        option_token, start_time, candle_time, '1min'
                    )
                    
                    if len(option_candles) > 0:
                        option_5min = {
                            'open': option_candles.iloc[0]['open'],
                            'high': option_candles['high'].max(),
                            'low': option_candles['low'].min(),
                            'close': option_candles.iloc[-1]['close']
                        }
                        
                        ref_high = levels.RC if side == 'CALL' else levels.RP
                        
                        # Check breakout/confirmation
                        if breakout_detector.check_breakout(pd.Series(option_5min), ref_high, side):
                            logger.info(f"🔔 Breakout on {side}")
                        
                        if breakout_detector.check_confirmation(pd.Series(option_5min), ref_high, side):
                            self._enter_trade(side, option_5min['close'], levels)
            
            # Manage position
            if self.in_position:
                self._manage_position(candle_time)
    
    def _enter_trade(self, side, entry_price, levels):
        """Enter trade"""
        trade_id = generate_trade_id(side, entry_price)
        
        ref_low = levels.GC if side == 'CALL' else levels.GP
        ref_mid = levels.BC if side == 'CALL' else levels.BP
        ref_high = levels.RC if side == 'CALL' else levels.RP
        
        stop_loss_manager.initialize(entry_price, ref_low, ref_mid, ref_high)
        
        paper_trading_manager.log_entry(
            trade_id=trade_id,
            symbol=f"{side}_OPTION",
            side=side,
            qty=75,
            entry_price=entry_price,
            stop_loss=ref_low
        )
        
        self.in_position = True
        self.current_trade_id = trade_id
        self.current_side = side
        self.entry_price = entry_price
        
        logger.info(f"✅ ENTERED {side} @ {entry_price}")
    
    def _manage_position(self, candle_time):
        """Manage open position"""
        token = self.call_token if self.current_side == 'CALL' else self.put_token
        tick = broker_api.latest_ticks.get(token)
        
        if not tick:
            return
        
        current_price = tick['ltp']
        current_low = tick['low']
        
        # Update SL
        if not stop_loss_manager.is_breakeven_reached():
            stop_loss_manager.update_progressive_sl(current_price)
        else:
            stop_loss_manager.update_trailing_sl(current_price)
        
        # Check SL hit
        if stop_loss_manager.check_stop_loss_hit(current_low):
            sl = stop_loss_manager.get_current_sl()
            self._exit_trade(sl, 'SL_HIT')
    
    def _exit_trade(self, exit_price, reason):
        """Exit trade"""
        paper_trading_manager.log_exit(
            trade_id=self.current_trade_id,
            exit_price=exit_price,
            exit_reason=reason
        )
        
        pnl = (exit_price - self.entry_price) * 75
        self.daily_pnl += pnl
        
        logger.info(f"🚪 EXITED @ {exit_price} | Reason: {reason} | P&L: ₹{pnl:,.2f}")
        
        self.in_position = False
        self.current_trade_id = None
        self.current_side = None
        stop_loss_manager.reset()
        breakout_detector.reset_all()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Test with historical 1-min candles')
    parser.add_argument('--data', type=str, required=True, help='Path to historical CSV')
    parser.add_argument('--nifty-token', type=int, default=256265, help='Nifty token')
    parser.add_argument('--call-token', type=int, required=True, help='Call option token')
    parser.add_argument('--put-token', type=int, required=True, help='Put option token')
    
    args = parser.parse_args()
    
    # Set Phase 1
    os.environ['TRADING_PHASE'] = '1'
    
    tester = HistoricalTester(args.data)
    tester.nifty_token = args.nifty_token
    tester.call_token = args.call_token
    tester.put_token = args.put_token
    
    logger.info(f"Nifty Token: {tester.nifty_token}")
    logger.info(f"Call Token: {tester.call_token}")
    logger.info(f"Put Token: {tester.put_token}")
    logger.info("="*80)
    
    tester.run_test()

if __name__ == '__main__':
    main()