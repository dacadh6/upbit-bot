from datetime import datetime, timedelta, timezone
import os
from flask import Flask, Response
import requests

app = Flask(__name__)


def get_upbit_ticker_details(ticker):
    """현재가뿐만 아니라 High(고가), Low(저가) 정보도 함께 가져옵니다."""
    url = f"https://api.upbit.com/v1/ticker?markets={ticker}"
    try:
        response = requests.get(url, timeout=5).json()
        if isinstance(response, list) and len(response) > 0:
            return {
                "trade_price": response[0]["trade_price"],
                "high_price": response[0]["high_price"],
                "low_price": response[0]["low_price"],
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
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Telegram API Error: {e}")


def run_alert():
    """메인 알림 로직"""
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return

    kst = timezone(timedelta(hours=9))
    current_hour = datetime.now(kst).hour
    is_silent = current_hour >= 23 or current_hour <= 8

    tickers = ["KRW-KERNEL"]
    TARGET_COIN = "KRW-KERNEL"
    HIGH_TARGET = 50.2
    LOW_TARGET = 40.0

    target_alerts = []
    msg_lines = ["📊 **[업비트 실시간 시세 알림]**\n"]

    for ticker in tickers:
        data = get_upbit_ticker_details(ticker)
        if data is None:
            continue

        coin_name = ticker.split("-")[1]
        price = data["trade_price"]
        msg_lines.append(f"• **{coin_name}**: {price:,}원")

        if ticker == TARGET_COIN:
            high_price = data["high_price"]
            low_price = data["low_price"]

            if high_price >= HIGH_TARGET:
                target_alerts.append(
                    f"🚀 **[KERNEL] 50.2원 이상 터치함!** (최고가: {high_price:,}원 / 현재가: {price:,}원)"
                )

            if low_price <= LOW_TARGET:
                target_alerts.append(
                    f"🚨 **[KERNEL] 40.0원 이하 터치함!** (최저가: {low_price:,}원 / 현재가: {price:,}원)"
                )

    hourly_msg = "\n".join(msg_lines)
    final_message = (
        f"{'\n'.join(target_alerts)}\n\n{hourly_msg}"
        if target_alerts
        else hourly_msg
    )

    send_telegram_message(
        token, chat_id, final_message, disable_notification=is_silent
    )


@app.route("/")
def index():
    run_alert()
    # Cron-job.org가 좋아하는 가장 짧은 경량 응답 반환
    return Response("OK", status=200, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
