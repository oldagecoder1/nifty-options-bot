"""
Technical indicators - RSI calculation
"""
import pandas as pd
import numpy as np
from typing import Optional

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate RSI (Relative Strength Index)
    
    Args:
        data: Price data series
        period: RSI period (default 14)
    
    Returns:
        RSI series
    """
    delta = data.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def get_latest_rsi(df: pd.DataFrame, price_column: str = 'close', period: int = 14) -> Optional[float]:
    """
    Get latest RSI value from dataframe
    
    Args:
        df: OHLC dataframe with datetime index
        price_column: Column to use for RSI calculation
        period: RSI period
    
    Returns:
        Latest RSI value or None
    """
    if len(df) < period + 1:
        return None
    
    rsi_series = calculate_rsi(df[price_column], period)
    latest_rsi = rsi_series.iloc[-1]
    
    return latest_rsi if not pd.isna(latest_rsi) else None

def track_rsi_peak(current_rsi: float, peak_rsi: Optional[float]) -> float:
    """
    Track RSI peak value
    
    Args:
        current_rsi: Current RSI value
        peak_rsi: Previously tracked peak RSI
    
    Returns:
        Updated peak RSI
    """
    if peak_rsi is None:
        return current_rsi
    
    return max(peak_rsi, current_rsi)

def check_rsi_exit_condition(current_rsi: float, peak_rsi: float, drop_threshold: float = 10) -> bool:
    """
    Check if RSI drop condition is met for exit
    
    Args:
        current_rsi: Current RSI value
        peak_rsi: Peak RSI value since entry
        drop_threshold: RSI drop threshold for exit
    
    Returns:
        True if exit condition met, False otherwise
    """
    if peak_rsi is None:
        return False
    
    rsi_drop = peak_rsi - current_rsi
    return rsi_drop >= drop_threshold