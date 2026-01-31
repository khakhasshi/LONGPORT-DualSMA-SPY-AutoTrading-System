import click
import yaml
import sys
from rich.console import Console
from rich.syntax import Syntax
from src.utils.config_loader import load_config

console = Console()

@click.group(name='config')
def config_cmd():
    """管理配置文件"""
    pass

@config_cmd.command()
@click.pass_context
def show(ctx):
    """显示当前配置"""
    config_path = ctx.obj.get('CONFIG_PATH')
    try:
        # 这里重新加载一次以确保显示的是解析后的结果
        config = load_config(config_path)
        yaml_str = yaml.dump(config, allow_unicode=True, default_flow_style=False)
        
        syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
        console.print(f"[bold blue]当前配置 ({config_path}):[/bold blue]")
        console.print(syntax)
    except Exception as e:
        console.print(f"[bold red]无法读取配置:[/bold red] {e}")

@config_cmd.command()
@click.pass_context
def validate(ctx):
    """验证配置文件有效性"""
    config_path = ctx.obj.get('CONFIG_PATH')
    try:
        config = load_config(config_path)
        
        # 简单验证必要字段
        required_keys = ['symbol', 'strategy', 'longport']
        missing = [k for k in required_keys if k not in config]
        
        if missing:
            console.print(f"[bold red]配置校验失败![/bold red] 缺失字段: {', '.join(missing)}")
            sys.exit(1)
            
        console.print("[bold green]配置校验通过![/bold green]")
        
        # 验证环境变量是否已填充
        lp_config = config.get('longport', {})
        empty_vars = [k for k, v in lp_config.items() if str(v).startswith('${')]
        if empty_vars:
             console.print(f"[yellow]警告: 以下 Longport 配置项似乎未被环境变量替换:[/yellow] {', '.join(empty_vars)}")
             console.print("[yellow]请检查 .env 文件或系统环境变量[/yellow]")

    except Exception as e:
        console.print(f"[bold red]配置校验出错:[/bold red] {e}")
        sys.exit(1)
