import requests
import psycopg2
from datetime import datetime
from collections import defaultdict
import os
from dotenv import load_dotenv
import time

load_dotenv()

def fetch_and_store_margins():

    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 5432)
    )

    cursor = conn.cursor()

    # Define symbols
    strikes = range(24700, 25000 + 1, 50)
    symbols = [f"NSE:NIFTY25JUN{strike}CE" for strike in strikes] + \
              [f"NSE:NIFTY25JUN{strike}PE" for strike in strikes]
# Define symbols
strikes = range(24900, 25500 + 1, 50)
symbols = [f"NSE:NIFTY25JUN{strike}CE" for strike in strikes] + \
          [f"NSE:NIFTY25JUN{strike}PE" for strike in strikes]

    token_id = os.getenv("FYERS_TOKEN_ID")
    auth_token = os.getenv("FYERS_AUTH")

    # API headers
    url = f"https://api-t1.fyers.in/trade/v3/margin?token_id={token_id}"
    headers = {
        "accept": "application/json",
        "authorization": auth_token,
        "content-type": "application/json",
        "origin": "https://trade.fyers.in",
        "referer": "https://trade.fyers.in/",
        "user-agent": "Mozilla/5.0"
    }

    now = datetime.now()
    margins = defaultdict(dict)

    for symbol in symbols:
        payload = {
            "symbol": symbol,
            "qty": 75,
            "side": -1,
            "productType": "MARGIN",
            "limitPrice": 0,
            "stopLoss": 0,
            "stopPrice": 0,
            "takeProfit": 0,
            "type": 2
        }

        response = requests.post(url, headers=headers, json=payload)
        try:
            data = response.json()
            margin_total = data["data"]["margin_total"] if data.get("s") == "ok" else None
        except:
            margin_total = None

        strike = int(symbol[14:-2])
        opt_type = symbol[-2:]
        margins[strike][opt_type] = margin_total

    for strike in sorted(margins):
        ce = margins[strike].get("CE")
        pe = margins[strike].get("PE")
        cursor.execute("""
            INSERT INTO margin_data (timestamp, strike, ce_margin, pe_margin)
            VALUES (%s, %s, %s, %s)
        """, (now, strike, ce, pe))

    conn.commit()
    conn.close()
    print(f"✅ Data saved to Supabase at {now}")

if __name__ == "__main__":
    while True:
        fetch_and_store_margins()
        time.sleep(12)
