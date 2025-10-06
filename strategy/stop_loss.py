"""
Stop loss progression and trailing logic
"""
from typing import Optional
from dataclasses import dataclass
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class StopLossState:
    """Track stop loss state"""
    current_sl: float
    entry_price: float
    is_at_breakeven: bool = False
    reference_low: float = None  # GC for Call, GP for Put
    reference_mid: float = None  # BC for Call, BP for Put
    reference_high: float = None  # RC for Call, RP for Put
    
    last_trailing_level: float = None  # Track last trailing increment

class StopLossManager:
    """Manage stop loss progression and trailing"""
    
    def __init__(self):
        self.state: Optional[StopLossState] = None
    
    def initialize(
        self,
        entry_price: float,
        reference_low: float,
        reference_mid: float,
        reference_high: float
    ):
        """
        Initialize stop loss for a new trade
        
        Args:
            entry_price: Entry price (EC)
            reference_low: GC for Call, GP for Put
            reference_mid: BC for Call, BP for Put
            reference_high: RC for Call, RP for Put
        """
        self.state = StopLossState(
            current_sl=reference_low,
            entry_price=entry_price,
            reference_low=reference_low,
            reference_mid=reference_mid,
            reference_high=reference_high,
            last_trailing_level=entry_price
        )
        
        logger.info(f"🛡️ Initial SL set at {reference_low:.2f} (Entry: {entry_price:.2f})")
    
    def update_progressive_sl(self, current_price: float) -> float:
        """
        Update stop loss based on progressive rules (before breakeven)
        
        Args:
            current_price: Current option price
        
        Returns:
            Updated stop loss value
        """
        if not self.state or self.state.is_at_breakeven:
            return self.state.current_sl if self.state else 0
        
        EC = self.state.entry_price
        GC = self.state.reference_low
        BC = self.state.reference_mid
        RC = self.state.reference_high
        
        old_sl = self.state.current_sl
        
        # Rule 1: If price >= EC + (BC - GC), move SL to BC
        if current_price >= EC + (BC - GC) and self.state.current_sl < BC:
            self.state.current_sl = BC
            logger.info(f"📈 SL moved to BC: {old_sl:.2f} → {BC:.2f}")
        
        # Rule 2: If price >= EC + (RC - GC), move SL to RC
        elif current_price >= EC + (RC - GC) and self.state.current_sl < RC:
            self.state.current_sl = RC
            logger.info(f"📈 SL moved to RC: {old_sl:.2f} → {RC:.2f}")
        
        # Rule 3: If price >= EC + (EC - GC), move SL to EC (breakeven)
        elif current_price >= EC + (EC - GC) and self.state.current_sl < EC:
            self.state.current_sl = EC
            self.state.is_at_breakeven = True
            logger.info(f"🎯 SL moved to BREAKEVEN: {old_sl:.2f} → {EC:.2f}")
        
        return self.state.current_sl
    
    def update_trailing_sl(self, current_price: float) -> float:
        """
        Update trailing stop loss (after breakeven)
        
        Args:
            current_price: Current option price
        
        Returns:
            Updated stop loss value
        """
        if not self.state or not self.state.is_at_breakeven:
            return self.state.current_sl if self.state else 0
        
        EC = self.state.entry_price
        increment = settings.TRAILING_INCREMENT
        
        # Calculate how many increments above entry
        price_above_entry = current_price - EC
        num_increments = int(price_above_entry / increment)
        
        if num_increments > 0:
            new_trailing_level = EC + (num_increments * increment)
            
            # Only update if we've crossed a new increment level
            if new_trailing_level > self.state.last_trailing_level:
                old_sl = self.state.current_sl
                self.state.current_sl = new_trailing_level
                self.state.last_trailing_level = new_trailing_level
                
                logger.info(f"🔼 Trailing SL updated: {old_sl:.2f} → {new_trailing_level:.2f}")
        
        return self.state.current_sl
    
    def check_stop_loss_hit(self, current_price: float) -> bool:
        """
        Check if stop loss is hit
        
        Args:
            current_price: Current option price
        
        Returns:
            True if SL hit, False otherwise
        """
        if not self.state:
            return False
        
        if current_price <= self.state.current_sl:
            logger.warning(f"🛑 STOP LOSS HIT: Price {current_price:.2f} <= SL {self.state.current_sl:.2f}")
            return True
        
        return False
    
    def get_current_sl(self) -> Optional[float]:
        """Get current stop loss value"""
        return self.state.current_sl if self.state else None
    
    def is_breakeven_reached(self) -> bool:
        """Check if breakeven is reached"""
        return self.state.is_at_breakeven if self.state else False
    
    def reset(self):
        """Reset stop loss state"""
        self.state = None
        logger.info("Stop loss state reset")

# Global instance
stop_loss_manager = StopLossManager()