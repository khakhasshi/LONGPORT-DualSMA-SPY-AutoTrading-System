import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.core.lp_config import get_hardcoded_lp_config
from longport.openapi import QuoteContext, TradeContext

def test_quote():
    print("Testing QuoteContext Connection...")
    conf = get_hardcoded_lp_config()
    try:
        ctx = QuoteContext(conf)
        print("QuoteContext Initialized.")
        q = ctx.quote(["SPY.US"])
        print(f"Quote received: {q}")
        return True
    except Exception as e:
        print(f"QuoteContext Failed: {e}")
        return False

def test_trade():
    print("\nTesting TradeContext Connection...")
    conf = get_hardcoded_lp_config()
    try:
        ctx = TradeContext(conf)
        print("TradeContext Initialized.")
        assets = ctx.account_asset()
        print(f"Assets received: {assets}")
        return True
    except Exception as e:
        print(f"TradeContext Failed: {e}")
        return False

if __name__ == "__main__":
    q_ok = test_quote()
    t_ok = test_trade()
    
    if q_ok and t_ok:
        print("\nAll connections successful!")
    else:
        print("\nSome connections failed.")
