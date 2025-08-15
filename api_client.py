# api_client.py
import logging
import pandas as pd
from typing import Optional, List, Dict
from pybit.unified_trading import HTTP
import config

logger = logging.getLogger(__name__)
session = HTTP(testnet=False) # สร้าง session ที่นี่ที่เดียว

def get_all_tickers() -> List[Dict]:
    """Fetches all linear USDT tickers from Bybit."""
    try:
        response = session.get_tickers(category="linear")
        if response.get('retCode') == 0:
            return [t for t in response['result']['list'] if t['symbol'].endswith('USDT')]
    except Exception as e:
        logger.error(f"Failed to fetch all tickers: {e}")
    return []

def get_kline_as_df(symbol: str) -> Optional[pd.DataFrame]:
    """Fetches kline data and returns a clean, sorted pandas DataFrame."""
    try:
        response = session.get_kline(
            category="linear", 
            symbol=symbol, 
            interval=config.TIMEFRAME, 
            limit=250
        )
        if response.get('retCode') != 0: return None
        
        klines = response['result']['list']
        if not klines or len(klines) < config.EMA_SLOW: return None
        
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        for col in df.columns:
            if col != 'timestamp':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df.dropna(inplace=True)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df.sort_values('timestamp', ascending=True).reset_index(drop=True)
    except Exception as e:
        logger.debug(f"Could not fetch kline for {symbol}: {e}")
        return None