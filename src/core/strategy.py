import pandas as pd
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime
from src.utils.logger import get_logger

@dataclass
class Signal:
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    timestamp: datetime
    price: float
    short_ma: float
    long_ma: float
    reason: str
    
    def __str__(self):
        color_map = {'BUY': 'green', 'SELL': 'red', 'HOLD': 'yellow'}
        return f"[{self.timestamp}] {self.signal_type}: {self.reason} (Price: {self.price:.2f})"

class Strategy:
    def __init__(self, short_window: int = 5, long_window: int = 20):
        self.logger = get_logger("strategy")
        self.short_window = short_window
        self.long_window = long_window

    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标 (MA)
        Args:
            data: 必须包含 'close' 列，且按时间升序排列
        Returns:
            DataFrame: 包含 MA 数据的 DataFrame
        """
        if data.empty:
            return data
            
        df = data.copy()
        # 确保按时间排序
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
            
        df[f'MA{self.short_window}'] = df['close'].rolling(window=self.short_window).mean()
        df[f'MA{self.long_window}'] = df['close'].rolling(window=self.long_window).mean()
        return df

    def check_signal(self, data: pd.DataFrame) -> Signal:
        """
        根据最新数据检查是否产生信号
        通常传入包含当天收盘数据的完整 DataFrame
        """
        if len(data) < self.long_window + 1:
             msg = f"Insufficient data: have {len(data)}, need > {self.long_window + 1}"
             self.logger.warning(msg)
             # 返回空 HOLD 信号
             last_price = data['close'].iloc[-1] if not data.empty else 0
             ts = data['timestamp'].iloc[-1] if not data.empty and 'timestamp' in data.columns else datetime.now()
             return Signal('HOLD', ts, last_price, 0, 0, msg)

        df = self.calculate_indicators(data)
        
        # 获取最后两行数据：T-1 (prev) 和 T (curr)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        short_ma_curr = curr[f'MA{self.short_window}']
        long_ma_curr = curr[f'MA{self.long_window}']
        short_ma_prev = prev[f'MA{self.short_window}']
        long_ma_prev = prev[f'MA{self.long_window}']
        
        price = curr['close']
        timestamp = curr['timestamp'] if 'timestamp' in curr else datetime.now()
        
        signal_type = 'HOLD'
        # 默认理由
        reason = f"MA{self.short_window}:{short_ma_curr:.2f}, MA{self.long_window}:{long_ma_curr:.2f}"
        
        # NaN 检查
        if pd.isna(short_ma_curr) or pd.isna(long_ma_curr) or pd.isna(short_ma_prev) or pd.isna(long_ma_prev):
             return Signal('HOLD', timestamp, price, 0, 0, "Calculating MAs (not enough warmup data)")

        # 金叉: 短线上穿长线
        if short_ma_prev < long_ma_prev and short_ma_curr >= long_ma_curr:
            signal_type = 'BUY'
            reason = f"Golden Cross: MA{self.short_window} ({short_ma_curr:.2f}) crossed above MA{self.long_window} ({long_ma_curr:.2f})"
            
        # 死叉: 短线下穿长线
        elif short_ma_prev > long_ma_prev and short_ma_curr <= long_ma_curr:
            signal_type = 'SELL'
            reason = f"Death Cross: MA{self.short_window} ({short_ma_curr:.2f}) crossed below MA{self.long_window} ({long_ma_curr:.2f})"
        
        self.logger.debug(f"Signal Check: {signal_type} at {timestamp} | {reason}")
            
        return Signal(
            signal_type=signal_type,
            timestamp=timestamp,
            price=price,
            short_ma=short_ma_curr,
            long_ma=long_ma_curr,
            reason=reason
        )

