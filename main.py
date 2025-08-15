# ====================================
# FILE: main.py
# DESCRIPTION: Main entry point and scheduler for the Market Intelligence Bot.
# ====================================

import logging
import time
import schedule
import config
import utils
import telegram_bot
from analyzer import MarketAnalyzer

def run_scan():
    """Executes the full market scan and reporting process."""
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("STARTING NEW MARKET INTELLIGENCE SCAN")
    logger.info("="*50)
    
    start_time = time.time()
    
    try:
        # Initialize analyzer
        analyzer = MarketAnalyzer()
        
        # Step 1: Macro Analysis
        macro_data = analyzer.analyze_macro_conditions()
        macro_data['news_warning'] = utils.get_current_day_warning() # Add news warning
        
        # Step 2: Micro Analysis
        micro_data = analyzer.analyze_micro_conditions()
        
        # Step 3: Reporting
        telegram_bot.generate_and_send_report(macro_data, micro_data)

    except Exception as e:
        logger.critical(f"A critical error occurred in the main scan loop: {e}", exc_info=True)
        telegram_bot.send_error_report(str(e))
        
    finally:
        execution_time = time.time() - start_time
        logger.info(f"Scan cycle finished in {execution_time:.2f} seconds.")

def main():
    """Main function to initialize and run the bot."""
    utils.setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🤖 Market Intelligence Bot Starting...")
    print("=" * 50)
    print("Configuration:")
    print(f"- Scan Interval: {config.SCAN_INTERVAL_HOURS} hours")
    print(f"- Min Volume: ${config.MIN_VOLUME_24H_USD:,}")
    print(f"- Min Open Interest: ${config.MIN_OPEN_INTEREST_USD:,}")
    print("=" * 50)

    # Schedule the job
    schedule.every(config.SCAN_INTERVAL_HOURS).hours.do(run_scan)

    # Run the first scan immediately
    logger.info("Running initial scan on startup...")
    run_scan()
    
    logger.info(f"Startup scan complete. Bot is now running. Next scan in {config.SCAN_INTERVAL_HOURS} hours.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped manually by user.")
    except Exception as e:
        logging.getLogger(__name__).critical(f"A fatal error caused the bot to stop: {e}", exc_info=True)