"""
Configuration settings with KiteConnect phase support
"""
import os
from dotenv import load_dotenv
import pytz

load_dotenv()

class Settings:
    """Application settings from environment variables"""
    
    # Phase Configuration
    TRADING_PHASE: int = int(os.getenv('TRADING_PHASE', '1'))
    
    # Phase 1: Mock data + Paper trading
    # Phase 2: Real KiteConnect data + Paper trading  
    # Phase 3: Real KiteConnect data + Real orders
    
    @classmethod
    def is_using_real_data(cls) -> bool:
        """Check if using real broker data (Phase 2 or 3)"""
        return cls.TRADING_PHASE >= 2
    
    @classmethod
    def is_live_trading(cls) -> bool:
        """Check if placing real orders (Phase 3)"""
        return cls.TRADING_PHASE == 3
    
    # KiteConnect Configuration
    KITE_API_KEY: str = os.getenv('KITE_API_KEY', '')
    KITE_API_SECRET: str = os.getenv('KITE_API_SECRET', '')
    KITE_ACCESS_TOKEN: str = os.getenv('KITE_ACCESS_TOKEN', '')
    
    # Strategy Parameters
    STRIKE_OFFSET: int = int(os.getenv('STRIKE_OFFSET', '200'))
    LOT_SIZE: int = int(os.getenv('LOT_SIZE', '75'))
    DAILY_LOSS_LIMIT: float = float(os.getenv('DAILY_LOSS_LIMIT', '10000'))
    MAX_POSITIONS: int = int(os.getenv('MAX_POSITIONS', '1'))
    
    # Time Settings
    MARKET_START_TIME: str = os.getenv('MARKET_START_TIME', '09:15')
    REFERENCE_WINDOW_START: str = os.getenv('REFERENCE_WINDOW_START', '10:00')
    REFERENCE_WINDOW_END: str = os.getenv('REFERENCE_WINDOW_END', '10:15')
    STRIKE_SELECTION_TIME: str = os.getenv('STRIKE_SELECTION_TIME', '10:15')
    HARD_EXIT_TIME: str = os.getenv('HARD_EXIT_TIME', '15:15')
    MARKET_END_TIME: str = os.getenv('MARKET_END_TIME', '15:30')
    
    # Trailing Stop Loss
    TRAILING_INCREMENT: float = float(os.getenv('TRAILING_INCREMENT', '20'))
    RSI_EXIT_DROP: float = float(os.getenv('RSI_EXIT_DROP', '10'))
    
    # AlgoTest API
    ALGOTEST_API_KEY: str = os.getenv('ALGOTEST_API_KEY', '')
    ALGOTEST_API_SECRET: str = os.getenv('ALGOTEST_API_SECRET', '')
    ALGOTEST_BASE_URL: str = os.getenv('ALGOTEST_BASE_URL', 'https://api.algotest.in/v1')
    
    # Data & Logging
    INSTRUMENTS_CSV_PATH: str = os.getenv('INSTRUMENTS_CSV_PATH', './data/instruments.csv')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH: str = os.getenv('LOG_FILE_PATH', './logs/trading.log')
    TIMEZONE: pytz.timezone = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Kolkata'))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        errors = []
        
        # Phase 2 & 3 require KiteConnect credentials
        if cls.is_using_real_data():
            if not cls.KITE_API_KEY:
                errors.append("KITE_API_KEY required for Phase 2/3")
            if not cls.KITE_ACCESS_TOKEN:
                errors.append("KITE_ACCESS_TOKEN required for Phase 2/3")
        
        # Phase 3 requires AlgoTest
        if cls.is_live_trading():
            if not cls.ALGOTEST_API_KEY:
                errors.append("ALGOTEST_API_KEY required for Phase 3")
        
        if cls.STRIKE_OFFSET <= 0:
            errors.append("STRIKE_OFFSET must be positive")
        
        if errors:
            for error in errors:
                print(f"❌ Configuration Error: {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        phase_names = {
            1: "📝 PHASE 1: Mock Data + Paper Trading",
            2: "📊 PHASE 2: KiteConnect Data + Paper Trading", 
            3: "🔴 PHASE 3: KiteConnect Data + LIVE Trading"
        }
        
        print("\n" + "="*60)
        print("📊 NIFTY OPTIONS TRADING BOT - CONFIGURATION")
        print("="*60)
        print(f"Mode: {phase_names.get(cls.TRADING_PHASE, 'Unknown')}")
        print(f"Using Real Data: {'✅ Yes' if cls.is_using_real_data() else '❌ No (Mock)'}")
        print(f"Live Orders: {'🔴 YES' if cls.is_live_trading() else '📝 No (Paper)'}")
        print(f"Strike Offset: ±{cls.STRIKE_OFFSET}")
        print(f"Lot Size: {cls.LOT_SIZE}")
        print(f"Daily Loss Limit: ₹{cls.DAILY_LOSS_LIMIT:,.2f}")
        print(f"Trailing Increment: {cls.TRAILING_INCREMENT}")
        print(f"RSI Exit Drop: {cls.RSI_EXIT_DROP}")
        print("="*60 + "\n")

# Global settings instance
settings = Settings()