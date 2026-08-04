from datetime import datetime, timedelta, timezone
import os
from flask import Flask
import requests

app = Flask(__name__)


def get_upbit_ticker_details(ticker):
    """현재가뿐만 아니라 High(고가), Low(저가) 정보도 함께 가져옵니다."""
    url = f"https://api.upbit.com/v1/ticker?markets={ticker}"
    try:
        response = requests.get(url).json()
        if isinstance(response, list) and len(response) > 0:
            return {
                "trade_price": response[0]["trade_price"],  # 현재가
                "high_price": response[0]["high_price"],  # 최근 24시간 최고가
                "low_price": response[0]["low_price"],  # 최근 24시간 최저가
            }
    except Exception as e:
        print(f"Upbit API Error: {e}")
    return None


def send_telegram_message(token, chat_id, message, disable_notification=False):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_notification": disable_notification,
    }
    requests.post(url, json=payload)


def run_alert():
    """기존 main.py의 메인 로직"""
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("텔레그램 토큰 또는 채팅 ID가 설정되지 않았습니다.")
        return

    # 한국 시간(KST) 기준 계산
    kst = timezone(timedelta(hours=9))
    current_hour = datetime.now(kst).hour

    # 23시 ~ 08시 무음 설정 (23, 0, 1, 2, 3, 4, 5, 6, 7, 8시)
    is_silent = current_hour >= 23 or current_hour <= 8

    tickers = ["KRW-KERNEL"]

    TARGET_COIN = "KRW-KERNEL"
    HIGH_TARGET = 50.2  # 이상 도달 목표가
    LOW_TARGET = 40.0  # 이하 도달 목표가

    target_alerts = []
    msg_lines = ["📊 **[업비트 실시간 시세 알림]**\n"]

    for ticker in tickers:
        data = get_upbit_ticker_details(ticker)
        if data is None:
            continue

        coin_name = ticker.split("-")[1]
        price = data["trade_price"]
        msg_lines.append(f"• **{coin_name}**: {price:,}원")

        # KERNEL 코인이 목표가 범위를 터치했는지 검사
        if ticker == TARGET_COIN:
            high_price = data["high_price"]
            low_price = data["low_price"]

            # 1. 50.2원 이상에 도달한 적이 있는지 (고가 기준)
            if high_price >= HIGH_TARGET:
                target_alerts.append(
                    f"🚀 **[KERNEL] 50.2원 이상 터치함!** (최고가: {high_price:,}원 / 현재가: {price:,}원)"
                )

            # 2. 40.0원 이하로 내려간 적이 있는지 (저가 기준)
            if low_price <= LOW_TARGET:
                target_alerts.append(
                    f"🚨 **[KERNEL] 40.0원 이하 터치함!** (최저가: {low_price:,}원 / 현재가: {price:,}원)"
                )

    # 멘트 구성
    hourly_msg = "\n".join(msg_lines)

    if target_alerts:
        alert_header = "\n".join(target_alerts)
        final_message = f"{alert_header}\n\n{hourly_msg}"
    else:
        final_message = hourly_msg

    send_telegram_message(
        token, chat_id, final_message, disable_notification=is_silent
    )


@app.route("/")
def index():
    # Cron-job.org가 이 URL을 호출할 때 알림 실행
    run_alert()
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
