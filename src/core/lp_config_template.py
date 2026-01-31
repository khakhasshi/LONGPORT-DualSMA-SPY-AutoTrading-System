from longport.openapi import Config

def get_hardcoded_lp_config():
    # 请在这里直接填写您的 LongPort API 信息
    # Please fill in your LongPort API information here
    app_key = "YOUR_APP_KEY"
    app_secret = "YOUR_APP_SECRET"
    access_token = "YOUR_ACCESS_TOKEN"
    
    return Config(
        app_key=app_key,
        app_secret=app_secret,
        access_token=access_token
    )
