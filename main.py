# ====================================
# FILE: main.py (v2.0 - Refactored)
# DESCRIPTION: Main entry point and scheduler for the Market Intelligence Bot.
# ====================================

import logging
import time
import schedule
import config
import utils
from analyzer import MarketAnalyzer
from telegram_bot import TelegramBot

def run_scan():
    """Executes the full market scan and reporting process."""
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("STARTING NEW MARKET INTELLIGENCE SCAN")
    
    start_time = time.time()
    
    try:
        # [แก้ไข] สร้าง instance ของ Analyzer และ Bot
        analyzer = MarketAnalyzer()
        bot = TelegramBot()

        # [แก้ไข] เรียกใช้ analysis แค่ครั้งเดียว ได้ผลลัพธ์ทั้งหมด
        full_analysis_result = analyzer.run_full_analysis()
        
        # [แก้ไข] สร้างและส่ง report จากผลลัพธ์ก้อนเดียว
        report = bot.generate_report(full_analysis_result)
        bot.send_message(report)

    except Exception as e:
        logger.critical(f"A critical error occurred in the main scan loop: {e}", exc_info=True)
        # ส่ง report แจ้งเตือน error ผ่าน bot
        error_bot = TelegramBot()
        error_report = error_bot.generate_error_report(str(e))
        error_bot.send_message(error_report)
        
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
    # [แก้ไข] แสดงผลค่า Filter ทั้ง 2 โหมด
    print(f"- Strict Filters (Trending): Vol/OI > ${config.STRICT_MIN_VOLUME_24H:,}")
    print(f"- Relaxed Filters (Quiet/Chop): Vol/OI > ${config.RELAXED_MIN_VOLUME_24H:,}")
    print("=" * 50)

    # Schedule the job to run at specified intervals
    schedule.every(config.SCAN_INTERVAL_HOURS).hours.do(run_scan)

    # Run the first scan immediately on startup
    logger.info("Running initial scan on startup...")
    run_scan()
    
    logger.info(f"Startup scan complete. Bot is now running. Next scan in {config.SCAN_INTERVAL_HOURS} hours.")
    
    # Main loop to run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped manually by user.")
    except Exception as e:
        # Log any fatal error that stops the main loop
        logging.getLogger(__name__).critical(f"A fatal error caused the bot to stop: {e}", exc_info=True)