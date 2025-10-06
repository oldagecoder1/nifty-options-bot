"""
Calculate and store reference levels from 10:00-10:15 candle
"""
from typing import Dict, Optional
import pandas as pd
from dataclasses import dataclass
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ReferenceLevels:
    """Reference levels for Nifty and options"""
    # Nifty levels
    RN: float  # Nifty high
    GN: float  # Nifty low
    BN: float  # Nifty midpoint
    
    # Call option levels
    RC: float  # Call high
    GC: float  # Call low
    BC: float  # Call midpoint
    
    # Put option levels
    RP: float  # Put high
    GP: float  # Put low
    BP: float  # Put midpoint
    
    def __str__(self):
        return (
            f"Nifty: RN={self.RN:.2f}, GN={self.GN:.2f}, BN={self.BN:.2f}\n"
            f"Call:  RC={self.RC:.2f}, GC={self.GC:.2f}, BC={self.BC:.2f}\n"
            f"Put:   RP={self.RP:.2f}, GP={self.GP:.2f}, BP={self.BP:.2f}"
        )

class ReferenceCalculator:
    """Calculate reference levels from the 10:00-10:15 candle"""
    
    def __init__(self):
        self.levels: Optional[ReferenceLevels] = None
    
    def calculate_from_candle(
        self,
        nifty_df: pd.DataFrame,
        call_df: pd.DataFrame,
        put_df: pd.DataFrame
    ) -> ReferenceLevels:
        """
        Calculate reference levels from 15-min candle data
        
        Args:
            nifty_df: Nifty OHLC data for 10:00-10:15
            call_df: Call option OHLC data for 10:00-10:15
            put_df: Put option OHLC data for 10:00-10:15
        
        Returns:
            ReferenceLevels object
        """
        # Nifty levels
        RN = nifty_df['high'].max()
        GN = nifty_df['low'].min()
        BN = (RN + GN) / 2
        
        # Call levels
        RC = call_df['high'].max()
        GC = call_df['low'].min()
        BC = (RC + GC) / 2
        
        # Put levels
        RP = put_df['high'].max()
        GP = put_df['low'].min()
        BP = (RP + GP) / 2
        
        self.levels = ReferenceLevels(
            RN=RN, GN=GN, BN=BN,
            RC=RC, GC=GC, BC=BC,
            RP=RP, GP=GP, BP=BP
        )
        
        logger.info("Reference levels calculated:")
        logger.info(f"\n{self.levels}")
        
        return self.levels
    
    def get_levels(self) -> Optional[ReferenceLevels]:
        """Get stored reference levels"""
        return self.levels
    
    def reset(self):
        """Reset reference levels"""
        self.levels = None
        logger.info("Reference levels reset")

# Global instance
reference_calculator = ReferenceCalculator()