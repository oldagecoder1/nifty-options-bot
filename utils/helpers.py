"""
Helper utility functions
"""
from datetime import datetime, time
from typing import Optional
import pytz
from config.settings import settings

def get_current_time() -> datetime:
    """Get current time in IST"""
    return datetime.now(settings.TIMEZONE)

def parse_time_str(time_str: str) -> time:
    """
    Parse time string to time object
    
    Args:
        time_str: Time in format 'HH:MM'
    
    Returns:
        time object
    """
    hour, minute = map(int, time_str.split(':'))
    return time(hour, minute)

def is_market_open() -> bool:
    """Check if market is currently open"""
    current_time = get_current_time().time()
    market_start = parse_time_str(settings.MARKET_START_TIME)
    market_end = parse_time_str(settings.MARKET_END_TIME)
    
    return market_start <= current_time <= market_end

def round_to_nearest(value: float, base: int = 50) -> int:
    """
    Round value to nearest multiple of base
    
    Args:
        value: Value to round
        base: Base multiple (default 50)
    
    Returns:
        Rounded value
    """
    return int(base * round(value / base))

def generate_trade_id(side: str, entry_price: float) -> str:
    """
    Generate unique trade ID
    
    Args:
        side: 'CALL' or 'PUT'
        entry_price: Entry price
    
    Returns:
        Unique trade ID
    """
    timestamp = get_current_time().strftime('%Y%m%d_%H%M%S')
    return f"{timestamp}_{side}_{int(entry_price)}"

def calculate_pnl(entry_price: float, exit_price: float, qty: int, side: str = 'BUY') -> float:
    """
    Calculate P&L for a trade
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        qty: Quantity
        side: 'BUY' or 'SELL'
    
    Returns:
        P&L amount
    """
    if side.upper() == 'BUY':
        return (exit_price - entry_price) * qty
    else:
        return (entry_price - exit_price) * qty

def format_time(dt: Optional[datetime] = None) -> str:
    """Format datetime to string"""
    if dt is None:
        dt = get_current_time()
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def is_between_times(start_time_str: str, end_time_str: str) -> bool:
    """
    Check if current time is between start and end times
    
    Args:
        start_time_str: Start time as 'HH:MM'
        end_time_str: End time as 'HH:MM'
    
    Returns:
        True if current time is between start and end
    """
    current_time = get_current_time().time()
    start_time = parse_time_str(start_time_str)
    end_time = parse_time_str(end_time_str)
    
    return start_time <= current_time <= end_time