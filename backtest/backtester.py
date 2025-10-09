"""
Backtesting engine for strategy validation
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, time, timedelta
from dataclasses import dataclass, asdict
from config.settings import settings
from strategy.reference_levels import ReferenceLevels
from strategy.indicators import calculate_rsi
from utils.logger import get_logger
from utils.helpers import round_to_nearest

logger = get_logger(__name__)

@dataclass
class BacktestTrade:
    """Backtest trade record"""
    date: str
    side: str
    entry_time: str
    entry_price: float
    exit_time: str
    exit_price: float
    exit_reason: str
    pnl: float
    max_sl: float
    max_price: float

class Backtester:
    """Backtest the trading strategy on historical data"""
    
    def __init__(self):
        self.trades: List[BacktestTrade] = []
        self.daily_pnl: Dict[str, float] = {}
    
    def load_data(self, csv_path: str) -> pd.DataFrame:
        """
        Load historical data from CSV
        
        Expected columns: datetime, nifty_open, nifty_high, nifty_low, nifty_close,
                         call_open, call_high, call_low, call_close,
                         put_open, put_high, put_low, put_close
        
        Args:
            csv_path: Path to historical data CSV
        
        Returns:
            DataFrame with datetime index
        """
        try:
            df = pd.read_csv(csv_path)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            
            logger.info(f"Loaded {len(df)} candles from {csv_path}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading backtest data: {e}")
            raise
    
    def resample_to_5min(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resample 1-min data to 5-min candles"""
        resampled = df.resample('5min').agg({
            'nifty_open': 'first',
            'nifty_high': 'max',
            'nifty_low': 'min',
            'nifty_close': 'last',
            'call_open': 'first',
            'call_high': 'max',
            'call_low': 'min',
            'call_close': 'last',
            'put_open': 'first',
            'put_high': 'max',
            'put_low': 'min',
            'put_close': 'last',
        }).dropna()
        
        return resampled
    
    def calculate_reference_levels(self, df: pd.DataFrame, date: str) -> Optional[ReferenceLevels]:
        """Calculate reference levels from 09:45-10:00 candle"""
        try:
            ref_start = pd.Timestamp(f"{date} 09:45:00")
            ref_end = pd.Timestamp(f"{date} 09:59:59")
            
            ref_data = df.loc[ref_start:ref_end]
            
            if len(ref_data) == 0:
                logger.warning(f"No data in reference window for {date}")
                return None
            
            levels = ReferenceLevels(
                RN=ref_data['nifty_high'].max(),
                GN=ref_data['nifty_low'].min(),
                BN=(ref_data['nifty_high'].max() + ref_data['nifty_low'].min()) / 2,
                RC=ref_data['call_high'].max(),
                GC=ref_data['call_low'].min(),
                BC=(ref_data['call_high'].max() + ref_data['call_low'].min()) / 2,
                RP=ref_data['put_high'].max(),
                GP=ref_data['put_low'].min(),
                BP=(ref_data['put_high'].max() + ref_data['put_low'].min()) / 2
            )
            
            return levels
            
        except Exception as e:
            logger.error(f"Error calculating reference levels: {e}")
            return None
    
    def run_backtest(self, data_path: str, start_date: str = None, end_date: str = None):
        """
        Run backtest on historical data
        
        Args:
            data_path: Path to CSV file with historical data
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        logger.info("🔄 Starting backtest...")
        
        # Load data
        df_1min = self.load_data(data_path)
        
        # Filter date range
        if start_date:
            df_1min = df_1min[df_1min.index >= start_date]
        if end_date:
            df_1min = df_1min[df_1min.index <= end_date]
        
        # Resample to 5-min
        df_5min = self.resample_to_5min(df_1min)
        
        # Get unique dates
        dates = df_5min.index.date
        unique_dates = sorted(set(dates))
        
        logger.info(f"Backtesting {len(unique_dates)} days...")
        
        for date in unique_dates:
            logger.info(f"\n{'='*60}")
            logger.info(f"Backtesting date: {date}")
            logger.info(f"{'='*60}")
            
            # Get data for this date
            day_data = df_5min[df_5min.index.date == date]
            
            if len(day_data) < 10:
                logger.warning(f"Insufficient data for {date}, skipping")
                continue
            
            # Calculate reference levels
            levels = self.calculate_reference_levels(day_data, str(date))
            if not levels:
                continue
            
            # Run strategy for this day
            self._backtest_single_day(day_data, levels, str(date))
        
        # Generate report
        self._generate_report()
    
    def _backtest_single_day(self, df: pd.DataFrame, levels: ReferenceLevels, date: str):
        """Backtest a single day"""
        
        # State variables
        in_trade = False
        side = None
        entry_price = None
        entry_time = None
        stop_loss = None
        breakout_detected = False
        confirmation_pending = False
        breakout_high = None
        is_at_breakeven = False
        last_trailing_level = None
        rsi_peak = None
        max_price = None
        
        # Filter trading hours (10:00 onwards)
        trading_data = df[df.index.time >= time(10, 0)]
        
        for idx, row in trading_data.iterrows():
            current_time = idx.time()
            
            # Hard exit at 3:15 PM
            if current_time >= time(15, 15) and in_trade:
                exit_price = row[f'{side.lower()}_close']
                pnl = (exit_price - entry_price) * settings.LOT_SIZE
                
                trade = BacktestTrade(
                    date=date,
                    side=side,
                    entry_time=str(entry_time.time()),
                    entry_price=entry_price,
                    exit_time=str(current_time),
                    exit_price=exit_price,
                    exit_reason='HARD_EXIT',
                    pnl=pnl,
                    max_sl=stop_loss,
                    max_price=max_price
                )
                self.trades.append(trade)
                logger.info(f"  🕒 HARD EXIT: {side} @ {exit_price:.2f} | P&L: ₹{pnl:,.2f}")
                break
            
            # If not in trade, look for entry
            if not in_trade:
                # Decide side
                nifty_close = row['nifty_close']
                nifty_open = row['nifty_open']
                
                if nifty_close > nifty_open and nifty_close > levels.RN:
                    side = 'CALL'
                    ref_high = levels.RC
                    ref_low = levels.GC
                    ref_mid = levels.BC
                elif nifty_close < nifty_open and nifty_close < levels.GN:
                    side = 'PUT'
                    ref_high = levels.RP
                    ref_low = levels.GP
                    ref_mid = levels.BP
                else:
                    continue
                
                option_close = row[f'{side.lower()}_close']
                option_open = row[f'{side.lower()}_open']
                option_high = row[f'{side.lower()}_high']
                
                # Check breakout
                if not breakout_detected:
                    if option_close > option_open and option_close > ref_high:
                        breakout_detected = True
                        breakout_high = option_high
                        confirmation_pending = True
                        logger.info(f"  🔔 Breakout detected: {side} @ {option_close:.2f}")
                        continue
                
                # Check confirmation
                if confirmation_pending:
                    if (option_close > option_open and 
                        option_close > breakout_high and 
                        option_close > ref_high):
                        
                        # ENTRY!
                        in_trade = True
                        entry_price = option_close
                        entry_time = idx
                        stop_loss = ref_low
                        last_trailing_level = entry_price
                        max_price = entry_price
                        rsi_peak = None
                        
                        logger.info(f"  ✅ ENTRY: {side} @ {entry_price:.2f} | SL: {stop_loss:.2f}")
                    else:
                        # Reset if confirmation failed
                        breakout_detected = False
                        confirmation_pending = False
                        breakout_high = None
            
            # If in trade, manage position
            else:
                option_close = row[f'{side.lower()}_close']
                option_low = row[f'{side.lower()}_low']
                
                # Track max price
                if option_close > max_price:
                    max_price = option_close
                
                # Check stop loss hit
                if option_low <= stop_loss:
                    exit_price = stop_loss
                    pnl = (exit_price - entry_price) * settings.LOT_SIZE
                    
                    trade = BacktestTrade(
                        date=date,
                        side=side,
                        entry_time=str(entry_time.time()),
                        entry_price=entry_price,
                        exit_time=str(current_time),
                        exit_price=exit_price,
                        exit_reason='SL_HIT',
                        pnl=pnl,
                        max_sl=stop_loss,
                        max_price=max_price
                    )
                    self.trades.append(trade)
                    logger.info(f"  🛑 SL HIT: {side} @ {exit_price:.2f} | P&L: ₹{pnl:,.2f}")
                    
                    # Reset for next trade
                    in_trade = False
                    side = None
                    breakout_detected = False
                    confirmation_pending = False
                    continue
                
                # Progressive SL (before breakeven)
                if not is_at_breakeven:
                    EC = entry_price
                    GC = ref_low
                    BC = ref_mid
                    RC = ref_high
                    
                    if option_close >= EC + (BC - GC) and stop_loss < BC:
                        stop_loss = BC
                    elif option_close >= EC + (RC - GC) and stop_loss < RC:
                        stop_loss = RC
                    elif option_close >= EC + (EC - GC) and stop_loss < EC:
                        stop_loss = EC
                        is_at_breakeven = True
                
                # Trailing SL (after breakeven)
                if is_at_breakeven:
                    price_above_entry = option_close - entry_price
                    num_increments = int(price_above_entry / settings.TRAILING_INCREMENT)
                    
                    if num_increments > 0:
                        new_trailing = entry_price + (num_increments * settings.TRAILING_INCREMENT)
                        if new_trailing > last_trailing_level:
                            stop_loss = new_trailing
                            last_trailing_level = new_trailing
                
                # RSI exit check (calculate RSI on last 14 candles)
                # Get historical data for RSI
                hist_data = df[df.index <= idx].tail(20)
                if len(hist_data) >= 15:
                    rsi_series = calculate_rsi(hist_data[f'{side.lower()}_close'], period=14)
                    current_rsi = rsi_series.iloc[-1]
                    
                    if not np.isnan(current_rsi):
                        if rsi_peak is None or current_rsi > rsi_peak:
                            rsi_peak = current_rsi
                        
                        if rsi_peak and (rsi_peak - current_rsi) >= settings.RSI_EXIT_DROP:
                            exit_price = option_close
                            pnl = (exit_price - entry_price) * settings.LOT_SIZE
                            
                            trade = BacktestTrade(
                                date=date,
                                side=side,
                                entry_time=str(entry_time.time()),
                                entry_price=entry_price,
                                exit_time=str(current_time),
                                exit_price=exit_price,
                                exit_reason='RSI_EXIT',
                                pnl=pnl,
                                max_sl=stop_loss,
                                max_price=max_price
                            )
                            self.trades.append(trade)
                            logger.info(f"  📉 RSI EXIT: {side} @ {exit_price:.2f} | P&L: ₹{pnl:,.2f}")
                            
                            # Reset
                            in_trade = False
                            side = None
                            breakout_detected = False
                            confirmation_pending = False
                            continue
    
    def _generate_report(self):
        """Generate backtest report"""
        if not self.trades:
            logger.warning("No trades executed in backtest")
            return
        
        df_trades = pd.DataFrame([asdict(t) for t in self.trades])
        
        # Calculate metrics
        total_trades = len(df_trades)
        winning_trades = len(df_trades[df_trades['pnl'] > 0])
        losing_trades = len(df_trades[df_trades['pnl'] <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = df_trades['pnl'].sum()
        avg_win = df_trades[df_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df_trades[df_trades['pnl'] <= 0]['pnl'].mean() if losing_trades > 0 else 0
        max_win = df_trades['pnl'].max()
        max_loss = df_trades['pnl'].min()
        
        # Print report
        print("\n" + "="*80)
        print("📊 BACKTEST RESULTS")
        print("="*80)
        print(f"Total Trades: {total_trades}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Losing Trades: {losing_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"\nTotal P&L: ₹{total_pnl:,.2f}")
        print(f"Average Win: ₹{avg_win:,.2f}")
        print(f"Average Loss: ₹{avg_loss:,.2f}")
        print(f"Max Win: ₹{max_win:,.2f}")
        print(f"Max Loss: ₹{max_loss:,.2f}")
        print(f"Profit Factor: {abs(avg_win / avg_loss):.2f}" if avg_loss != 0 else "N/A")
        print("="*80)
        
        # Save to CSV
        output_file = f'./backtest_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df_trades.to_csv(output_file, index=False)
        print(f"\n📁 Detailed results saved to: {output_file}\n")

# Global instance
backtester = Backtester()