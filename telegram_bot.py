# ====================================
# FILE: telegram_bot.py (v2.0 - Class-based & Patched)
# DESCRIPTION: Handles Telegram notifications and report formatting.
# ====================================

import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List
import config
import utils  # [แก้ไข] เพิ่ม import ที่ขาดไป

logger = logging.getLogger(__name__)

class TelegramBot:
    """A class to handle all Telegram-related functionalities."""

    def generate_report(self, full_analysis_result: Dict) -> str:
        """Formats the final analysis data into a markdown string for Telegram."""
        macro_data = full_analysis_result.get("macro", {})
        micro_data = full_analysis_result.get("micro", {})
        
        # --- Header ---
        report = "====================================\n"
        report += "  📊 **MARKET INTELLIGENCE REPORT**\n"
        report += "====================================\n\n"

        # --- Macro Analysis ---
        report += "**[ MACRO ANALYSIS ]**\n"
        report += f"- BTC 4H Trend: **{macro_data.get('btc_trend', 'N/A')}**\n"
        report += f"- Market Regime: **{macro_data.get('market_regime', 'N/A')}**\n"
        # [แก้ไข] เรียกใช้ฟังก์ชันจาก utils ที่ import เข้ามาแล้ว
        report += f"- News Events: {utils.get_current_day_warning()} 🗓️\n\n"
        report += "---\n\n"

        # --- Bullish Coins ---
        bullish_coins = micro_data.get('bullish', [])
        report += "🔥 **Top Healthy Uptrend Coins** 🔥\n"
        report += "```\n"
        report += "#   Symbol       | Stage    | 24h Change\n"
        report += "------------------------------------------\n"
        if bullish_coins:
            for i, coin in enumerate(bullish_coins, 1):
                stage = coin.get('stage', 'N/A').ljust(10)
                symbol = coin.get('symbol', 'N/A').ljust(12)
                try:
                    change_val = float(coin.get('price24hPcnt', 0)) * 100
                    change = f"{change_val: >+7.2f}%"
                except (ValueError, TypeError):
                    change = " N/A"
                report += f"{i:<2} {symbol}| {stage} | {change}\n"
        else:
            report += "No qualifying bullish candidates found.\n"
        report += "```\n---\n\n"

        # --- Bearish Coins ---
        bearish_coins = micro_data.get('bearish', [])
        report += "💧 **Top Healthy Downtrend Coins** 💧\n"
        report += "```\n"
        report += "#   Symbol       | 24h Change\n"
        report += "---------------------------------\n"
        if bearish_coins:
            for i, coin in enumerate(bearish_coins, 1):
                symbol = coin.get('symbol', 'N/A').ljust(12)
                try:
                    change_val = float(coin.get('price24hPcnt', 0)) * 100
                    change = f"{change_val: >+7.2f}%"
                except (ValueError, TypeError):
                    change = " N/A"
                report += f"{i:<2} {symbol}| {change}\n"
        else:
            report += "No qualifying bearish candidates found.\n"
        report += "```\n\n"

        # --- Recommendation ---
        recommendation = self._generate_recommendation(macro_data)
        report += "**[ RECOMMENDATION ]**\n"
        report += f"_{recommendation}_\n\n"

        # --- Footer ---
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        report += f"_Generated: {timestamp}_"
        return report
        
    def _generate_recommendation(self, macro_data: Dict) -> str:
        """Generates a trading recommendation based on market conditions."""
        btc_trend = macro_data.get('btc_trend', '')
        market_regime = macro_data.get('market_regime', '')

        if "BULLISH" in btc_trend and "Trending" in market_regime:
            return "Market conditions are favorable. Prioritize Early Stage 🌱 candidates."
        elif "BEARISH" in btc_trend:
            return "Market shows bearish bias. Consider short opportunities or wait."
        else:
            return "Mixed signals detected. Exercise caution and wait for a clearer market direction."

    def send_message(self, message_text: str):
        """Sends a formatted message to the configured Telegram chat."""
        if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
            logger.warning("Telegram token not configured. Skipping message send.")
            print("\n--- TELEGRAM REPORT ---\n")
            print(message_text)
            print("\n-----------------------\n")
            return

        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {'chat_id': config.TELEGRAM_CHAT_ID, 'text': message_text, 'parse_mode': 'Markdown'}
        try:
            response = requests.post(url, json=payload, timeout=config.API_TIMEOUT)
            response.raise_for_status()
            logger.info("Successfully sent report to Telegram.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message to Telegram: {e}")
            
    def generate_error_report(self, error_message: str) -> str:
        """Generates a simplified error message string."""
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        return (
            f"⚠️ **Market Intelligence Bot Error** ⚠️\n\n"
            f"An error occurred during the scan:\n`{error_message}`\n\n"
            f"_Time: {timestamp}_"
        )