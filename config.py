# ====================================
# FILE: config.py
# DESCRIPTION: Configuration file for Market Intelligence Bot.
# ====================================

# --- TELEGRAM CONFIGURATION ---
TELEGRAM_BOT_TOKEN = "7673207599:AAGieVWYvOl34OB0Lth8_Bsszw2fUTOw7rc"  # <-- ใส่ Token ของคุณ
TELEGRAM_CHAT_ID = "1950722362"      # <-- ใส่ Chat ID ของคุณ

# --- AUTOMATION & API SETTINGS ---
SCAN_INTERVAL_HOURS = 4   # ความถี่ในการสแกนตลาด (ชั่วโมง)
API_TIMEOUT = 15          # เวลาสูงสุดที่รอการตอบกลับจาก API (วินาที)
MAX_WORKERS = 10          # จำนวน Threads ที่ใช้ในการวิเคราะห์เหรียญพร้อมกัน

# --- DYNAMIC LIQUIDITY FILTERS ---
# ใช้เกณฑ์ที่เข้มงวดเมื่อตลาดมีเทรนด์ชัดเจน (Trending)
STRICT_MIN_VOLUME_24H = 50_000_000      # Volume ขั้นต่ำ $50M
STRICT_MIN_OPEN_INTEREST = 50_000_000   # OI ขั้นต่ำ $50M

# ใช้เกณฑ์ที่ผ่อนปรนเมื่อตลาดซบเซาหรือผันผวน (Quiet/Choppy)
RELAXED_MIN_VOLUME_24H = 25_000_000     # Volume ขั้นต่ำ $25M
RELAXED_MIN_OPEN_INTEREST = 25_000_000  # OI ขั้นต่ำ $25M

# --- RANKING & REPORTING ---
TOP_BULLISH_COUNT = 10  # จำนวนเหรียญขาขึ้นสูงสุดที่จะแสดงในรายงาน
TOP_BEARISH_COUNT = 10  # จำนวนเหรียญขาลงสูงสุดที่จะแสดงในรายงาน

# --- TECHNICAL ANALYSIS PARAMETERS ---
TIMEFRAME = "240"        # Timeframe ที่ใช้ในการวิเคราะห์ (4 ชั่วโมง)
KLINE_LIMIT = 250        # จำนวนแท่งเทียนที่ดึงมาเพื่อคำนวณ Indicator

# EMA Periods
EMA_SHORT_PERIOD = 50
EMA_LONG_PERIOD = 200

# ATR Period for Market Regime
ATR_PERIOD = 14

# --- MARKET REGIME THRESHOLDS (ATR %) ---
ATR_TRENDING_THRESHOLD = 2.5  # ค่า ATR % ขั้นต่ำที่จะถือว่าเป็น "Trending"
ATR_QUIET_THRESHOLD = 1.0     # ค่า ATR % สูงสุดที่จะถือว่าเป็น "Quiet / Ranging"

# --- TREND STAGE / OVEREXTENDED THRESHOLDS ---
MAX_DISTANCE_FROM_EMA_PERCENT = 15.0 # ระยะห่างสูงสุดจาก EMA(50) ที่จะถือว่าเทรนด์ยังดีอยู่

# Uptrend Stage Definitions (% distance from EMA50)
EARLY_STAGE_MAX_PERCENT = 5.0  # ระยะห่างสูงสุดสำหรับ "Early Stage" (0% - 5%)
MID_STAGE_MAX_PERCENT = 15.0   # ระยะห่างสูงสุดสำหรับ "Mid Stage" (5% - 15%)

# --- LOGGING CONFIGURATION ---
LOG_LEVEL = "INFO"
LOG_FILE = "market_intelligence.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'