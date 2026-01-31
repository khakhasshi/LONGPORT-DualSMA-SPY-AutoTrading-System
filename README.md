# DualSMA-SPY-AutoTrading-System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![LongPort](https://img.shields.io/badge/LongPort-SDK-orange)](https://open.longportapp.com/)
[![Status](https://img.shields.io/badge/Status-Active-green)]()

Professional automated trading CLI tool tailored for SPY Moving Average Crossover strategy, built on top of the LongPort Open API.
专业级自动化交易命令行工具，基于 LongPort Open API 构建，专为 SPY 双均线策略定制。

## 📖 简介 | Introduction

DualSMA-SPY-AutoTrading-System (原 RealTrade) 是一个全功能的量化交易实盘系统，采用现代化的 CLI (命令行) 架构。它不仅支持自动化的定时交易，还提供了强大的手动交易终端、实时行情监控、账户管理以及策略回测功能。

**核心特性：**
*   **交互式 Shell**: 类似 `mysql` 或 `ipython` 的交互式命令行，支持命令补全和历史记录。
*   **策略引擎**: 经典双均线 (MA) 策略，支持自定义周期 (如 MA5 vs MA20)。
*   **实盘/模拟**: 无缝切换 Paper Trading 和 Live Trading。
*   **数据可视化**: 终端内直接绘制 K 线图、资金曲线图。
*   **任务调度**: 内置调度器，自动处理开盘/收盘逻辑。
*   **回测框架**: 向量化回测引擎，快速验证策略绩效。

## 🛠 技术栈 | Tech Stack

*   **Language**: Python 3.11
*   **Broker API**: [LongPort SDK](https://github.com/longportapp/openapi-python) (v3.x)
*   **CLI Framework**: `Click` + `Prompt Toolkit` (for REPL)
*   **UI/UX**: `Rich` (Tables, Logs), `Plotext` (Terminal Plotting)
*   **Data Analysis**: `Pandas`, `Numpy`
*   **Scheduling**: `Schedule`

## 🚀 快速开始 | Getting Started

### 1. 安装 | Installation

```bash
# 克隆仓库
git clone https://github.com/your-repo/DualSMA-SPY-AutoTrading-System.git
cd DualSMA-SPY-AutoTrading-System

# 建议创建虚拟环境
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Microsoft

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 | Configuration

为了安全起见，API 密钥不包含在版本控制中。请根据模板创建您的配置文件。

1.  复制模板文件：
    ```bash
    cp src/core/lp_config_template.py src/core/lp_config.py
    ```
2.  编辑 `src/core/lp_config.py`，填入您的 LongPort App Key, Secret 和 Access Token。
3.  (可选) 修改 `config/config.yaml` 以调整策略参数（如均线周期）。

### 3. 运行 | Running

**进入交互式终端 (推荐):**
```bash
python src/cli/main.py
```
你将看到 `DualSMA-SPY>` 提示符，可以开始输入命令。

---

## 💻 功能详解 | Commands

在交互终端中，您可以执行以下命令组：

### 1. 行情 (Quote)
*   **查看实时价格**:
    ```text
    quote price SPY.US AAPL.US
    ```
*   **查看 K 线数据**:
    ```text
    quote kline SPY.US --period day --limit 5
    ```

### 2. 账户 (Account)
*   **查看资金**:
    ```text
    account balance
    ```
*   **查看持仓**:
    ```text
    account positions
    ```
*   **查看今日订单**:
    ```text
    account orders
    ```

### 3. 策略分析 (Strategy)
*   **查看当前信号状态**:
    ```text
    strategy status
    ```
*   **在终端画图 (支持缩放)**:
    ```text
    strategy chart --days 60
    ```

### 4. 交易 (Trade)
*⚠️ 实盘模式下均产生真实资金流动*
*   **买入**:
    ```text
    trade buy SPY.US --quantity 1 --price 100.00
    ```
*   **卖出**:
    ```text
    trade sell SPY.US --quantity 1
    ```
*   **撤单**:
    ```text
    trade cancel <ORDER_ID>
    ```

### 5. 回测 (Backtest)
*   **运行历史回测**:
    ```text
    backtest --symbol SPY.US --days 365 --capital 100000
    ```
    *自动生成绩效表格与资金曲线图。*

### 6. 自动交易 (Run)
*   **挂机运行**:
    ```text
    run --mode live
    ```
    *程序将进入循环模式，每天于预定时间 (如 16:05 ET) 自动检查信号并交易。*

---

## ☁️ 部署指南 | Deployment

推荐使用 `tmux` 在服务器后台长期运行自动交易程序。

```bash
# 1. 新建会话
tmux new -s realtrade

# 2. 启动程序
python src/cli/main.py run --mode live

# 3. 分离会话 (程序后台运行)
# 按 Ctrl+B, 然后按 d

# 4. 回到会话
tmux attach -t realtrade
```

## 📮 联系作者 | Contact

*   **Author**: JIANG JINGZHE
*   **Email**: [contact@jiangjingzhe.com](mailto:contact@jiangjingzhe.com)
*   **WeChat**: jiangjingzhe_2004

© 2026 RealTrade. All Rights Reserved.
```bash
realtrade --help
```
