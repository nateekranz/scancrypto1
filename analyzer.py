# ====================================
# FILE: analyzer.py (v3.1 - Final Bugfix Version)
# ====================================

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pybit.unified_trading import HTTP
from concurrent.futures import ThreadPoolExecutor, as_completed
import config

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Encapsulates all market analysis logic with a more efficient, structured approach."""

    def __init__(self):
        self.session = HTTP(testnet=False)

    def run_full_analysis(self) -> Dict:
        """Orchestrates the entire analysis pipeline."""
        macro_data = self._analyze_macro_conditions()
        market_regime = macro_data.get('market_regime', "Choppy 🟡")
        liquid_tickers = self._get_liquid_tickers(market_regime)

        if not liquid_tickers:
            logger.warning("No symbols passed liquidity filters for the current market regime.")
            return {"macro": macro_data, "micro": {"bullish": [], "bearish": []}}

        bullish, bearish = self._screen_coins(liquid_tickers, market_regime)

        return {"macro": macro_data, "micro": {"bullish": bullish, "bearish": bearish}}

    def _analyze_macro_conditions(self) -> Dict:
        """Analyzes BTC trend and market regime."""
        logger.info("Analyzing macro conditions (BTC Trend & Market Regime)...")
        btc_df = self._get_kline_as_df("BTCUSDT", limit=config.KLINE_LIMIT)
        if btc_df is None or len(btc_df) < config.EMA_LONG_PERIOD:
            return {"btc_trend": "Unknown ❓", "market_regime": "Unknown ❓"}

        btc_df['ema_short'] = btc_df['close'].ewm(span=config.EMA_SHORT_PERIOD, adjust=False).mean()
        btc_df['ema_long'] = btc_df['close'].ewm(span=config.EMA_LONG_PERIOD, adjust=False).mean()
        latest = btc_df.iloc[0]

        btc_trend = "NEUTRAL 🟡"
        if latest['close'] > latest['ema_short'] > latest['ema_long']:
            btc_trend = "BULLISH 🟢"
        elif latest['close'] < latest['ema_short'] < latest['ema_long']:
            btc_trend = "BEARISH 🔴"
        
        tr = pd.concat([
            btc_df['high'] - btc_df['low'],
            (btc_df['high'] - btc_df['close'].shift(-1)).abs(),
            (btc_df['low'] - btc_df['close'].shift(-1)).abs()
        ], axis=1).max(axis=1)
        
        atr = tr.ewm(span=config.ATR_PERIOD, adjust=False).mean().iloc[0]
        atr_percent = (atr / latest['close']) * 100 if latest['close'] > 0 else 0

        market_regime = "Choppy 🟡"
        if atr_percent > config.ATR_TRENDING_THRESHOLD:
            market_regime = "Trending ✅"
        elif atr_percent < config.ATR_QUIET_THRESHOLD:
            market_regime = "Quiet / Ranging 🔴"
        
        logger.info(f"Macro analysis complete: BTC Trend is {btc_trend}, Market Regime is {market_regime}")
        return {"btc_trend": btc_trend, "market_regime": market_regime}

    def _get_liquid_tickers(self, market_regime: str) -> List[Dict]:
        """Fetches all linear tickers and applies DYNAMIC liquidity filters."""
        min_vol, min_oi = (config.STRICT_MIN_VOLUME_24H, config.STRICT_MIN_OPEN_INTEREST) if market_regime == "Trending ✅" else (config.RELAXED_MIN_VOLUME_24H, config.RELAXED_MIN_OPEN_INTEREST)
        logger.info(f"Using {'STRICT' if market_regime == 'Trending ✅' else 'RELAXED'} liquidity filters...")

        try:
            response = self.session.get_tickers(category="linear")
            if response['retCode'] == 0:
                all_tickers = [t for t in response['result']['list'] if t['symbol'].endswith('USDT')]
                liquid_tickers = [t for t in all_tickers if float(t.get('turnover24h', 0)) >= min_vol and float(t.get('openInterestValue', 0)) >= min_oi]
                logger.info(f"Found {len(liquid_tickers)} liquid symbols out of {len(all_tickers)}.")
                return liquid_tickers
        except Exception as e:
            logger.error(f"Could not fetch or filter tickers: {e}")
        return []

    def _screen_coins(self, liquid_tickers: List[Dict], market_regime: str) -> Tuple[List[Dict], List[Dict]]:
        """Analyzes liquid tickers in parallel with a dynamic health score threshold."""
        min_health_score = config.STRICT_MIN_HEALTH_SCORE if market_regime == "Trending ✅" else config.RELAXED_MIN_HEALTH_SCORE
        logger.info(f"Using MINIMUM HEALTH SCORE of {min_health_score} for this scan.")

        bullish, bearish = [], []
        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            future_to_ticker = {executor.submit(self._analyze_single_symbol, ticker, min_health_score): ticker for ticker in liquid_tickers}
            for future in as_completed(future_to_ticker):
                result = future.result()
                if result:
                    if result['trend_type'] == 'bullish': bullish.append(result)
                    elif result['trend_type'] == 'bearish': bearish.append(result)
        
        bullish.sort(key=lambda x: x.get('health_score', 0), reverse=True)
        bearish.sort(key=lambda x: x.get('health_score', 0), reverse=True)
        
        logger.info(f"Screening complete. Found {len(bullish)} bullish and {len(bearish)} bearish candidates.")
        return bullish[:config.TOP_BULLISH_COUNT], bearish[:config.TOP_BEARISH_COUNT]

    def _analyze_single_symbol(self, ticker_data: Dict, min_health_score: int) -> Optional[Dict]:
        """Analyzes a single symbol using a scoring system with a dynamic threshold."""
        symbol = ticker_data['symbol']
        df = self._get_kline_as_df(symbol, limit=config.KLINE_LIMIT)
        if df is None or len(df) < config.EMA_LONG_PERIOD: return None

        df['ema_short'] = df['close'].ewm(span=config.EMA_SHORT_PERIOD, adjust=False).mean()
        df['ema_long'] = df['close'].ewm(span=config.EMA_LONG_PERIOD, adjust=False).mean()
        latest = df.iloc[0]
        
        if pd.isna(latest['ema_short']) or pd.isna(latest['ema_long']) or latest['ema_long'] == 0: return None

        health_score = 0
        ema_separation_percent = ((latest['ema_short'] - latest['ema_long']) / latest['ema_long']) * 100
        
        # [แก้ไข BUG] ใช้ round() แทน int() และเอา deadzone ออก
        if ema_separation_percent > 0: # Uptrend
            health_score += min(50, round(ema_separation_percent * 10)) # ให้ 10 คะแนนต่อ 1%
        else: # Downtrend
            health_score += min(50, round(abs(ema_separation_percent) * 10))

        is_uptrend_structure = ema_separation_percent > 0
        is_downtrend_structure = ema_separation_percent < 0

        if is_uptrend_structure and latest['close'] > latest['ema_short']:
            health_score += 30
        elif is_downtrend_structure and latest['close'] < latest['ema_short']:
            health_score += 30
            
        percent_diff_from_ema50 = ((latest['close'] - latest['ema_short']) / latest['ema_short']) * 100 if latest['ema_short'] > 0 else 0
        if abs(percent_diff_from_ema50) < config.MAX_DISTANCE_FROM_EMA_PERCENT:
            health_score += 20

        if health_score < min_health_score:
            return None

        ticker_data['trend_type'] = 'bullish' if is_uptrend_structure else 'bearish'
        ticker_data['health_score'] = health_score
        
        stage = "N/A"
        if is_uptrend_structure and percent_diff_from_ema50 >= 0:
            stage = "🌱 Early" if percent_diff_from_ema50 < config.EARLY_STAGE_MAX_PERCENT else "🌳 Mid"
        ticker_data['stage'] = stage
        
        return ticker_data
    
    def _get_kline_as_df(self, symbol: str, limit: int) -> Optional[pd.DataFrame]:
        """Fetches k-line data and returns a pandas DataFrame, sorted descending by time."""
        try:
            response = self.session.get_kline(category="linear", symbol=symbol, interval=config.TIMEFRAME, limit=limit)
            if response['retCode'] == 0 and response['result']['list']:
                df = pd.DataFrame(response['result']['list'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
                numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'turnover']
                df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df.sort_values('timestamp', ascending=False).reset_index(drop=True)
            else:
                logger.warning(f"Could not fetch k-line for {symbol}: {response.get('retMsg', 'Empty list')}")
        except Exception as e:
            logger.error(f"Exception fetching k-line for {symbol}: {e}")
        return None