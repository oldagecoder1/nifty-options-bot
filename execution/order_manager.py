"""
Order execution with phase support
Phase 1 & 2: Paper trading (mock orders)
Phase 3: Real orders via AlgoTest
"""
import requests
import time
from typing import Dict, Optional
from config.settings import settings
from utils.logger import get_logger
from utils.helpers import generate_trade_id

logger = get_logger(__name__)

class OrderManager:
    """Manage order execution based on trading phase"""
    
    def __init__(self):
        self.base_url = settings.ALGOTEST_BASE_URL
        self.api_key = settings.ALGOTEST_API_KEY
        self.api_secret = settings.ALGOTEST_API_SECRET
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.max_retries = 3
    
    def place_entry_order(
        self,
        symbol: str,
        qty: int,
        entry_price: float,
        trade_id: str,
        side: str = 'BUY'
    ) -> Dict:
        """Place entry order"""
        
        payload = {
            'signal_type': 'ENTRY',
            'trade_id': trade_id,
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'order_type': 'MARKET',
            'price': entry_price,
            'timestamp': time.time()
        }
        
        if settings.is_live_trading():
            # Phase 3: Real orders
            logger.info("🔴 PHASE 3: Placing REAL order via AlgoTest")
            return self._send_real_order(payload, trade_id)
        else:
            # Phase 1 & 2: Paper trading
            logger.info(f"📝 PHASE {settings.TRADING_PHASE}: Simulating order (Paper Trading)")
            return self._simulate_order(payload)
    
    def place_exit_order(
        self,
        symbol: str,
        qty: int,
        exit_price: float,
        trade_id: str,
        exit_reason: str,
        side: str = 'SELL'
    ) -> Dict:
        """Place exit order"""
        
        payload = {
            'signal_type': 'EXIT',
            'trade_id': trade_id,
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'order_type': 'MARKET',
            'price': exit_price,
            'exit_reason': exit_reason,
            'timestamp': time.time()
        }
        
        if settings.is_live_trading():
            # Phase 3: Real orders
            logger.info("🔴 PHASE 3: Placing REAL exit order")
            return self._send_real_order(payload, trade_id)
        else:
            # Phase 1 & 2: Paper trading
            logger.info(f"📝 PHASE {settings.TRADING_PHASE}: Simulating exit (Paper Trading)")
            return self._simulate_order(payload)
    
    def _send_real_order(self, payload: Dict, idempotency_key: str) -> Dict:
        """Send real order to AlgoTest API (Phase 3 only)"""
        
        headers = self.headers.copy()
        headers['Idempotency-Key'] = idempotency_key
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Sending {payload['signal_type']} order (attempt {attempt}/{self.max_retries})")
                
                response = requests.post(
                    f"{self.base_url}/signals",  # Adjust endpoint as per AlgoTest docs
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"✅ Order placed successfully: {result}")
                return result
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Order API error (attempt {attempt}): {e}")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded. Order failed.")
                    return {
                        'status': 'error',
                        'message': str(e),
                        'payload': payload
                    }
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return {
                    'status': 'error',
                    'message': str(e),
                    'payload': payload
                }
        
        return {'status': 'error', 'message': 'Unknown error'}
    
    def _simulate_order(self, payload: Dict) -> Dict:
        """Simulate order for paper trading (Phase 1 & 2)"""
        
        order_id = f"PAPER_{int(time.time() * 1000)}"
        
        result = {
            'status': 'success',
            'order_id': order_id,
            'message': f'Paper trading - {payload["signal_type"]} simulated',
            'payload': payload,
            'filled_qty': payload['qty'],
            'average_price': payload['price']
        }
        
        logger.info(f"📝 Simulated {payload['signal_type']}: {payload['symbol']} @ ₹{payload['price']:.2f}")
        
        return result
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status"""
        
        if settings.is_live_trading():
            # Phase 3: Real order status
            try:
                response = requests.get(
                    f"{self.base_url}/orders/{order_id}",
                    headers=self.headers,
                    timeout=10
                )
                return response.json()
            except Exception as e:
                logger.error(f"Error checking order status: {e}")
                return None
        else:
            # Phase 1 & 2: Mock status
            return {
                'order_id': order_id,
                'status': 'COMPLETE',
                'message': 'Paper trading - order simulated'
            }
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        
        if settings.is_live_trading():
            # Phase 3: Real cancellation
            try:
                response = requests.delete(
                    f"{self.base_url}/orders/{order_id}",
                    headers=self.headers,
                    timeout=10
                )
                logger.info(f"Order {order_id} cancelled")
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Error cancelling order: {e}")
                return False
        else:
            # Phase 1 & 2: Mock cancellation
            logger.info(f"📝 Simulated order cancellation: {order_id}")
            return True

# Global instance
order_manager = OrderManager()