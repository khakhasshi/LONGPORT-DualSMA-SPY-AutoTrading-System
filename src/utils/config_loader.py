import os
import yaml
import re
from pathlib import Path
from dotenv import load_dotenv

def load_env():
    """加载 .env 文件"""
    load_dotenv()

def _env_var_constructor(loader, node):
    """
    解析 YAML 中的环境变量，格式为 ${VAR_NAME}
    """
    pattern = re.compile(r'.*?\${(\w+)}.*?')
    value = loader.construct_scalar(node)
    match = pattern.findall(value)
    if match:
        full_value = value
        for var in match:
            env_val = os.environ.get(var)
            if env_val is None:
                # 如果环境变量不存在，保持原样或报错，这里选择保持原样但给个警告（实际在 logger 中做）
                # 为了简单，如果没找到就留空或者保留占位符
                pass 
            else:
                full_value = full_value.replace(f'${{{var}}}', env_val)
        return full_value
    return value

def load_config(path: str) -> dict:
    """
    加载并解析配置文件
    """
    load_env()
    
    # 注册自定义构造器以处理环境变量
    yaml.SafeLoader.add_implicit_resolver('!env_var', re.compile(r'.*?\${(\w+)}.*?'), None)
    yaml.SafeLoader.add_constructor('!env_var', _env_var_constructor)

    # Hack: 覆盖默认的字符串构造器，使其能处理所有字符串中的变量
    # 上面的 implicit_resolver 可能不够，更稳妥的是 hook 默认的 scalar constructor
    # 但简单起见，我们可以手动处理读取后的字典，或者使用 string.Template
    # 为了完整支持 yaml 结构中的替换，我们使用 regex 替换 approach
    
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件未找到: {path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        # 先读取为字符串
        content = f.read()
        
    # 执行环境变量替换
    # 匹配 ${VAR_NAME}
    pattern = re.compile(r'\${(\w+)}')
    
    def replace_env(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0)) # 如果没找到环境变量，保留原样
        
    content_expanded = pattern.sub(replace_env, content)
    
    # 解析 YAML
    try:
        config = yaml.safe_load(content_expanded)
        return config if config else {}
    except yaml.YAMLError as e:
        raise RuntimeError(f"配置文件解析失败: {e}")

