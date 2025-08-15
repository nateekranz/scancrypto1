# ====================================
# FILE: analyzer.py
# DESCRIPTION: Core analysis engine for macro and micro market conditions.
# ====================================

import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pybit.unified_trading import HTTP
from concurrent.futures import ThreadPoolExecutor, as_completed
import config

logger = logging.getLogger(__name__)

class MarketAnalyzer:
    """Encapsulates all market analysis logic."""

    def __init__(self):
        self.session = HTTP(testnet=False)

    def _get_kline_as_df(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetches k-line data and returns it as a pandas DataFrame."""
        try:
            response = self.session.get_kline(
                category="linear",
                symbol=symbol,
                interval=config.TIMEFRAME,
                limit=config.KLINE_LIMIT
            )
            if response['retCode'] == 0 and response['result']['list']:
                df = pd.DataFrame(response['result']['list'],
                                  columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
                
                # Convert to numeric, sort by timestamp descending
                for col in df.columns:
                    if col != 'timestamp':
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df = df.sort_values('timestamp', ascending=False).reset_index(drop=True)
                return df
            else:
                logger.warning(f"Could not fetch k-line data for {symbol}: {response.get('retMsg', 'Empty list')}")
                return None
        except Exception as e:
            logger.error(f"Exception fetching k-line for {symbol}: {e}")
            return None

    def analyze_macro_conditions(self) -> Dict:
        """Analyzes BTC trend and market regime to determine overall market state."""
        logger.info("Analyzing macro conditions (BTC Trend & Market Regime)...")
        btc_df = self._get_kline_as_df("BTCUSDT")
        if btc_df is None or len(btc_df) < config.EMA_LONG_PERIOD:
            return {"btc_trend": "Unknown ❓", "market_regime": "Unknown ❓"}

        # --- BTC Trend Analysis (EMA Alignment) ---
        btc_df['ema_short'] = btc_df['close'].ewm(span=config.EMA_SHORT_PERIOD, adjust=False).mean()
        btc_df['ema_long'] = btc_df['close'].ewm(span=config.EMA_LONG_PERIOD, adjust=False).mean()
        latest = btc_df.iloc[0]

        btc_trend = "NEUTRAL 🟡"
        if latest['close'] > latest['ema_short'] > latest['ema_long']:
            btc_trend = "BULLISH 🟢"
        elif latest['close'] < latest['ema_short'] < latest['ema_long']:
            btc_trend = "BEARISH 🔴"
        
        # --- Market Regime Analysis (ATR) ---
        high_low = btc_df['high'] - btc_df['low']
        high_close = (btc_df['high'] - btc_df['close'].shift(-1)).abs()
        low_close = (btc_df['low'] - btc_df['close'].shift(-1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.ewm(span=config.ATR_PERIOD, adjust=False).mean().iloc[0]
        atr_percent = (atr / latest['close']) * 100

        market_regime = "Choppy 🟡"
        if atr_percent > config.ATR_TRENDING_THRESHOLD: market_regime = "Trending ✅"
        elif atr_percent < config.ATR_QUIET_THRESHOLD: market_regime = "Quiet / Ranging 🔴"

        return {"btc_trend": btc_trend, "market_regime": market_regime}

    def _get_liquid_tickers(self) -> List[Dict]:
        """Fetches all linear tickers and filters for high liquidity."""
        logger.info("Fetching all tickers to filter for liquidity...")
        try:
            response = self.session.get_tickers(category="linear")
            if response['retCode'] == 0:
                all_tickers = [t for t in response['result']['list'] if t['symbol'].endswith('USDT')]
                liquid_tickers = [
                    t for t in all_tickers if
                    float(t.get('turnover24h', 0)) >= config.MIN_VOLUME_24H_USD and
                    float(t.get('openInterestValue', 0)) >= config.MIN_OPEN_INTEREST_USD
                ]
                logger.info(f"Found {len(liquid_tickers)} liquid symbols out of {len(all_tickers)}.")
                return liquid_tickers
        except Exception as e:
            logger.error(f"Could not fetch or filter tickers: {e}")
        return []

    def _analyze_single_symbol(self, ticker_data: Dict) -> Optional[Dict]:
        """Analyzes a single symbol based on trend structure and stage."""
        symbol = ticker_data['symbol']
        df = self._get_kline_as_df(symbol)
        if df is None or len(df) < config.EMA_LONG_PERIOD: return None

        df['ema_short'] = df['close'].ewm(span=config.EMA_SHORT_PERIOD, adjust=False).mean()
        df['ema_long'] = df['close'].ewm(span=config.EMA_LONG_PERIOD, adjust=False).mean()
        latest = df.iloc[0]
        
        # Ensure EMA values are valid
        if pd.isna(latest['ema_short']) or pd.isna(latest['ema_long']) or latest['ema_short'] == 0:
            return None

        # Condition A: Trend Structure
        is_uptrend_structure = latest['ema_short'] > latest['ema_long']
        is_downtrend_structure = latest['ema_short'] < latest['ema_long']
        if not (is_uptrend_structure or is_downtrend_structure): return None

        # Condition B: Not Overextended
        percent_diff = ((latest['close'] - latest['ema_short']) / latest['ema_short']) * 100
        if abs(percent_diff) >= config.MAX_DISTANCE_FROM_EMA_PERCENT: return None

        # Categorize Stage (Uptrend Only)
        stage = "N/A"
        if is_uptrend_structure and percent_diff > 0:
            if percent_diff < config.EARLY_STAGE_MAX_PERCENT:
                stage = "🌱 Early"
            elif percent_diff < config.MID_STAGE_MAX_PERCENT:
                stage = "🌳 Mid"
            else: # Should be caught by MAX_DISTANCE check, but as a fallback.
                return None 

        ticker_data['trend_type'] = 'bullish' if is_uptrend_structure else 'bearish'
        ticker_data['stage'] = stage
        return ticker_data

    def analyze_micro_conditions(self) -> Dict:
        """Finds and ranks the best trading candidates."""
        liquid_tickers = self._get_liquid_tickers()
        if not liquid_tickers:
            return {"bullish": [], "bearish": [], "recommendation": "Could not fetch liquid tickers."}

        logger.info(f"Analyzing {len(liquid_tickers)} liquid symbols with {config.MAX_WORKERS} workers...")
        bullish, bearish = [], []

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            future_to_ticker = {executor.submit(self._analyze_single_symbol, ticker): ticker for ticker in liquid_tickers}
            for future in as_completed(future_to_ticker):
                result = future.result()
                if result:
                    if result['trend_type'] == 'bullish': bullish.append(result)
                    elif result['trend_type'] == 'bearish': bearish.append(result)
        
        # Rank by 24h price change
        bullish.sort(key=lambda x: float(x.get('price24hPcnt', 0)), reverse=True)
        bearish.sort(key=lambda x: float(x.get('price24hPcnt', 0)))

        # Generate Recommendation
        macro_state = self.analyze_macro_conditions()
        if "BULLISH" in macro_state['btc_trend'] and "Trending" in macro_state['market_regime']:
            recommendation = "Market conditions are favorable. Prioritize Early Stage 🌱 candidates."
        elif "BEARISH" in macro_state['btc_trend']:
            recommendation = "Market shows bearish bias. Consider short opportunities or wait for clearer signals."
        else:
            recommendation = "Mixed signals detected. Exercise extreme caution and wait for a clearer market direction."

        logger.info(f"Screening complete. Found {len(bullish)} bullish and {len(bearish)} bearish candidates.")
        return {
            "bullish": bullish[:config.TOP_BULLISH_COUNT],
            "bearish": bearish[:config.TOP_BEARISH_COUNT],
            "recommendation": recommendation
        }