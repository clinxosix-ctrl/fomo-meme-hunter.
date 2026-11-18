
import os
import json
import requests
from datetime import datetime, timezone

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
STATE_FILE = "sent_alerts.json"

def api(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def notify(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message
    }, timeout=20)
    r.raise_for_status()

def main():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            sent = set(json.load(f))
    else:
        sent = set()

    profiles = api(
        "https://api.dexscreener.com/token-profiles/latest/v1"
    )

    candidates = []

    for token in profiles:
        if token.get("chainId") != "solana":
            continue

        address = token.get("tokenAddress")
        if not address or address in sent:
            continue

        data = api(
            f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        )

        pairs = [
            p for p in (data.get("pairs") or [])
            if p.get("chainId") == "solana"
        ]
        if not pairs:
            continue

        pair = max(
            pairs,
            key=lambda p: (p.get("liquidity") or {}).get("usd") or 0
        )

        liquidity = (pair.get("liquidity") or {}).get("usd") or 0
        volume = (pair.get("volume") or {}).get("h1") or 0
        tx = (pair.get("txns") or {}).get("h1") or {}
        buys = tx.get("buys") or 0
        sells = tx.get("sells") or 0

        created = pair.get("pairCreatedAt")
        if not created:
            continue

        age = (
            datetime.now(timezone.utc).timestamp()
            - created / 1000
        ) / 3600

        if not (
            0 <= age <= 12
            and liquidity >= 15000
            and volume >= 10000
            and buys >= 30
            and buys > sells
        ):
            continue

        score = 0
        if liquidity >= 30000:
            score += 2
        if volume >= 30000:
            score += 2
        if buys >= 100:
            score += 2
        if buys >= sells * 1.5:
            score += 2
        if age <= 3:
            score += 2

        candidates.append((score, address, pair, age,
                           liquidity, volume, buys, sells))

    candidates.sort(reverse=True, key=lambda x: x[0])

    for score, address, pair, age, liquidity, volume, buys, sells in candidates[:5]:
        name = (pair.get("baseToken") or {}).get("name", "Unknown")

        message = (
            f"🚨 FOMO MEME HUNTER\n"
            f"🪙 {name}\n"
            f"⭐ Activity Score: {score}/10\n"
            f"💧 Liquidity: ${liquidity:,.0f}\n"
            f"📊 Volume 1h: ${volume:,.0f}\n"
            f"🟢 Buys: {buys} | 🔴 Sells: {sells}\n"
            f"⏱ Age: {age:.1f} hours\n"
            f"📋 Contract: {address}\n"
            f"🔗 {pair.get('url', '')}\n\n"
            f"⚠️ Speculative alert. Security not verified."
        )

        notify(message)
        sent.add(address)

    with open(STATE_FILE, "w") as f:
        json.dump(sorted(sent), f)

    print(f"Alert inviati: {min(5, len(candidates))}")

if __name__ == "__main__":
    main()
