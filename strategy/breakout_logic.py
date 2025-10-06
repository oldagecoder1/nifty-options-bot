"""
Breakout and confirmation detection logic
"""
from typing import Optional, Literal
import pandas as pd
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

TradeSide = Literal['CALL', 'PUT', 'NONE']

@dataclass
class BreakoutState:
    """Track breakout state"""
    detected: bool = False
    breakout_high: Optional[float] = None
    breakout_candle_close: Optional[float] = None
    confirmation_pending: bool = False

class BreakoutDetector:
    """Detect breakout and confirmation for entry"""
    
    def __init__(self):
        self.call_breakout = BreakoutState()
        self.put_breakout = BreakoutState()
        self.current_side: TradeSide = 'NONE'
    
    def decide_side(self, nifty_candle: pd.Series, RN: float, GN: float) -> TradeSide:
        """
        Decide trading side based on Nifty 5-min candle
        
        Args:
            nifty_candle: Nifty 5-min candle (with open, high, low, close)
            RN: Nifty reference high
            GN: Nifty reference low
        
        Returns:
            'CALL', 'PUT', or 'NONE'
        """
        close = nifty_candle['close']
        open_price = nifty_candle['open']
        
        # Green candle above RN -> CALL
        if close > open_price and close > RN:
            self.current_side = 'CALL'
            logger.info(f"✅ Side selected: CALL (Nifty close {close:.2f} > RN {RN:.2f})")
            return 'CALL'
        
        # Red candle below GN -> PUT
        elif close < open_price and close < GN:
            self.current_side = 'PUT'
            logger.info(f"✅ Side selected: PUT (Nifty close {close:.2f} < GN {GN:.2f})")
            return 'PUT'
        
        return 'NONE'
    
    def check_breakout(
        self,
        option_candle: pd.Series,
        reference_high: float,
        side: TradeSide
    ) -> bool:
        """
        Check if breakout occurred
        
        Args:
            option_candle: Option 5-min candle
            reference_high: RC for Call or RP for Put
            side: 'CALL' or 'PUT'
        
        Returns:
            True if breakout detected, False otherwise
        """
        if side not in ['CALL', 'PUT']:
            return False
        
        state = self.call_breakout if side == 'CALL' else self.put_breakout
        
        # Already detected, waiting for confirmation
        if state.detected and state.confirmation_pending:
            return False
        
        close = option_candle['close']
        open_price = option_candle['open']
        high = option_candle['high']
        
        # Must be green candle closing above reference high
        if close > open_price and close > reference_high:
            state.detected = True
            state.breakout_high = high
            state.breakout_candle_close = close
            state.confirmation_pending = True
            
            logger.info(f"🔔 BREAKOUT detected on {side}: Close={close:.2f} > Ref={reference_high:.2f}")
            return True
        
        return False
    
    def check_confirmation(
        self,
        option_candle: pd.Series,
        reference_high: float,
        side: TradeSide
    ) -> bool:
        """
        Check if confirmation occurred after breakout
        
        Args:
            option_candle: Option 5-min candle (next candle after breakout)
            reference_high: RC for Call or RP for Put
            side: 'CALL' or 'PUT'
        
        Returns:
            True if confirmation detected, False otherwise
        """
        if side not in ['CALL', 'PUT']:
            return False
        
        state = self.call_breakout if side == 'CALL' else self.put_breakout
        
        # No breakout detected yet
        if not state.detected or not state.confirmation_pending:
            return False
        
        close = option_candle['close']
        open_price = option_candle['open']
        
        # Must be green candle closing above both breakout high AND reference high
        if (close > open_price and 
            close > state.breakout_high and 
            close > reference_high):
            
            state.confirmation_pending = False
            logger.info(f"✅ CONFIRMATION on {side}: Close={close:.2f} > Breakout High={state.breakout_high:.2f}")
            return True
        
        # Reset if failed to confirm
        logger.warning(f"❌ Confirmation failed on {side}, resetting breakout state")
        state.detected = False
        state.breakout_high = None
        state.breakout_candle_close = None
        state.confirmation_pending = False
        
        return False
    
    def reset_breakout(self, side: TradeSide):
        """Reset breakout state for a side"""
        if side == 'CALL':
            self.call_breakout = BreakoutState()
        elif side == 'PUT':
            self.put_breakout = BreakoutState()
        logger.info(f"Breakout state reset for {side}")
    
    def reset_all(self):
        """Reset all breakout states"""
        self.call_breakout = BreakoutState()
        self.put_breakout = BreakoutState()
        self.current_side = 'NONE'
        logger.info("All breakout states reset")
    
    def get_current_side(self) -> TradeSide:
        """Get current trading side"""
        return self.current_side

# Global instance
breakout_detector = BreakoutDetector()