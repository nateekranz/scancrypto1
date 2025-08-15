# ====================================
# FILE: telegram_bot.py
# DESCRIPTION: Handles Telegram notifications and report formatting
# ====================================

import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List
import config

logger = logging.getLogger(__name__)

def _send_message(message_text: str):
    """Sends a formatted message to the configured Telegram chat."""
    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.warning("Telegram token not configured. Skipping message send.")
        print("--- TELEGRAM REPORT ---")
        print(message_text)
        print("-----------------------")
        return

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': config.TELEGRAM_CHAT_ID,
        'text': message_text,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=config.API_TIMEOUT)
        response.raise_for_status()
        logger.info("Successfully sent report to Telegram.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send message to Telegram: {e}")

def _format_report(macro_data: Dict, micro_data: Dict) -> str:
    """Formats the final analysis data into a markdown string for Telegram."""
    # --- Header ---
    report = "====================================\n"
    report += "  📊 **MARKET INTELLIGENCE REPORT**\n"
    report += "====================================\n\n"

    # --- Macro Analysis ---
    report += "**[ MACRO ANALYSIS ]**\n"
    report += f"- BTC 4H Trend: **{macro_data['btc_trend']}**\n"
    report += f"- Market Regime: **{macro_data['market_regime']}**\n"
    report += f"- News Events: {macro_data['news_warning']} 🗓️\n\n"
    report += "---\n\n"

    # --- Bullish Coins ---
    report += "🔥 **Top 10 Healthy Uptrend Coins** 🔥\n"
    report += "```\n"
    report += "#   Symbol       | Stage    | 24h Change\n"
    report += "------------------------------------------\n"
    if micro_data['bullish']:
        for i, coin in enumerate(micro_data['bullish'], 1):
            stage = coin['stage'].ljust(10)
            symbol = coin['symbol'].ljust(12)
            change = f"{float(coin['price24hPcnt'])*100: >+7.2f}%"
            report += f"{i:<2} {symbol}| {stage} | {change}\n"
    else:
        report += "No qualifying bullish candidates found.\n"
    report += "```\n---\n\n"

    # --- Bearish Coins ---
    report += "💧 **Top 10 Healthy Downtrend Coins** 💧\n"
    report += "```\n"
    report += "#   Symbol       | 24h Change\n"
    report += "---------------------------------\n"
    if micro_data['bearish']:
        for i, coin in enumerate(micro_data['bearish'], 1):
            symbol = coin['symbol'].ljust(12)
            change = f"{float(coin['price24hPcnt'])*100: >+7.2f}%"
            report += f"{i:<2} {symbol}| {change}\n"
    else:
        report += "No qualifying bearish candidates found.\n"
    report += "```\n"

    # --- Recommendation ---
    report += "**[ RECOMMENDATION ]**\n"
    report += f"_{micro_data['recommendation']}_\n\n"

    # --- Footer ---
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    report += f"_Generated: {timestamp}_"

    return report

def generate_and_send_report(macro_data: Dict, micro_data: Dict):
    """Top-level function to format the report and send it."""
    logger.info("Generating and sending final report...")
    report_str = _format_report(macro_data, micro_data)
    _send_message(report_str)

def send_error_report(error_message: str):
    """Sends a simplified error message to Telegram."""
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    report = (
        f"⚠️ **Market Intelligence Bot Error** ⚠️\n\n"
        f"An error occurred during the scan:\n`{error_message}`\n\n"
        f"_Time: {timestamp}_"
    )
    _send_message(report)