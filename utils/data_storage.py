"""
Data storage utility for saving ticks and candles to CSV files
"""
import os
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from utils.logger import setup_logger

logger = setup_logger('DataStorage', level='INFO')

class DataStorage:
    """Handle storage of ticks and candles to CSV files"""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize data storage
        
        Args:
            base_dir: Base directory for storing data files (default: ./market_data)
        """
        if base_dir is None:
            # Use market_data directory in project root
            self.base_dir = Path(__file__).parent.parent / 'market_data'
        else:
            self.base_dir = Path(base_dir)
        
        # Create subdirectories
        self.ticks_dir = self.base_dir / 'ticks'
        self.candles_1min_dir = self.base_dir / 'candles_1min'
        self.candles_5min_dir = self.base_dir / 'candles_5min'
        
        # Create directories if they don't exist
        self._create_directories()
        
        # Track current date for file rotation
        self.current_date = datetime.now().date()
        
        # File handles and writers
        self.tick_files = {}  # {token: (file_handle, csv_writer)}
        self.candle_1min_files = {}  # {token: (file_handle, csv_writer)}
        self.candle_5min_files = {}  # {token: (file_handle, csv_writer)}
        
        logger.info(f"📁 Data storage initialized at: {self.base_dir}")
    
    def _create_directories(self):
        """Create necessary directories"""
        for directory in [self.ticks_dir, self.candles_1min_dir, self.candles_5min_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_date_string(self) -> str:
        """Get current date string for file naming"""
        return datetime.now().strftime('%Y%m%d')
    
    def _check_date_rotation(self):
        """Check if date has changed and close old files"""
        current_date = datetime.now().date()
        if current_date != self.current_date:
            logger.info(f"📅 Date changed from {self.current_date} to {current_date} - rotating files")
            self.close_all_files()
            self.current_date = current_date
    
    def save_tick(self, token: int, ltp: float, timestamp: datetime, instrument_name: str = None):
        """
        Save a tick to CSV file
        
        Args:
            token: Instrument token
            ltp: Last traded price
            timestamp: Tick timestamp
            instrument_name: Optional instrument name for better file naming
        """
        self._check_date_rotation()
        
        # Get or create file handle
        if token not in self.tick_files:
            self._create_tick_file(token, instrument_name)
        
        file_handle, writer = self.tick_files[token]
        
        # Write tick data
        writer.writerow({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'token': token,
            'ltp': ltp
        })
        
        # Flush to ensure data is written
        file_handle.flush()
    
    def save_1min_candle(self, token: int, candle: Dict, instrument_name: str = None):
        """
        Save a 1-minute candle to CSV file
        
        Args:
            token: Instrument token
            candle: Candle dictionary with OHLC data
            instrument_name: Optional instrument name for better file naming
        """
        self._check_date_rotation()
        
        # Get or create file handle
        if token not in self.candle_1min_files:
            self._create_candle_file(token, '1min', instrument_name)
        
        file_handle, writer = self.candle_1min_files[token]
        
        # Write candle data
        writer.writerow({
            'timestamp': candle['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'token': token,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close']
        })
        
        # Flush to ensure data is written
        file_handle.flush()
    
    def save_5min_candle(self, token: int, candle: Dict, instrument_name: str = None):
        """
        Save a 5-minute candle to CSV file
        
        Args:
            token: Instrument token
            candle: Candle dictionary with OHLC data
            instrument_name: Optional instrument name for better file naming
        """
        self._check_date_rotation()
        
        # Get or create file handle
        if token not in self.candle_5min_files:
            self._create_candle_file(token, '5min', instrument_name)
        
        file_handle, writer = self.candle_5min_files[token]
        
        # Write candle data
        writer.writerow({
            'timestamp': candle['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            'token': token,
            'open': candle['open'],
            'high': candle['high'],
            'low': candle['low'],
            'close': candle['close']
        })
        
        # Flush to ensure data is written
        file_handle.flush()
    
    def _create_tick_file(self, token: int, instrument_name: str = None):
        """Create a new tick CSV file"""
        date_str = self._get_date_string()
        
        if instrument_name:
            filename = f"ticks_{instrument_name}_{token}_{date_str}.csv"
        else:
            filename = f"ticks_{token}_{date_str}.csv"
        
        filepath = self.ticks_dir / filename
        
        # Open file in append mode
        file_handle = open(filepath, 'a', newline='')
        
        # Create CSV writer
        fieldnames = ['timestamp', 'token', 'ltp']
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        
        # Write header if file is new
        if filepath.stat().st_size == 0:
            writer.writeheader()
        
        self.tick_files[token] = (file_handle, writer)
        logger.info(f"📝 Created tick file: {filepath}")
    
    def _create_candle_file(self, token: int, interval: str, instrument_name: str = None):
        """Create a new candle CSV file"""
        date_str = self._get_date_string()
        
        if instrument_name:
            filename = f"candles_{interval}_{instrument_name}_{token}_{date_str}.csv"
        else:
            filename = f"candles_{interval}_{token}_{date_str}.csv"
        
        if interval == '1min':
            filepath = self.candles_1min_dir / filename
            file_dict = self.candle_1min_files
        else:  # 5min
            filepath = self.candles_5min_dir / filename
            file_dict = self.candle_5min_files
        
        # Open file in append mode
        file_handle = open(filepath, 'a', newline='')
        
        # Create CSV writer
        fieldnames = ['timestamp', 'token', 'open', 'high', 'low', 'close']
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        
        # Write header if file is new
        if filepath.stat().st_size == 0:
            writer.writeheader()
        
        file_dict[token] = (file_handle, writer)
        logger.info(f"📝 Created candle file: {filepath}")
    
    def close_all_files(self):
        """Close all open file handles"""
        # Close tick files
        for token, (file_handle, _) in self.tick_files.items():
            file_handle.close()
        self.tick_files.clear()
        
        # Close 1-min candle files
        for token, (file_handle, _) in self.candle_1min_files.items():
            file_handle.close()
        self.candle_1min_files.clear()
        
        # Close 5-min candle files
        for token, (file_handle, _) in self.candle_5min_files.items():
            file_handle.close()
        self.candle_5min_files.clear()
        
        logger.info("📁 All data files closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close_all_files()

# Global instance
data_storage = DataStorage()