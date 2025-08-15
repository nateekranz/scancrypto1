# config.py
"""Configuration file for Market Intelligence Bot."""

# --- TELEGRAM CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "7673207599:AAGieVWYvOl34OB0Lth8_Bsszw2fUTOw7rc"
TELEGRAM_CHAT_ID = "1950722362"

# -- Automation & API Settings --
SCAN_INTERVAL_HOURS = 4  # How often to run the full market scan
API_TIMEOUT = 10         # Seconds to wait for an API response
MAX_WORKERS = 10         # Threads for parallel coin analysis

# -- Liquidity & Ranking --
MIN_VOLUME_24H_USD = 50_000_000  # $50M minimum 24h trading volume
MIN_OPEN_INTEREST_USD = 50_000_000 # $50M minimum open interest
TOP_BULLISH_COUNT = 10           # Number of top bullish coins to report
TOP_BEARISH_COUNT = 10           # Number of top bearish coins to report

# -- Technical Analysis Parameters --
TIMEFRAME = "240"        # 4-hour timeframe for analysis
KLINE_LIMIT = 201        # Number of candles to fetch (200 for EMA, +1 for current)

# EMA Periods
EMA_SHORT_PERIOD = 50
EMA_LONG_PERIOD = 200

# ATR Period for Market Regime
ATR_PERIOD = 14

# -- Market Regime Thresholds (ATR %) --
ATR_TRENDING_THRESHOLD = 2.5  # ATR % value to be considered a "Trending" market
ATR_QUIET_THRESHOLD = 1.0     # ATR % value to be considered a "Quiet / Ranging" market

# -- Trend Stage / Overextended Thresholds --
MAX_DISTANCE_FROM_EMA_PERCENT = 15.0 # Max distance from EMA(50) to be considered healthy

# Uptrend Stage Definitions (% distance from EMA50)
EARLY_STAGE_MAX_PERCENT = 5.0
MID_STAGE_MAX_PERCENT = 15.0

# -- Logging Configuration --
LOG_LEVEL = "INFO"
LOG_FILE = "market_intelligence.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'