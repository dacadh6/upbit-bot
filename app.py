import os
from datetime import datetime, timedelta, timezone
from flask import Flask
import requests

app = Flask(__name__)


def get_upbit_ticker_details(tickers):
    ticker_str = ",".join(tickers)
    url = f"https://api.upbit.com/v1/ticker?markets={ticker_str}"
    try:
        response = requests.get(url, timeout=5).json()
        if isinstance(response, list) and len(response) > 0:
            result = {}
            for item in response:
                result[item["market"]] = {
                    "trade_price": item["trade_price"],
                    "high_price": item["high_price"],
                    "low_price": item["low_price"],
                    "signed_change_rate": item["signed_change_rate"],
                }
            return result
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
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    current_hour = now.hour
    current_minute = now.minute

    # ----------------------------------------------------
    # [알림 주기 제어]
    # - 09:00 ~ 10:00 사이: 10분마다 알림 발송
    # - 그 외 시간: 정각(00분~09분)에만 1시간 간격 알림 발송
    # ----------------------------------------------------
    is_frequent_time = (current_hour == 9) or (current_hour == 10 and current_minute < 10)

    if not is_frequent_time and current_minute >= 10:
        return

    # 야간 무음 설정 (23시 ~ 08시)
    is_silent = current_hour >= 23 or current_hour <= 8

    tickers = ["KRW-KERNEL", "KRW-BTC"]
    TARGET_COIN = "KRW-KERNEL"
    HIGH_TARGET = 50.2
    LOW_TARGET = 40.0

    ticker_data = get_upbit_ticker_details(tickers)
    if not ticker_data:
        return

    target_alerts = []
    msg_lines = ["📊 **[업비트 실시간 시세 알림]**\n"]

    for ticker in tickers:
        data = ticker_data.get(ticker)
        if not data:
            continue

        coin_name = ticker.split("-")[1]
        price = data["trade_price"]
        change_rate = data["signed_change_rate"] * 100

        rate_str = f"{change_rate:+.2f}%"

        # 모든 코인에 등락률 표시
        msg_lines.append(f"• **{coin_name}**: {price:,}원 ({rate_str})")

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
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
