
import os
import requests
from datetime import datetime, timezone

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def get_json(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message
    }, timeout=20)
    r.raise_for_status()

def main():
    profiles = get_json(
        "https://api.dexscreener.com/token-profiles/latest/v1"
    )

    found = 0
    seen = set()

    for token in profiles:
        if token.get("chainId") != "solana":
            continue

        address = token.get("tokenAddress")
        if not address or address in seen:
            continue
        seen.add(address)

        data = get_json(
            f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        )

        pairs = data.get("pairs") or []
        pairs = [
            p for p in pairs
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

        created = pair.get("pairCreatedAt")
        age = 9999
        if created:
            age = (
                datetime.now(timezone.utc).timestamp()
                - created / 1000
            ) / 3600

        if not (
            age <= 24
            and liquidity >= 10000
            and volume >= 5000
            and buys >= 20
        ):
            continue

        name = (pair.get("baseToken") or {}).get("name", "Unknown")
        link = pair.get("url", "")
        alert(
            f"🚨 FOMO MEME HUNTER\n"
            f"Token: {name}\n"
            f"Liquidita: ${liquidity:,.0f}\n"
            f"Volume 1h: ${volume:,.0f}\n"
            f"Acquisti 1h: {buys}\n"
            f"Eta pool: {age:.1f} ore\n"
            f"Contratto: {address}\n"
            f"{link}\n\n"
            f"⚠️ Segnale speculativo, non verificato."
        )
        found += 1

        if found >= 5:
            break

    print(f"Alert inviati: {found}")

if __name__ == "__main__":
    main()
