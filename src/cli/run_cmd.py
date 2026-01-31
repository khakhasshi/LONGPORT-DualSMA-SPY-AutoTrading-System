import click
import time
import schedule
from datetime import datetime
from rich.console import Console
from src.core.data_fetcher import DataFetcher
from src.core.strategy import Strategy, Signal
from src.core.trader import Trader
from src.core.notifier import Notifier
from src.utils.logger import get_logger

console = Console()
logger = get_logger("runner")

def run_job(ctx, mode: str):
    """
    核心任务：获取数据 -> 计算信号 -> (模拟/实盘) 交易
    """
    config = ctx.obj.get('CONFIG')
    if not config:
        logger.error("Configuration not loaded.")
        return

    symbol = config.get('symbol', 'SPY.US')
    logger.info(f"Starting job for {symbol} in [{mode}] mode...")
    
    try:
        # 1. 初始化模块
        fetcher = DataFetcher(config)
        
        strat_conf = config.get('strategy', {})
        strategy = Strategy(
            short_window=strat_conf.get('short_ma_period', 5),
            long_window=strat_conf.get('long_ma_period', 20)
        )
        
        notifier = Notifier(config)
        
        # 2. 获取数据
        # 需要足够的数据来计算 MA
        count = strategy.long_window + 10
        logger.info("Fetching market data...")
        df = fetcher.get_historical_klines(symbol, period='day', count=count)
        
        if df.empty:
            logger.error("No data fetched from market.")
            return

        # 3. 计算信号
        logger.info("Calculating signal...")
        signal = strategy.check_signal(df)
        logger.info(f"Signal Result: {signal}")
        
        # 4. 根据模式执行
        if signal.signal_type == "HOLD":
            logger.info("No trading signal. Holding...")
            return

        # 有信号 (BUY/SELL)
        notifier.notify_signal(signal) # 先发信号通知
        
        if mode == 'signal':
            logger.info("[Signal Mode] Operation complete. No trade executed.")
            return
            
        # 初始化 Trader (Paper/Live 需要)
        trader = Trader(config)
        
        # 计算交易数量
        # 这里简化逻辑：全仓买入或全部卖出，具体看 config.trading.position_ratio
        qty = 0
        
        trading_conf = config.get('trading', {})
        position_ratio = trading_conf.get('position_ratio', 1.0)
        
        if signal.signal_type == "BUY":
            # 计算买入数量
            # 获取当前现金
            balance = trader.get_account_balance()
            if not balance:
                logger.error("Failed to get account balance.")
                return
                
            cash = balance.get('cash', 0)
            target_cash = cash * position_ratio
            current_price = signal.price
            
            if current_price > 0:
                qty = int(target_cash / current_price)
                
            if qty <= 0:
                logger.warning(f"Insufficient funds to buy. Cash: {cash}, Price: {current_price}")
                return
                
        elif signal.signal_type == "SELL":
            # 计算卖出数量 (全部平仓)
            positions = trader.get_positions(symbol)
            pos = next((p for p in positions if p['symbol'] == symbol), None)
            if not pos:
                logger.warning("Signal is SELL but no position found.")
                return
            qty = pos.get('available_quantity', 0)
            
        if qty > 0:
            if mode == 'live':
                logger.info(f"[LIVE] Executing {signal.signal_type} {qty} {symbol}...")
                order_type = trading_conf.get('order_type', 'Market') # 默认市价单，可配合设计文档升级为限价
                
                # 如果是 Limit 单，需要价格，这里简单用当前信号价格 (收盘价)
                # 实际生产中可能需要获取最新 quote or order_execution 配置逻辑
                price = None
                if order_type == 'Limit':
                    price = signal.price 
                    
                order_id = trader.submit_order(symbol, signal.signal_type, qty, price, order_type)
                logger.info(f"Trade submitted. ID: {order_id}")
                notifier.notify_order(f"Executed {signal.signal_type} {qty} {symbol}. Order ID: {order_id}")
                
            elif mode == 'paper':
                logger.info(f"[PAPER] Simulated {signal.signal_type} {qty} {symbol} @ {signal.price}")
                notifier.notify_order(f"[PAPER] Simulated {signal.signal_type} {qty} {symbol}")
        else:
             logger.info("Calculated quantity is 0. No trade.")

    except Exception as e:
        logger.error(f"Job execution failed: {e}", exc_info=True)
        notifier.send("Error Alert", f"Job failed: {e}")

@click.command(name='run')
@click.option('--mode', type=click.Choice(['signal', 'paper', 'live']), default='signal', help='运行模式')
@click.option('--once', is_flag=True, help='立即运行一次并退出')
@click.pass_context
def run_cmd(ctx, mode, once):
    """运行策略主程序"""
    console.print(f"[bold green]Starting RealTrade Engine[/bold green]")
    console.print(f"Mode: [bold cyan]{mode.upper()}[/bold cyan]")
    
    if mode == 'live':
        console.print("[bold red]WARNING: You are running in LIVE mode. Real money will be used![/bold red]")
        if not once:
             # 如果是后台运行，给个倒计时确认
             console.print("Starting in 5 seconds...")
             time.sleep(5)
    
    if once:
        run_job(ctx, mode)
        return

    # 定时任务调度
    # 每天美东时间 16:05 (收盘后不久) 执行
    # 注意：服务器时区问题。这里假设运行环境本地时间正确，或者使用 UTC 转换
    # 简单起见，我们每分钟检查一次时间，或者使用 schedule 库
    
    # 模拟设定：每天 16:05 运行
    schedule_time = "16:05" 
    console.print(f"Scheduled to run daily at {schedule_time}")
    
    schedule.every().day.at(schedule_time).do(run_job, ctx=ctx, mode=mode)
    
    # 另外添加一个心跳日志
    schedule.every(1).hours.do(lambda: logger.info("Heartbeat: Engine is running..."))

    logger.info("Scheduler started.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Engine stopped.[/yellow]")
