import os
import requests
from datetime import datetime, timezone, timedelta

def get_upbit_price(ticker):
    url = f"https://api.upbit.com/v1/ticker?markets={ticker}"
    response = requests.get(url).json()
    return response[0]['trade_price']

def send_telegram_message(token, chat_id, message, disable_notification=False):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_notification": disable_notification  # True면 무음(진동X, 소리X) 전송
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    # 한국 시간(KST = UTC+9) 기준 현재 시각 계산
    kst = timezone(timedelta(hours=9))
    current_hour = datetime.now(kst).hour

    # 23시 ~ 08시 (23시, 0시, 1시, 2시, 3시, 4시, 5시, 6시, 7시, 8시) 사이에는 무음 설정
    is_silent = (current_hour >= 23 or current_hour <= 8)

    tickers = ["KRW-KERNEL"]
    
    msg_lines = ["📊 **[업비트 실시간 시세 알림]**\n"]
    for ticker in tickers:
        price = get_upbit_price(ticker)
        coin_name = ticker.split("-")[1]
        msg_lines.append(f"• **{coin_name}**: {price:,}원")
    
    message = "\n".join(msg_lines)
    
    # 메시지 전송 (지정한 수면 시간에는 disable_notification=True)
    send_telegram_message(token, chat_id, message, disable_notification=is_silent)
