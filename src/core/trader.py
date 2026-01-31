from typing import List, Dict, Optional, Any
from decimal import Decimal
from longport.openapi import TradeContext, Config, OrderSide, OrderType, TimeInForceType, OrderStatus
from src.utils.logger import get_logger

class Trader:
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = get_logger("trader")
        self.config = config or {}
        
        # 从硬编码文件加载配置
        try:
            from src.core.lp_config import get_hardcoded_lp_config
            lp_config = get_hardcoded_lp_config()
            self.ctx = TradeContext(lp_config)
            self.logger.debug("Longport TradeContext initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize TradeContext: {e}")
            self.ctx = None

    def _check_connection(self):
        if self.ctx is None:
            raise RuntimeError("TradeContext not initialized. Check your .env configuration.")

    def get_account_balance(self, currency: str = "USD") -> Dict[str, float]:
        """
        获取账户余额信息
        """
        self._check_connection()
        try:
            # SDK 3.x 变更为 account_balance
            balances = self.ctx.account_balance()
            if not balances:
                return {}
            
            # 简单起见取第一个，实际可能需要根据 currency 筛选
            # 注意: SDK返回的结构可能较复杂，这里做简化映射
            bal = balances[0]
            
            return {
                "total_assets": float(bal.net_assets),
                "cash": float(bal.total_cash),
                # 均值为估算
                "market_value": float(bal.net_assets) - float(bal.total_cash),
                "currency": bal.currency
            }
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}")
            raise

    def get_positions(self, symbol: str = None) -> List[Dict[str, Any]]:
        """
        获取持仓列表
        """
        self._check_connection()
        try:
            # SDK 3.x 返回 StockPositionsResponse -> channels -> positions
            resp = self.ctx.stock_positions(symbol if symbol else [])
            result = []
            
            # 处理新版 SDK 结构
            channels = getattr(resp, 'channels', [])
            for channel in channels:
                for p in channel.positions:
                    result.append({
                        "symbol": p.symbol,
                        "quantity": int(p.quantity),
                        "available_quantity": int(p.available_quantity),
                        "cost_price": float(p.cost_price),
                        # 以下字段若 SDK 对象中不存在则给默认值 (新版 SDK Position 对象可能不包含实时市值)
                        "current_price": float(getattr(p, 'last_done', 0.0)),
                        "market_value": float(getattr(p, 'market_value', 0.0)),
                        "profit_loss": float(getattr(p, 'unrealized_pnl', 0.0))
                    })
            return result
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            raise

    def submit_order(self, symbol: str, side: str, quantity: int, price: float = None, order_type: str = "Market") -> str:
        """
        提交订单
        
        Args:
            symbol: 代码
            side: 'Buy' or 'Sell'
            quantity: 数量
            price: 价格 (Limit单必填)
            order_type: 'Market' or 'Limit'
            
        Returns:
            order_id (str)
        """
        self._check_connection()
        
        # 转换枚举
        side_enum = OrderSide.Buy if side.lower() == 'buy' else OrderSide.Sell
        # SDK 3.x: OrderType.LO (Limit), OrderType.MO (Market)
        type_enum = OrderType.LO if order_type.lower() == 'limit' else OrderType.MO
        
        if type_enum == OrderType.LO and price is None:
            raise ValueError("Price must be provided for Limit orders")

        try:
            self.logger.info(f"Submitting order: {side} {quantity} {symbol} @ {order_type} {price if price else ''}")
            
            order_id = self.ctx.submit_order(
                symbol=symbol,
                order_type=type_enum,
                side=side_enum,
                submitted_quantity=quantity,
                submitted_price=Decimal(str(price)) if price else None,
                time_in_force=TimeInForceType.Day
            )
            self.logger.info(f"Order submitted successfully. ID: {order_id}")
            return order_id
        except Exception as e:
            self.logger.error(f"Error submitting order: {e}")
            raise

    def cancel_order(self, order_id: str):
        """撤单"""
        self._check_connection()
        try:
            self.ctx.cancel_order(order_id)
            self.logger.info(f"Order cancelled: {order_id}")
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            raise

    def get_orders(self, symbol: str = None, status: List[str] = None):
        """
        查询订单 (仅示意，SDK可能有 list_orders 或 history_orders 接口)
        不同的 Longport SDK 版本对订单查询的支持不同，通常是 history_orders 或 today_orders
        """
        self._check_connection()
        try:
            # 假设使用 today_orders
            orders = self.ctx.today_orders(symbol if symbol else [])
            return orders
        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return []

