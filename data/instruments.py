"""
Instrument management - Load and manage strike data
"""
import pandas as pd
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger('InstrumentManager', level='INFO')

class InstrumentManager:
    """Manage instruments and strike selection"""
    
    def __init__(self, csv_path: str = None):
        """
        Initialize instrument manager
        
        Args:
            csv_path: Path to instruments CSV file
        """
        self.csv_path = csv_path or settings.INSTRUMENTS_CSV_PATH
        self.instruments_df: Optional[pd.DataFrame] = None
        self.load_instruments()
    
    def load_instruments(self):
        """Load instruments from CSV file"""
        try:
            self.instruments_df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.instruments_df)} instruments from {self.csv_path}")
            
            # Expected columns: symbol, token, strike, expiry, option_type, lot_size
            required_cols = ['symbol', 'token', 'strike', 'expiry', 'option_type', 'lot_size']
            missing_cols = [col for col in required_cols if col not in self.instruments_df.columns]
            
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                raise ValueError(f"CSV missing columns: {missing_cols}")
            
            # Convert expiry to datetime
            self.instruments_df['expiry'] = pd.to_datetime(self.instruments_df['expiry'])
            
        except FileNotFoundError:
            logger.error(f"Instruments CSV not found at {self.csv_path}")
            logger.warning("Creating sample CSV template...")
            self._create_sample_csv()
            raise
        except Exception as e:
            logger.error(f"Error loading instruments: {e}")
            raise
    
    def _create_sample_csv(self):
        """Create a sample instruments CSV template"""
        sample_data = {
            'symbol': ['NIFTY24OCT20100CE', 'NIFTY24OCT20100PE'],
            'token': [12345, 67890],
            'strike': [20100, 20100],
            'expiry': ['2024-10-31', '2024-10-31'],
            'option_type': ['CE', 'PE'],
            'lot_size': [75, 75]
        }
        df = pd.DataFrame(sample_data)
        df.to_csv(self.csv_path, index=False)
        logger.info(f"Sample CSV created at {self.csv_path}. Please update with actual data.")
    
    def get_nearest_weekly_expiry(self, from_date: datetime = None) -> datetime:
        """
        Get nearest weekly expiry date
        
        Args:
            from_date: Reference date (default: today)
        
        Returns:
            Nearest weekly expiry datetime
        """
        if from_date is None:
            from_date = datetime.now()
        
        # Filter only option instruments (CE/PE), exclude index/equity
        options_df = self.instruments_df[
            self.instruments_df['option_type'].isin(['CE', 'PE'])
        ]
        
        # Get unique expiry dates from options only
        expiries = sorted(options_df['expiry'].unique())
        
        # Compare only dates (not time) to find nearest expiry >= today
        from_date_only = from_date.date() if hasattr(from_date, 'date') else from_date
        
        for expiry in expiries:
            expiry_date = expiry.date() if hasattr(expiry, 'date') else expiry
            if expiry_date >= from_date_only:
                logger.info(f"Nearest weekly expiry: {expiry.date()}")
                return expiry
        
        logger.warning("No future expiry found, using last available")
        return expiries[-1] if expiries else from_date
    
    def get_strike_data(self, strike: int, option_type: str, expiry: datetime = None) -> Optional[Dict]:
        """
        Get instrument data for specific strike
        
        Args:
            strike: Strike price
            option_type: 'CE' or 'PE'
            expiry: Expiry date (default: nearest weekly)
        
        Returns:
            Dictionary with symbol, token, lot_size or None
        """
        if expiry is None:
            expiry = self.get_nearest_weekly_expiry()
        
        # Filter for matching strike, option_type, and expiry
        mask = (
            (self.instruments_df['strike'] == strike) &
            (self.instruments_df['option_type'] == option_type) &
            (self.instruments_df['expiry'] == expiry)
        )
        
        result = self.instruments_df[mask]
        
        if result.empty:
            logger.warning(f"No data found for {strike} {option_type} expiring {expiry.date()}")
            return None
        
        row = result.iloc[0]
        return {
            'symbol': row['symbol'],
            'token': row['token'],
            'lot_size': int(row['lot_size']),
            'strike': int(row['strike']),
            'option_type': row['option_type'],
            'expiry': row['expiry']
        }
    
    def get_nifty_token(self) -> Optional[int]:
        """Get Nifty spot token"""
        # Assuming Nifty spot is marked with strike=0 or specific symbol
        nifty = self.instruments_df[
            (self.instruments_df['symbol'].str.contains('NIFTY')) &
            (~self.instruments_df['symbol'].str.contains('CE|PE'))
        ]
        
        if not nifty.empty:
            return int(nifty.iloc[0]['token'])
        
        logger.warning("Nifty spot token not found in instruments CSV")
        return None
    
    def get_trading_symbol(self, token: int) -> Optional[str]:
        """
        Get trading symbol for a given token
        
        Args:
            token: Instrument token
            
        Returns:
            Trading symbol with exchange prefix (e.g., 'NSE:NIFTY 50' or 'NFO:NIFTY25O0725000CE')
        """
        try:
            instrument = self.instruments_df[self.instruments_df['token'] == token]
            
            if not instrument.empty:
                row = instrument.iloc[0]
                symbol = row['symbol']
                option_type = row['option_type']
                
                # Determine exchange based on option type
                if option_type == 'EQ' or option_type == 'INDEX':
                    exchange = 'NSE'
                elif option_type in ['CE', 'PE']:
                    exchange = 'NFO'
                else:
                    exchange = 'NFO'  # Default to NFO
                
                return f"{exchange}:{symbol}"
            
            logger.warning(f"Trading symbol not found for token {token}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting trading symbol for token {token}: {e}")
            return None
    
    def validate_strike_liquidity(self, strike: int, option_type: str) -> bool:
        """
        Check if strike has sufficient liquidity (placeholder logic)
        
        Args:
            strike: Strike price
            option_type: 'CE' or 'PE'
        
        Returns:
            True if liquid, False otherwise
        """
        # TODO: Implement actual liquidity check via market depth API
        # For now, just check if strike exists
        data = self.get_strike_data(strike, option_type)
        return data is not None

# Global instance
instrument_manager = InstrumentManager()