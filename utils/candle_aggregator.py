"""
Aggregate real-time ticks into candles
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
from utils.logger import get_logger

logger = get_logger(__name__)

class CandleAggregator:
    """Aggregate ticks into 1-minute and 5-minute candles"""
    
    def __init__(self):
        # Store current candles being built
        self.current_1min_candles = {}  # {token: {open, high, low, close, timestamp}}
        self.current_5min_candles = {}
        
        # Store completed candles
        self.completed_1min_candles = defaultdict(list)  # {token: [candles]}
        self.completed_5min_candles = defaultdict(list)
        
        # Callbacks for when candles complete
        self.on_1min_candle_callbacks = []
        self.on_5min_candle_callbacks = []
    
    def add_tick(self, token: int, ltp: float, timestamp: datetime):
        """
        Add a tick and aggregate into candles
        
        Args:
            token: Instrument token
            ltp: Last traded price
            timestamp: Tick timestamp
        """
        # Update 1-minute candle
        self._update_candle(token, ltp, timestamp, interval_minutes=1)
        
        # Update 5-minute candle
        self._update_candle(token, ltp, timestamp, interval_minutes=5)
    
    def _update_candle(self, token: int, ltp: float, timestamp: datetime, interval_minutes: int):
        """Update candle for given interval"""
        
        # Determine which candle dict to use
        if interval_minutes == 1:
            current_candles = self.current_1min_candles
            completed_candles = self.completed_1min_candles
            callbacks = self.on_1min_candle_callbacks
        elif interval_minutes == 5:
            current_candles = self.current_5min_candles
            completed_candles = self.completed_5min_candles
            callbacks = self.on_5min_candle_callbacks
        else:
            return
        
        # Round timestamp to candle interval
        candle_time = timestamp.replace(
            minute=(timestamp.minute // interval_minutes) * interval_minutes,
            second=0,
            microsecond=0
        )
        
        # Check if we need to start a new candle
        if token not in current_candles:
            # First tick for this token
            current_candles[token] = {
                'open': ltp,
                'high': ltp,
                'low': ltp,
                'close': ltp,
                'timestamp': candle_time,
                'token': token
            }
        else:
            current_candle = current_candles[token]
            
            # Check if new candle period started
            if candle_time > current_candle['timestamp']:
                # Save completed candle
                completed_candles[token].append(current_candle.copy())
                
                # Call callbacks
                for callback in callbacks:
                    callback(token, current_candle.copy())
                
                # Start new candle
                current_candles[token] = {
                    'open': ltp,
                    'high': ltp,
                    'low': ltp,
                    'close': ltp,
                    'timestamp': candle_time,
                    'token': token
                }
            else:
                # Update current candle
                current_candle['high'] = max(current_candle['high'], ltp)
                current_candle['low'] = min(current_candle['low'], ltp)
                current_candle['close'] = ltp
    
    def get_candles(self, token: int, interval: str = '5min', count: int = None, start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
        """
        Get candles for a token
        
        Args:
            token: Instrument token
            interval: '1min' or '5min'
            count: Number of recent candles (None = all)
            start_time: Filter candles from this time (optional)
            end_time: Filter candles until this time (optional)
        
        Returns:
            DataFrame with OHLC data
        """
        if interval == '1min':
            candles = self.completed_1min_candles.get(token, [])
        elif interval == '5min':
            candles = self.completed_5min_candles.get(token, [])
        else:
            return pd.DataFrame()
        
        if not candles:
            return pd.DataFrame()
        
        # Apply time filters during candle selection (efficient)
        if start_time or end_time:
            filtered_candles = []
            for candle in candles:
                candle_time = candle['timestamp']
                
                # Check start time
                if start_time and candle_time < start_time:
                    continue
                
                # Check end time
                if end_time and candle_time > end_time:
                    continue
                
                filtered_candles.append(candle)
            
            candles = filtered_candles
        
        if not candles:
            return pd.DataFrame()
        
        df = pd.DataFrame(candles)
        df.set_index('timestamp', inplace=True)
        df = df[['open', 'high', 'low', 'close']]
        
        if count:
            df = df.tail(count)
        
        return df
    
    def get_current_candle(self, token: int, interval: str = '5min') -> Optional[Dict]:
        """Get current (incomplete) candle"""
        if interval == '1min':
            return self.current_1min_candles.get(token)
        elif interval == '5min':
            return self.current_5min_candles.get(token)
        return None
    
    def register_1min_callback(self, callback):
        """Register callback for 1-min candle completion"""
        self.on_1min_candle_callbacks.append(callback)
    
    def register_5min_callback(self, callback):
        """Register callback for 5-min candle completion"""
        self.on_5min_candle_callbacks.append(callback)
    
    def get_candles_for_period(self, token: int, start_time: datetime, end_time: datetime, interval: str = '1min') -> pd.DataFrame:
        """
        Get candles for specific time period (uses efficient filtering)
        
        Args:
            token: Instrument token
            start_time: Period start
            end_time: Period end
            interval: '1min' or '5min'
        
        Returns:
            DataFrame with candles in the time range
        """
        # Directly pass filters to get_candles (no double filtering)
        return self.get_candles(token, interval=interval, start_time=start_time, end_time=end_time)

# Global instance
candle_aggregator = CandleAggregator()