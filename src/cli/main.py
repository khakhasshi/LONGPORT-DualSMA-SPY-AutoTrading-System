import click
import sys
import os
import subprocess
import shlex

# 将项目根目录添加到 sys.path 以解决模块导入问题
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from rich.console import Console
from src.utils.config_loader import load_config
from src.utils.logger import setup_logger

# 导入所有子命令
from src.cli.config_cmd import config_cmd
from src.cli.account_cmd import account_cmd
from src.cli.quote_cmd import quote_cmd
from src.cli.strategy_cmd import strategy_cmd
from src.cli.trade_cmd import trade_cmd
from src.cli.backtest_cmd import backtest_cmd
from src.cli.run_cmd import run_cmd
from src.cli.logs_cmd import logs_cmd
from src.cli.notify_cmd import notify_cmd

console = Console()

@click.group(invoke_without_command=True)
@click.option('--config', '-c', default='./config/config.yaml', help='指定配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='启用详细输出模式')
@click.version_option()
@click.pass_context
def cli(ctx, config, verbose):
    """SPY 双均线交易策略 CLI 工具"""
    ctx.ensure_object(dict)
    ctx.obj['CONFIG_PATH'] = config
    ctx.obj['VERBOSE'] = verbose
    
    # 初始化日志
    log_level = "DEBUG" if verbose else "INFO"
    try:
        setup_logger(level=log_level)
    except Exception as e:
        console.print(f"[bold red]日志初始化失败:[/bold red] {e}")
        sys.exit(1)
        
    # 尝试加载配置
    try:
        cfg = load_config(config)
        ctx.obj['CONFIG'] = cfg
        if verbose:
            console.print(f"[bold blue]成功加载配置文件:[/bold blue] {config}")
    except Exception as e:
        if verbose:
            console.print(f"[yellow]配置文件加载警告:[/yellow] {e}")
        ctx.obj['CONFIG'] = None
    
    # 如果没有子命令，自动进入 Shell
    if ctx.invoked_subcommand is None:
        ctx.invoke(shell)

@click.command()
@click.pass_context
def shell(ctx):
    """进入交互式 Shell 模式"""
    # 尝试使用 prompt_toolkit 以获得更好的历史记录支持
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        
        history_file = os.path.expanduser('~/.dualsma_spy_history')
        # 仅仅为了创建文件
        if not os.path.exists(history_file):
            open(history_file, 'a').close()
            
        session = PromptSession(history=FileHistory(history_file))
        get_input = lambda: session.prompt('DualSMA-SPY> ')
    except ImportError:
        get_input = lambda: input('DualSMA-SPY> ')
        
    console.print("[bold green]已进入交互模式 (输入 exit 退出, help 查看命令)...[/bold green]")
    
    while True:
        try:
            cmd_text = get_input()
        except (EOFError, KeyboardInterrupt):
            console.print("再见!")
            break
            
        cmd_text = cmd_text.strip()
        if not cmd_text:
            continue
            
        if cmd_text.lower() in ('exit', 'quit'):
            break
        
        if cmd_text == 'clear':
            click.clear()
            continue
            
        # 构造并执行子进程命令
        # 我们使用当前 Python 解释器重新调用脚本，确保环境一致
        # cmd_text 应该是不包含 'realtrade' 前缀的，例如 "account positions"
        
        # 简单处理 help
        if cmd_text == 'help':
            args = ['--help']
        else:
            args = shlex.split(cmd_text)
            
        # 组合完整命令: python /path/to/main.py arg1 arg2 ...
        full_cmd = [sys.executable, sys.argv[0]] + args
        
        try:
            subprocess.run(full_cmd)
        except Exception as e:
            console.print(f"[red]执行出错: {e}[/red]")

# 注册所有子命令
cli.add_command(shell)
cli.add_command(config_cmd)
cli.add_command(account_cmd)
cli.add_command(quote_cmd)
cli.add_command(strategy_cmd)
cli.add_command(trade_cmd)
cli.add_command(backtest_cmd)
cli.add_command(run_cmd)
cli.add_command(logs_cmd)
cli.add_command(notify_cmd)

def main():
    cli(obj={})

if __name__ == '__main__':
    main()
