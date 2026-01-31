import click
from rich.console import Console
from src.core.notifier import Notifier

console = Console()

@click.group(name='notify')
def notify_cmd():
    """通知系统管理 (仅日志记录)"""
    pass

@notify_cmd.command()
@click.pass_context
def test(ctx):
    """发送测试通知 (写入日志)"""
    config = ctx.obj.get('CONFIG')
    try:
        notifier = Notifier(config)
        console.print("正在写入测试日志...")
        notifier.send("Test Notification", "This is a test message from RealTrade CLI.")
        console.print("[green]日志已记录。[/green]")
        
    except Exception as e:
        console.print(f"[red]测试失败:[/red] {e}")

@notify_cmd.command()
def status():
    """查看通知状态"""
    console.print("通知模块已简化为仅日志记录模式。")
