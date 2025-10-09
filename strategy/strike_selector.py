"""
Strike selection logic based on Nifty spot price
"""
from typing import Dict, Optional, Tuple
from config.settings import settings
from data.instruments import instrument_manager
from utils.helpers import round_to_nearest
from utils.logger import setup_logger

logger = setup_logger('StrikeSelector', level='INFO')

class StrikeSelector:
    """Select Call and Put strikes based on Nifty spot"""
    
    def __init__(self):
        self.selected_call_strike: Optional[int] = None
        self.selected_put_strike: Optional[int] = None
        self.call_instrument: Optional[Dict] = None
        self.put_instrument: Optional[Dict] = None
    
    def select_strikes(self, nifty_spot: float) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Select Call and Put strikes based on Nifty spot price
        
        Args:
            nifty_spot: Current Nifty spot price
        
        Returns:
            Tuple of (call_instrument, put_instrument) dictionaries
        """
        offset = settings.STRIKE_OFFSET
        
        # Calculate strikes
        call_strike = round_to_nearest(nifty_spot - offset, 50)
        put_strike = round_to_nearest(nifty_spot + offset, 50)
        
        logger.info(f"Nifty Spot: {nifty_spot:.2f}")
        logger.info(f"Selected Call Strike: {call_strike} CE")
        logger.info(f"Selected Put Strike: {put_strike} PE")
        
        # Get nearest weekly expiry
        expiry = instrument_manager.get_nearest_weekly_expiry()
        
        # Get Call instrument data
        self.call_instrument = instrument_manager.get_strike_data(call_strike, 'CE', expiry)
        if not self.call_instrument:
            logger.warning(f"Call strike {call_strike} CE not found, trying ±50")
            # Try alternate strikes
            for alt_strike in [call_strike + 50, call_strike - 50]:
                self.call_instrument = instrument_manager.get_strike_data(alt_strike, 'CE', expiry)
                if self.call_instrument:
                    call_strike = alt_strike
                    logger.info(f"Using alternate Call strike: {call_strike} CE")
                    break
        
        # Get Put instrument data
        self.put_instrument = instrument_manager.get_strike_data(put_strike, 'PE', expiry)
        if not self.put_instrument:
            logger.warning(f"Put strike {put_strike} PE not found, trying ±50")
            # Try alternate strikes
            for alt_strike in [put_strike + 50, put_strike - 50]:
                self.put_instrument = instrument_manager.get_strike_data(alt_strike, 'PE', expiry)
                if self.put_instrument:
                    put_strike = alt_strike
                    logger.info(f"Using alternate Put strike: {put_strike} PE")
                    break
        
        # Validate liquidity
        if self.call_instrument and not instrument_manager.validate_strike_liquidity(call_strike, 'CE'):
            logger.warning(f"Call strike {call_strike} may be illiquid")
        
        if self.put_instrument and not instrument_manager.validate_strike_liquidity(put_strike, 'PE'):
            logger.warning(f"Put strike {put_strike} may be illiquid")
        
        self.selected_call_strike = call_strike
        self.selected_put_strike = put_strike
        
        return self.call_instrument, self.put_instrument
    
    def get_selected_strikes(self) -> Tuple[Optional[int], Optional[int]]:
        """Get currently selected strikes"""
        return self.selected_call_strike, self.selected_put_strike
    
    def get_instruments(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Get selected instrument data"""
        return self.call_instrument, self.put_instrument
    
    def reset(self):
        """Reset strike selection"""
        self.selected_call_strike = None
        self.selected_put_strike = None
        self.call_instrument = None
        self.put_instrument = None
        logger.info("Strike selection reset")

# Global instance
strike_selector = StrikeSelector()