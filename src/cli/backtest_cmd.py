import click
import plotext as plt
from rich.console import Console
from rich.table import Table
from src.core.data_fetcher import DataFetcher
from src.core.strategy import Strategy
from src.backtest.engine import Backtester

console = Console()

@click.command(name='backtest')
@click.option('--symbol', '-s', help='回测标的代码')
@click.option(
    '--days', '-d', 
    default=365*2, 
    help='回测天数 (默认 730天 / 2年)'
)
@click.option('--capital', default=100000.0, help='初始资金')
@click.option('--plot/--no-plot', default=True, help='是否显示资金曲线图')
@click.pass_context
def backtest_cmd(ctx, symbol, days, capital, plot):
    """
    运行策略回测
    
    分析指定标的在 SPY 双均线策略下的历史表现。
    """
    config = ctx.obj.get('CONFIG') or {}
    
    # 参数优先级：命令行 > 配置文件 > 默认 SPY.US
    target_symbol = symbol if symbol else config.get('symbol', 'SPY.US')
    short_window = config.get('strategy', {}).get('short_ma_period', 5)
    long_window = config.get('strategy', {}).get('long_ma_period', 20)
    
    console.print(f"[bold blue]开始回测:[/bold blue] {target_symbol}")
    console.print(f"策略参数: MA{short_window} vs MA{long_window}")
    console.print(f"时间范围: 最近 {days} 天")
    
    # 1. 获取数据
    fetcher = DataFetcher(config)
    # 为计算初始 MA，多取一点数据
    fetch_count = days + long_window + 10
    
    with console.status("[green]正在获取历史数据...[/green]"):
        df = fetcher.get_historical_klines(target_symbol, period='day', count=fetch_count)
    
    if df.empty:
        console.print("[red]获取数据失败，回测终止[/red]")
        return

    # 2. 初始化引擎并运行
    strategy = Strategy(short_window, long_window)
    engine = Backtester(strategy, initial_capital=capital)
    
    result_df = engine.run(df)
    metrics = engine.get_performance_metrics()
    
    if not metrics:
        console.print("[yellow]没有足够的数据产生交易或回测结果[/yellow]")
        return
        
    # 3. 显示结果
    # 3.1 绩效指标表
    table = Table(title=f"回测报告 ({target_symbol})")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold yellow")
    
    for k, v in metrics.items():
        table.add_row(k, str(v))
    
    console.print(table)
    
    # 3.2 绘制资金曲线
    if plot:
        console.print("\n[bold]资金曲线 vs 基准 (Buy & Hold)[/bold]")
        dates = [t.strftime('%Y-%m-%d') for t in result_df['timestamp']]
        equity = result_df['equity_curve'].tolist()
        benchmark = result_df['benchmark_curve'].tolist()
        
        plt.clear_figure()
        plt.theme('dark')
        plt.title("Equity Curve")
        plt.plot(equity, label='Strategy', color='green')
        plt.plot(benchmark, label='Benchmark', color='gray')
        plt.show()

    # 3.3 最近 5 笔交易
    trade_log = engine.get_trade_log()
    if trade_log:
        log_table = Table(title="最近 5 笔交易记录")
        log_table.add_column("Type")
        log_table.add_column("Date")
        log_table.add_column("Price")
        log_table.add_column("PnL")
        
        for t in trade_log[-5:]:
            color = "green" if t['type'] == 'BUY' else "red"
            pnl_str = f"{t['pnl_pct']:.2%}" if t['type'] == 'SELL' else "-"
            pnl_color = "green" if t['pnl'] > 0 else "red" if t['pnl'] < 0 else "white"
            
            log_table.add_row(
                f"[{color}]{t['type']}[/{color}]",
                t['date'].strftime('%Y-%m-%d'),
                f"{t['price']:.2f}",
                f"[{pnl_color}]{pnl_str}[/{pnl_color}]"
            )
        console.print(log_table)
