import click
import plotext as plt
from rich.console import Console
from rich.table import Table
from src.core.data_fetcher import DataFetcher
from src.core.strategy import Strategy

console = Console()

def get_strategy_context(ctx):
    """Helper to initialize Strategy and DataFetcher from config"""
    config = ctx.obj.get('CONFIG')
    if not config:
        console.print("[red]配置未加载，无法执行策略命令。请确保 config.yaml 存在且有效。[/red]")
        return None, None, None

    symbol = config.get('symbol', 'SPY.US')
    short_window = config.get('strategy', {}).get('short_ma_period', 5)
    long_window = config.get('strategy', {}).get('long_ma_period', 20)
    
    fetcher = DataFetcher(config)
    strategy = Strategy(short_window, long_window)
    
    return symbol, fetcher, strategy

def _show_strategy_status(ctx):
    """Refactored logic to show strategy status, used by group default and command"""
    symbol, fetcher, strategy = get_strategy_context(ctx)
    if not symbol: return

    # 需要足够的数据来计算长周期 MA，并对比前一天数据
    count = strategy.long_window + 10 
    
    try:
        with console.status(f"[bold green]正在获取 {symbol} 数据...[/bold green]"):
            df = fetcher.get_historical_klines(symbol, period='day', count=count)
            
        if df.empty:
            console.print(f"[red]无数据返回: {symbol}[/red]")
            return
            
        signal = strategy.check_signal(df)
        
        table = Table(title=f"策略状态: {symbol}")
        table.add_column("指标", style="cyan")
        table.add_column("数值", style="yellow")
        
        ts_str = str(signal.timestamp)
        table.add_row("Symbol", symbol)
        table.add_row("Time", ts_str)
        table.add_row("Price", f"{signal.price:.2f}")
        table.add_row(f"MA{strategy.short_window}", f"{signal.short_ma:.2f}")
        table.add_row(f"MA{strategy.long_window}", f"{signal.long_ma:.2f}")
        
        # 信号颜色
        sig_color = "green" if signal.signal_type == "BUY" else "red" if signal.signal_type == "SELL" else "white"
        table.add_row("Signal", f"[{sig_color} bold]{signal.signal_type}[/{sig_color} bold]")
        table.add_row("Reason", signal.reason)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]执行出错:[/bold red] {e}")

@click.group(name='strategy', invoke_without_command=True)
@click.option('--symbol', '-s', help='Override symbol for the strategy check')
@click.pass_context
def strategy_cmd(ctx, symbol):
    """策略状态与信号"""
    if symbol:
        if 'CONFIG' not in ctx.obj or ctx.obj['CONFIG'] is None:
             ctx.obj['CONFIG'] = {}
        ctx.obj['CONFIG']['symbol'] = symbol
    
    if ctx.invoked_subcommand is None:
        _show_strategy_status(ctx)

@strategy_cmd.command()
@click.pass_context
def status(ctx):
    """查看当前策略状态"""
    _show_strategy_status(ctx)

@strategy_cmd.command()
@click.pass_context
def signal(ctx):
    """计算并显示当前信号"""
    symbol, fetcher, strategy = get_strategy_context(ctx)
    if not symbol: return
    
    count = strategy.long_window + 5
    try:
        df = fetcher.get_historical_klines(symbol, period='day', count=count)
        if not df.empty:
            sig = strategy.check_signal(df)
            color = "green" if sig.signal_type == "BUY" else "red" if sig.signal_type == "SELL" else "dim"
            console.print(f"[{color}]{sig.signal_type}[/{color}]: {sig.reason}")
        else:
            console.print("[red]无法获取数据[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")

@strategy_cmd.command()
@click.option('--days', default=60, help='显示最近多少天的数据')
@click.pass_context
def chart(ctx, days):
    """终端显示均线图表"""
    symbol, fetcher, strategy = get_strategy_context(ctx)
    if not symbol: return
    
    # 确保获取足够的数据来计算初始的 MA
    count = days + strategy.long_window
    
    try:
        with console.status(f"[bold green]正在获取数据并绘制图表...[/bold green]"):
            df = fetcher.get_historical_klines(symbol, period='day', count=count)
        
        if df.empty:
            console.print("[red]无数据[/red]")
            return
            
        # 计算指标
        df_indicators = strategy.calculate_indicators(df)
        
        # 截取只需显示的最近 days 天
        df_plot = df_indicators.iloc[-days:]
        
        if df_plot.empty:
             console.print("[yellow]数据不足以显示图表[/yellow]")
             return
        
        # 准备绘图数据
        dates = [t.strftime('%Y-%m-%d') for t in df_plot['timestamp']]
        prices = df_plot['close'].tolist()
        ma_short = df_plot[f'MA{strategy.short_window}'].tolist()
        ma_long = df_plot[f'MA{strategy.long_window}'].tolist()
        
        # Plotext 配置
        plt.clear_figure()
        # 由于终端宽度限制，日期可能太密集，plotext 会自动处理
        
        plt.plot(prices, label='Price', color='default')
        plt.plot(ma_short, label=f'MA{strategy.short_window}', color='yellow')
        plt.plot(ma_long, label=f'MA{strategy.long_window}', color='magenta')
        
        plt.title(f"{symbol} Daily Chart ({days} days)")
        plt.xlabel("Days")
        plt.ylabel("Price")
        plt.theme('dark')
        plt.show()
        
        # 打印末尾的日期范围作为参考
        console.print(f"[dim]Range: {dates[0]} ~ {dates[-1]}[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]绘图错误:[/bold red] {e}")
