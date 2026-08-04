import os
import requests

def get_upbit_price(ticker):
    url = f"https://api.upbit.com/v1/ticker?markets={ticker}"
    response = requests.get(url).json()
    return response[0]['trade_price']

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    # 알림받고 싶은 코인 목록 (필요하면 코인을 추가/수정하세요)
    tickers = ["KRW-KERNEL"]
    
    msg_lines = ["📊 **[업비트 실시간 시세 알림]**\n"]
    for ticker in tickers:
        price = get_upbit_price(ticker)
        coin_name = ticker.split("-")[1]
        msg_lines.append(f"• **{coin_name}**: {price:,}원")
    
    message = "\n".join(msg_lines)
    send_telegram_message(token, chat_id, message)
