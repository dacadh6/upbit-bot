import os
import requests
from datetime import datetime, timezone, timedelta

def get_upbit_price(ticker):
    url = f"https://api.upbit.com/v1/ticker?markets={ticker}"
    response = requests.get(url).json()
    if isinstance(response, list) and len(response) > 0:
        return response[0]['trade_price']
    return None

def send_telegram_message(token, chat_id, message, disable_notification=False):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_notification": disable_notification
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    # 한국 시간(KST) 기준 계산
    kst = timezone(timedelta(hours=9))
    current_hour = datetime.now(kst).hour

    # 23시 ~ 08시 무음 설정
    is_silent = (current_hour >= 23 or current_hour <= 8)

    # 조회할 코인 목록 (KERNEL 추가)
    tickers = ["KRW-KERNEL"]
    
    # 🎯 KERNEL 코인 감시 목표 가격 설정
    TARGET_COIN = "KRW-KERNEL"
    TARGET_PRICES = [50.2, 40.0]
    
    target_alerts = []
    msg_lines = ["📊 **[업비트 실시간 시세 알림]**\n"]

    for ticker in tickers:
        price = get_upbit_price(ticker)
        if price is None:
            continue
            
        coin_name = ticker.split("-")[1]
        msg_lines.append(f"• **{coin_name}**: {price:,}원")
        
        # KERNEL 코인이 목표 가격에 도달했는지 체크
        if ticker == TARGET_COIN:
            for target_p in TARGET_PRICES:
                # 목표 가격 근처(이하)에 도달한 경우 경보 생성
                if price <= target_p:
                    target_alerts.append(f"🚨 **[{coin_name} 목표가 {target_p}원 도달!]** 현재가: {price:,}원")

    # 목표가 경보 메시지가 있는 경우 맨 위에 표시
    prefix_msg = ""
    if target_alerts:
        prefix_msg = "\n".join(target_alerts) + "\n\n"

    final_message = prefix_msg + "\n".join(msg_lines)
    
    send_telegram_message(token, chat_id, final_message, disable_notification=is_silent)
