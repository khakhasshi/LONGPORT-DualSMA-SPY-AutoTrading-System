import click
from rich.console import Console
from rich.table import Table
from src.core.data_fetcher import DataFetcher

console = Console()

@click.group(name='quote')
def quote_cmd():
    """行情数据查询"""
    pass

@quote_cmd.command()
@click.argument('symbols', nargs=-1)
def price(symbols):
    """获取实时价格 (支持多个: SPY.US AAPL.US)"""
    if not symbols:
        console.print("[yellow]请提供至少一个标的代码 (例如: SPY.US)[/yellow]")
        return

    try:
        fetcher = DataFetcher()
        data = fetcher.get_realtime_quote(list(symbols))
        
        if not data:
            console.print("[red]获取数据失败或无数据返回。请检查网络或 API Key。[/red]")
            return

        table = Table(title="实时行情")
        table.add_column("Symbol", style="cyan")
        table.add_column("Price", style="bold")
        table.add_column("Change", justify="right")
        table.add_column("High", justify="right")
        table.add_column("Low", justify="right")
        table.add_column("Prev Close", justify="right")
        table.add_column("Vol", justify="right")

        for symbol, quote in data.items():
            price = quote['price']
            prev_close = quote['prev_close']
            
            # 避免除以零
            if prev_close > 0:
                change = price - prev_close
                change_pct = (change / prev_close) * 100
                color = "green" if change >= 0 else "red"
                change_str = f"[{color}]{change:+.2f} ({change_pct:+.2f}%)[/{color}]"
            else:
                change_str = "-"
            
            table.add_row(
                symbol,
                f"{price:.2f}",
                change_str,
                f"{quote['high']:.2f}",
                f"{quote['low']:.2f}",
                f"{prev_close:.2f}",
                f"{quote['volume']:,}"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[bold red]发生错误:[/bold red] {e}")

@quote_cmd.command()
@click.argument('symbol')
@click.option('--period', '-p', default='day', help='K线周期 (day, week, 5m, 60m...)')
@click.option('--count', '-n', default=10, help='获取数量')
def kline(symbol, period, count):
    """获取K线数据"""
    try:
        fetcher = DataFetcher()
        df = fetcher.get_historical_klines(symbol, period, count)
        
        if df.empty:
            console.print(f"[red]获取 {symbol} K线数据失败或数据为空[/red]")
            return

        table = Table(title=f"{symbol} 历史K线 ({period})")
        table.add_column("Time", style="dim")
        table.add_column("Open", justify="right")
        table.add_column("High", justify="right")
        table.add_column("Low", justify="right")
        table.add_column("Close", justify="right")
        table.add_column("Volume", justify="right")

        for _, row in df.iterrows():
            # 简单的涨跌颜色：收盘 >= 开盘 为绿，否则红
            color = "green" if row['close'] >= row['open'] else "red"
            
            table.add_row(
                str(row['timestamp']),
                f"{row['open']:.2f}",
                f"{row['high']:.2f}",
                f"{row['low']:.2f}",
                f"[{color}]{row['close']:.2f}[/{color}]",
                f"{row['volume']:,}"
            )

        console.print(table)
    
    except Exception as e:
        console.print(f"[bold red]发生错误:[/bold red] {e}")
