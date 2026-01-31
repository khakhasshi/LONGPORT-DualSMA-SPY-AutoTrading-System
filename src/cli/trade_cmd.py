import click
from rich.console import Console
from rich.table import Table
from src.core.trader import Trader
from src.core.data_fetcher import DataFetcher

console = Console()

@click.group(name='trade')
def trade_cmd():
    """手动交易操作"""
    pass

@trade_cmd.command()
@click.argument('symbol')
@click.option('--quantity', '-q', type=int, default=None, help='买入数量')
@click.option('--amount', '-a', type=float, default=None, help='买入金额 (估算数量)')
@click.option('--price', '-p', type=float, help='限价单价格 (不填则为市价)')
@click.option('--force', is_flag=True, help='跳过确认直接下单')
def buy(symbol, quantity, amount, price, force):
    """手动买入"""
    if not quantity and not amount:
        console.print("[red]必须指定数量 (--quantity) 或金额 (--amount)[/red]")
        return
        
    try:
        trader = Trader()
        
        # 如果是按金额买入，需要获取当前价格计算数量
        if amount and not quantity:
            fetcher = DataFetcher()
            quote = fetcher.get_realtime_quote(symbol).get(symbol)
            if not quote:
                console.print(f"[red]无法获取 {symbol} 价格，无法按金额计算数量[/red]")
                return
            current_price = price if price else quote['price']
            quantity = int(amount / current_price)
            if quantity <= 0:
                console.print(f"[red]金额太小，不足以买入 1 股 (价格: {current_price})[/red]")
                return
            console.print(f"[dim]按价格 {current_price} 计算，金额 {amount} 将买入 {quantity} 股[/dim]")

        order_type = "Limit" if price else "Market"
        price_str = f" @ {price}" if price else " @ Market"
        
        info_str = f"[bold green]BUY {quantity} {symbol}{price_str}[/bold green]"
        console.print(f"准备提交订单: {info_str}")
        
        if not force:
            if not click.confirm("确认下单?"):
                console.print("取消操作")
                return
        
        order_id = trader.submit_order(symbol, "Buy", quantity, price, order_type)
        console.print(f"[green]下单成功! Order ID: {order_id}[/green]")
        
    except Exception as e:
        console.print(f"[bold red]下单失败:[/bold red] {e}")

@trade_cmd.command()
@click.argument('symbol')
@click.option('--quantity', '-q', type=int, help='卖出数量 (不填则卖出全部)')
@click.option('--price', '-p', type=float, help='限价单价格')
@click.option('--all', 'sell_all', is_flag=True, help='卖出全部持仓')
@click.option('--force', is_flag=True, help='跳过确认直接下单')
def sell(symbol, quantity, price, sell_all, force):
    """手动卖出"""
    try:
        trader = Trader()
        
        # 获取当前持仓以确定数量
        if not quantity or sell_all:
            positions = trader.get_positions(symbol)
            # 找到对应的持仓
            pos = next((p for p in positions if p['symbol'] == symbol), None)
            if not pos:
                console.print(f"[red]当前没有 {symbol} 的持仓，无法卖出[/red]")
                return
            
            available = pos['available_quantity'] # 使用可用数量
            
            if sell_all:
                quantity = available
            elif not quantity:
                 console.print(f"[yellow]未指定数量。当前可用持仓: {available}[/yellow]")
                 console.print("请使用 --quantity 指定数量 或 --all 卖出全部")
                 return
                 
            if quantity > available:
                console.print(f"[red]数量 {quantity} 超过可用持仓 {available}[/red]")
                return

        order_type = "Limit" if price else "Market"
        price_str = f" @ {price}" if price else " @ Market"
        
        info_str = f"[bold red]SELL {quantity} {symbol}{price_str}[/bold red]"
        console.print(f"准备提交订单: {info_str}")
        
        if not force:
            if not click.confirm("确认下单?"):
                console.print("取消操作")
                return
                
        order_id = trader.submit_order(symbol, "Sell", quantity, price, order_type)
        console.print(f"[green]下单成功! Order ID: {order_id}[/green]")

    except Exception as e:
        console.print(f"[bold red]下单失败:[/bold red] {e}")

@trade_cmd.command()
@click.argument('order_id')
def cancel(order_id):
    """撤销订单"""
    try:
        trader = Trader()
        trader.cancel_order(order_id)
        console.print(f"[green]已发送撤单请求: {order_id}[/green]")
    except Exception as e:
        console.print(f"[red]撤单失败:[/red] {e}")

@trade_cmd.command()
def orders():
    """查看今日订单列表"""
    try:
        trader = Trader()
        orders = trader.get_orders()
        
        if not orders:
            console.print("[yellow]今日无订单[/yellow]")
            return
            
        table = Table(title="今日订单")
        table.add_column("ID", style="dim")
        table.add_column("Symbol", style="cyan")
        table.add_column("Side")
        table.add_column("Type")
        table.add_column("Status")
        table.add_column("Qty/Filled")
        table.add_column("Price")
        
        for o in orders:
            side_color = "green" if o.side == "Buy" else "red"
            status_color = "green" if o.status == "Filled" else "yellow"
            
            table.add_row(
                o.order_id,
                o.symbol,
                f"[{side_color}]{o.side}[/{side_color}]",
                str(o.order_type),
                f"[{status_color}]{o.status}[/{status_color}]",
                f"{o.quantity}/{o.executed_quantity}",
                str(o.price) if o.price else "MKT"
            )
        
        console.print(table)
            
    except Exception as e:
        console.print(f"[red]查询订单失败:[/red] {e}")
