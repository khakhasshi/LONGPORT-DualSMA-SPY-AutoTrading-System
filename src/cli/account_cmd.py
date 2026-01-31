import click
from rich.console import Console
from rich.table import Table
from src.core.trader import Trader

console = Console()

@click.group(name='account')
def account_cmd():
    """账户信息管理"""
    pass

@account_cmd.command()
def login():
    """验证 Longport API 连接"""
    try:
        trader = Trader()
        # 简单调用一个轻量级接口验证，例如获取资产
        balance = trader.get_account_balance()
        if balance:
            console.print("[bold green]Longport API 连接成功![/bold green]")
            console.print(f"账户总资产: {balance.get('total_assets')} {balance.get('currency')}")
        else:
            console.print("[yellow]连接似乎成功，但未获取到资产信息。[/yellow]")
    except Exception as e:
        console.print(f"[bold red]连接失败:[/bold red] {e}")
        console.print("请检查 .env 文件中的 API Key 配置。")

@account_cmd.command()
def info():
    """显示账户信息"""
    login() # 复用 login 的逻辑显示基本信息

@account_cmd.command()
@click.option('--currency', default='USD', help='货币币种 (默认 USD)')
def balance(currency):
    """查询账户余额"""
    try:
        trader = Trader()
        bal = trader.get_account_balance(currency)
        
        table = Table(title=f"账户资产 ({currency})")
        table.add_column("项目", style="cyan")
        table.add_column("金额", justify="right", style="bold green")
        
        table.add_row("Total Assets", f"{bal.get('total_assets', 0):,.2f}")
        table.add_row("Cash", f"{bal.get('cash', 0):,.2f}")
        table.add_row("Market Value", f"{bal.get('market_value', 0):,.2f}")
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]查询失败:[/red] {e}")

@account_cmd.command()
@click.option('--symbol', help='过滤特定标的')
def positions(symbol):
    """查询当前持仓"""
    try:
        trader = Trader()
        positions = trader.get_positions(symbol)
        
        if not positions:
            console.print("[yellow]当前无持仓[/yellow]")
            return
            
        table = Table(title="当前持仓")
        table.add_column("Symbol", style="cyan")
        table.add_column("Qty", justify="right")
        table.add_column("Cost", justify="right")
        table.add_column("Current", justify="right")
        table.add_column("Mkt Value", justify="right")
        table.add_column("Unrealized P/L", justify="right")
        
        for p in positions:
            pnl = p['profit_loss']
            color = "green" if pnl >= 0 else "red"
            
            table.add_row(
                p['symbol'],
                str(p['quantity']),
                f"{p['cost_price']:.2f}",
                f"{p['current_price']:.2f}",
                f"{p['market_value']:.2f}",
                f"[{color}]{pnl:.2f}[/{color}]"
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]查询持仓失败:[/red] {e}")
