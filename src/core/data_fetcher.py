import pandas as pd
from typing import List, Union, Dict, Any
from longport.openapi import QuoteContext, Config, Period, AdjustType
from src.utils.logger import get_logger

class DataFetcher:
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = get_logger("data_fetcher")
        
        # 初始化 Longport Config
        try:
            from src.core.lp_config import get_hardcoded_lp_config
            self.lp_config = get_hardcoded_lp_config()
            self.ctx = QuoteContext(self.lp_config)
            self.logger.debug("Longport QuoteContext initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Longport QuoteContext: {e}")
            # 这里不抛出异常，允许在没有配置的情况下实例化，但在调用方法时会报错
            self.ctx = None

    def _check_connection(self):
        if self.ctx is None:
            raise RuntimeError("Longport QuoteContext not initialized. Check your .env configuration.")

    def get_historical_klines(self, symbol: str, period: str = 'day', count: int = 30) -> pd.DataFrame:
        """
        获取历史K线数据
        
        Args:
            symbol: 股票代码 (e.g., 'SPY.US')
            period: 周期 ('day', 'week', 'month', 'year', '1m', '5m', '15m', '30m', '60m')
            count: 获取数量
            
        Returns:
            pd.DataFrame: 包含 OHLCV 数据的 DataFrame
        """
        self._check_connection()
        
        period_map = {
            'day': Period.Day,
            'week': Period.Week,
            'month': Period.Month,
            'year': Period.Year,
            '1m': Period.Min_1,
            '5m': Period.Min_5,
            '15m': Period.Min_15,
            '30m': Period.Min_30,
            '60m': Period.Min_60,
        }
        
        lp_period = period_map.get(period.lower(), Period.Day)
        
        try:
            self.logger.info(f"Fetching {count} {period} klines for {symbol}...")
            # 使用前复权 (Forward) 适合策略回测
            candlesticks = self.ctx.candlesticks(symbol, lp_period, count, adjust_type=AdjustType.ForwardAdjust)
            
            data = []
            for k in candlesticks:
                data.append({
                    "timestamp": k.timestamp, 
                    "open": float(k.open),
                    "high": float(k.high),
                    "low": float(k.low),
                    "close": float(k.close),
                    "volume": int(k.volume)
                })
            
            df = pd.DataFrame(data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                # 不设置 index，保留 timestamp 列，方便查看
            
            self.logger.debug(f"Successfully fetched {len(df)} records")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching historical klines for {symbol}: {e}")
            return pd.DataFrame()

    def get_realtime_quote(self, symbols: Union[str, List[str]]) -> Dict[str, Dict]:
        """
        获取实时行情
        
        Args:
            symbols: 单个代码字符串或代码列表
            
        Returns:
            Dict: {symbol: {price, open, high, low, ...}}
        """
        self._check_connection()
        
        if isinstance(symbols, str):
            symbols = [symbols]
            
        try:
            self.logger.info(f"Fetching realtime quote for {symbols}...")
            quotes = self.ctx.quote(symbols)
            
            result = {}
            for q in quotes:
                result[q.symbol] = {
                    "price": float(q.last_done),
                    "open": float(q.open),
                    "high": float(q.high),
                    "low": float(q.low),
                    "prev_close": float(q.prev_close),
                    "volume": int(q.volume),
                    "timestamp": q.timestamp
                }
            
            return result
        except Exception as e:
            self.logger.error(f"Error fetching realtime quote: {e}")
            return {}

