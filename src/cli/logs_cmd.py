import click
import os
import time
from rich.console import Console

console = Console()

@click.command(name='logs')
@click.option('--tail', is_flag=True, help='实时查看 (类似 tail -f)')
@click.option('--lines', '-n', default=50, help='显示最后 N 行')
def logs_cmd(tail, lines):
    """查看系统日志"""
    # 假设日志文件是 logs/ 下当天的文件
    # 这里简单起见，找最新的日志文件
    log_dir = "logs"
    if not os.path.exists(log_dir):
        console.print("[yellow]日志目录不存在[/yellow]")
        return
        
    try:
        files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith('.log')]
        if not files:
            console.print("[yellow]暂无日志文件[/yellow]")
            return
            
        # 按修改时间排序，取最新的
        latest_file = max(files, key=os.path.getmtime)
        console.print(f"[dim]Viewing log file: {latest_file}[/dim]")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            if tail:
                # 简单实现 tail -f
                # 先读取最后部分
                f.seek(0, 2)
                f_size = f.tell()
                f.seek(max(f_size - 2000, 0)) # 倒退一下读取一些上下文
                for line in f:
                    console.print(line.strip(), highlight=False)
                    
                while True:
                    line = f.readline()
                    if line:
                        console.print(line.strip(), highlight=False)
                    else:
                        time.sleep(0.5)
            else:
                # 读取最后 N 行
                # 这种实现对于大文件效率不高，但对于日切日志通常够用
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    console.print(line.strip(), highlight=False)
                    
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error reading logs:[/red] {e}")
