import pandas as pd
import numpy as np
from typing import Dict, List, Any
from src.core.strategy import Strategy

class Backtester:
    def __init__(self, strategy: Strategy, initial_capital: float = 100000.0, commission_rate: float = 0.001):
        """
        Args:
            commission_rate: 交易费率 (e.g., 0.001 = 0.1%)
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.results = None

    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        运行回测
        """
        if data.empty:
            return pd.DataFrame()

        # 1. 计算指标
        df = self.strategy.calculate_indicators(data).copy()
        
        # 2. 生成信号 (1: 持仓/买入, 0: 空仓/卖出)
        # 策略: 短均线 > 长均线 -> 持有 (1)
        #       短均线 <= 长均线 -> 空仓 (0)
        short_ma_col = f'MA{self.strategy.short_window}'
        long_ma_col = f'MA{self.strategy.long_window}'
        
        # 避免 NaN 导致的问题 (前几个周期没有 MA)
        df = df.dropna(subset=[short_ma_col, long_ma_col])
        
        # 当天的信号决定次日的持仓 (假设收盘后产生信号，次日开盘执行，或者收盘即成交)
        # 这里简化假设：信号产生即代表此时刻持有状态。
        # 实际上收益计算通常是：今天持仓 * 今天的涨跌幅
        
        # 生成持仓状态信号: 1 代表多头，0 代表空仓
        df['position_signal'] = np.where(df[short_ma_col] > df[long_ma_col], 1, 0)
        
        # 实际持仓 (Position) 需要滞后一期，因为今天的信号只能指导明天
        # 如果是收盘交易，则今天的涨跌幅由昨天的持仓决定
        df['position'] = df['position_signal'].shift(1).fillna(0)
        
        # 3. 计算收益
        df['pct_change'] = df['close'].pct_change().fillna(0)
        df['strategy_return'] = df['position'] * df['pct_change']
        
        # 4. 考虑交易成本
        # 交易动作: position 发生变化
        df['trade_action'] = df['position'].diff().abs().fillna(0)
        # 扣除费率 (假设双边收费)
        df['strategy_return'] = df['strategy_return'] - (df['trade_action'] * self.commission_rate)
        
        # 5. 资金曲线
        df['equity_curve'] = (1 + df['strategy_return']).cumprod() * self.initial_capital
        df['benchmark_curve'] = (1 + df['pct_change']).cumprod() * self.initial_capital
        
        self.results = df
        return df

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        计算回测绩效指标
        """
        if self.results is None or self.results.empty:
            return {}
            
        df = self.results
        
        # 总收益率
        total_return = (df['equity_curve'].iloc[-1] / self.initial_capital) - 1
        benchmark_return = (df['benchmark_curve'].iloc[-1] / self.initial_capital) - 1
        
        # 交易天数
        days = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).days
        years = days / 365.25 if days > 0 else 0
        
        # 年化收益 (CAGR)
        if years > 0:
            cagr = (df['equity_curve'].iloc[-1] / self.initial_capital) ** (1 / years) - 1
        else:
            cagr = 0
            
        # 最大回撤 (Max Drawdown)
        rolling_max = df['equity_curve'].cummax()
        drawdown = (df['equity_curve'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # 夏普比率 (Sharpe Ratio) - 假设无风险利率为 0
        daily_returns = df['strategy_return']
        if daily_returns.std() != 0:
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
            
        # 交易次数
        total_trades = df['trade_action'].sum()
        
        return {
            "Start Date": df['timestamp'].iloc[0].strftime('%Y-%m-%d'),
            "End Date": df['timestamp'].iloc[-1].strftime('%Y-%m-%d'),
            "Duration (Days)": days,
            "Initial Capital": self.initial_capital,
            "Final Equity": df['equity_curve'].iloc[-1],
            "Total Return": f"{total_return:.2%}",
            "Benchmark Return": f"{benchmark_return:.2%}",
            "CAGR": f"{cagr:.2%}",
            "Max Drawdown": f"{max_drawdown:.2%}",
            "Sharpe Ratio": f"{sharpe_ratio:.2f}",
            "Total Trades": int(total_trades)
        }

    def get_trade_log(self) -> List[Dict]:
        """
        生成详细的交易记录
        """
        if self.results is None:
            return []
            
        trades = []
        in_position = False
        entry_price = 0
        entry_date = None
        
        # position 表示在该日期的“持仓状态”
        # 当 position 从 0 变 1 -> 实际上是在前一日收盘或当日开盘买入
        # 为了简化日志展示，我们认为：
        # signal 变 1 的那天 Close 买入
        # signal 变 0 的那天 Close 卖出
        
        # 重新遍历 signal 可能会更直观
        # position_signal 是基于当日 MA 计算出来的
        df = self.results
        
        for index, row in df.iterrows():
            current_signal = row['position_signal']
            price = row['close']
            date = row['timestamp']
            
            if current_signal == 1 and not in_position:
                # Buy
                in_position = True
                entry_price = price
                entry_date = date
                trades.append({
                    "type": "BUY",
                    "date": date,
                    "price": price,
                    "pnl": 0.0,
                    "pnl_pct": 0.0
                })
            
            elif current_signal == 0 and in_position:
                # Sell
                in_position = False
                pnl = price - entry_price
                pnl_pct = (price - entry_price) / entry_price
                trades.append({
                    "type": "SELL",
                    "date": date,
                    "price": price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct
                })
                
        return trades
