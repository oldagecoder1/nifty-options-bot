"""
Run backtesting on historical data
"""
import sys
import argparse
from backtest.backtester import backtester
from utils.logger import setup_logger
from config.settings import settings

# Setup logger
logger = setup_logger('Backtester', './logs/backtest.log', 'INFO')

def main():
    """Main backtest entry point"""
    parser = argparse.ArgumentParser(description='Run strategy backtest on historical data')
    parser.add_argument('--data', type=str, required=True, help='Path to historical data CSV file')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    logger.info("\n" + "="*80)
    logger.info("🔬 STARTING BACKTEST")
    logger.info("="*80)
    logger.info(f"Data file: {args.data}")
    if args.start:
        logger.info(f"Start date: {args.start}")
    if args.end:
        logger.info(f"End date: {args.end}")
    logger.info("="*80 + "\n")
    
    # Print strategy parameters
    print(f"Strategy Parameters:")
    print(f"  Strike Offset: ±{settings.STRIKE_OFFSET}")
    print(f"  Lot Size: {settings.LOT_SIZE}")
    print(f"  Trailing Increment: {settings.TRAILING_INCREMENT}")
    print(f"  RSI Exit Drop: {settings.RSI_EXIT_DROP}")
    print(f"  Daily Loss Limit: ₹{settings.DAILY_LOSS_LIMIT:,.2f}\n")
    
    try:
        # Run backtest
        backtester.run_backtest(
            data_path=args.data,
            start_date=args.start,
            end_date=args.end
        )
        
    except FileNotFoundError:
        logger.error(f"Data file not found: {args.data}")
        logger.info("\nExpected CSV format:")
        logger.info("datetime,nifty_open,nifty_high,nifty_low,nifty_close,")
        logger.info("call_open,call_high,call_low,call_close,")
        logger.info("put_open,put_high,put_low,put_close")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()