"""
Paper trading simulation and logging
"""
import csv
import os
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from config.settings import settings
from utils.logger import get_logger
from utils.helpers import get_current_time, calculate_pnl, format_time

logger = get_logger(__name__)

@dataclass
class PaperTrade:
    """Paper trade record"""
    trade_id: str
    timestamp: str
    action: str  # ENTRY or EXIT
    symbol: str
    side: str  # CALL or PUT
    qty: int
    price: float
    stop_loss: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl: Optional[float] = None

class PaperTradingManager:
    """Manage paper trading simulation"""
    
    def __init__(self):
        self.trades_dir = './trades'
        os.makedirs(self.trades_dir, exist_ok=True)
        
        self.current_date = get_current_time().strftime('%Y%m%d')
        self.csv_file = os.path.join(self.trades_dir, f'paper_trades_{self.current_date}.csv')
        
        self.trades: List[PaperTrade] = []
        self.active_trade: Optional[Dict] = None
        
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'trade_id', 'timestamp', 'action', 'symbol', 'side',
                    'qty', 'price', 'stop_loss', 'exit_reason', 'pnl'
                ])
                writer.writeheader()
            logger.info(f"Created paper trading CSV: {self.csv_file}")
    
    def log_entry(
        self,
        trade_id: str,
        symbol: str,
        side: str,
        qty: int,
        entry_price: float,
        stop_loss: float
    ) -> Dict:
        """
        Log paper trade entry
        
        Args:
            trade_id: Unique trade ID
            symbol: Trading symbol
            side: CALL or PUT
            qty: Quantity
            entry_price: Entry price
            stop_loss: Initial stop loss
        
        Returns:
            Entry confirmation dictionary
        """
        trade = PaperTrade(
            trade_id=trade_id,
            timestamp=format_time(),
            action='ENTRY',
            symbol=symbol,
            side=side,
            qty=qty,
            price=entry_price,
            stop_loss=stop_loss
        )
        
        self.trades.append(trade)
        self._write_to_csv(trade)
        
        # Store active trade for exit calculation
        self.active_trade = {
            'trade_id': trade_id,
            'symbol': symbol,
            'side': side,
            'qty': qty,
            'entry_price': entry_price,
            'entry_time': trade.timestamp
        }
        
        logger.info(f"📝 PAPER ENTRY: {side} {symbol} @ {entry_price:.2f} | Qty: {qty} | SL: {stop_loss:.2f}")
        
        return {
            'status': 'success',
            'trade_id': trade_id,
            'action': 'ENTRY',
            'price': entry_price
        }
    
    def log_exit(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str
    ) -> Dict:
        """
        Log paper trade exit
        
        Args:
            trade_id: Trade ID
            exit_price: Exit price
            exit_reason: Reason for exit
        
        Returns:
            Exit confirmation with P&L
        """
        if not self.active_trade or self.active_trade['trade_id'] != trade_id:
            logger.error(f"No active trade found for ID: {trade_id}")
            return {'status': 'error', 'message': 'No active trade'}
        
        # Calculate P&L
        entry_price = self.active_trade['entry_price']
        qty = self.active_trade['qty']
        pnl = calculate_pnl(entry_price, exit_price, qty, 'BUY')
        
        trade = PaperTrade(
            trade_id=trade_id,
            timestamp=format_time(),
            action='EXIT',
            symbol=self.active_trade['symbol'],
            side=self.active_trade['side'],
            qty=qty,
            price=exit_price,
            exit_reason=exit_reason,
            pnl=pnl
        )
        
        self.trades.append(trade)
        self._write_to_csv(trade)
        
        logger.info(f"📝 PAPER EXIT: {self.active_trade['side']} @ {exit_price:.2f} | "
                   f"Reason: {exit_reason} | P&L: ₹{pnl:,.2f}")
        
        # Clear active trade
        result = {
            'status': 'success',
            'trade_id': trade_id,
            'action': 'EXIT',
            'exit_price': exit_price,
            'entry_price': entry_price,
            'pnl': pnl,
            'exit_reason': exit_reason
        }
        
        self.active_trade = None
        
        return result
    
    def _write_to_csv(self, trade: PaperTrade):
        """Write trade to CSV file"""
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'trade_id', 'timestamp', 'action', 'symbol', 'side',
                    'qty', 'price', 'stop_loss', 'exit_reason', 'pnl'
                ])
                writer.writerow(asdict(trade))
        except Exception as e:
            logger.error(f"Error writing to CSV: {e}")
    
    def get_daily_pnl(self) -> float:
        """Calculate total P&L for the day"""
        total_pnl = sum(
            trade.pnl for trade in self.trades
            if trade.action == 'EXIT' and trade.pnl is not None
        )
        return total_pnl
    
    def get_active_trade(self) -> Optional[Dict]:
        """Get current active trade"""
        return self.active_trade
    
    def has_active_trade(self) -> bool:
        """Check if there's an active trade"""
        return self.active_trade is not None
    
    def generate_summary(self) -> Dict:
        """Generate daily trading summary"""
        exits = [t for t in self.trades if t.action == 'EXIT']
        
        if not exits:
            return {
                'total_trades': 0,
                'total_pnl': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0
            }
        
        total_pnl = sum(t.pnl for t in exits if t.pnl)
        winning = [t for t in exits if t.pnl and t.pnl > 0]
        losing = [t for t in exits if t.pnl and t.pnl <= 0]
        
        summary = {
            'total_trades': len(exits),
            'total_pnl': total_pnl,
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(exits) * 100) if exits else 0,
            'avg_win': sum(t.pnl for t in winning) / len(winning) if winning else 0,
            'avg_loss': sum(t.pnl for t in losing) / len(losing) if losing else 0
        }
        
        return summary
    
    def print_summary(self):
        """Print daily summary"""
        summary = self.generate_summary()
        
        print("\n" + "="*60)
        print("📊 PAPER TRADING DAILY SUMMARY")
        print("="*60)
        print(f"Total Trades: {summary['total_trades']}")
        print(f"Total P&L: ₹{summary['total_pnl']:,.2f}")
        print(f"Winning Trades: {summary['winning_trades']}")
        print(f"Losing Trades: {summary['losing_trades']}")
        print(f"Win Rate: {summary['win_rate']:.2f}%")
        if summary['avg_win'] > 0:
            print(f"Average Win: ₹{summary['avg_win']:,.2f}")
        if summary['avg_loss'] < 0:
            print(f"Average Loss: ₹{summary['avg_loss']:,.2f}")
        print("="*60)
        print(f"📁 Trade log saved to: {self.csv_file}\n")

# Global instance
paper_trading_manager = PaperTradingManager()