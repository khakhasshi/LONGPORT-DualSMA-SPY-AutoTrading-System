from typing import Dict, Any
from src.utils.logger import get_logger

class Notifier:
    """
    简化版通知模块：仅记录日志，不发送实际通知
    """
    def __init__(self, config: Dict[str, Any] = None):
        self.logger = get_logger("notifier")
        self.config = config or {}
        
    def send(self, subject: str, message: str):
        """记录通知内容到日志"""
        self.logger.info(f"[NOTIFICATION] Subject: {subject} | Message: {message}")

    def notify_signal(self, signal):
        """记录信号通知"""
        self.logger.info(f"[NOTIFICATION] Signal Triggered: {signal.signal_type} @ {signal.price} ({signal.reason})")

    def notify_order(self, order_info: str):
        """记录订单通知"""
        self.logger.info(f"[NOTIFICATION] Order Executed: {order_info}")


