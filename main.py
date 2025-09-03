import os
import shutil
import tempfile
import requests
import yfinance as yf
from datetime import datetime
from requests_toolbelt.multipart.encoder import MultipartEncoder

# ========= הגדרות =========
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"
YEMOT_UPLOAD_URL = "https://www.call2all.co.il/ym/api/UploadFile"
YEMOT_TARGET_DIR = "ivr2:/7/"  # שלוחה לדוגמה

# ========= מילים כפי שהקבצים קיימים =========
UNITS = ["אפס","אחד","שתי","שלוש","ארבע","חמש","שש","שבע","שמונה","תישע"]

TEENS = [
    "עשר","אחד עשרה","שתים עשרה","שלוש עשרה","ארבע עשרה",
    "חמש עשרה","שש עשרה","שבע עשרה","שמונה עשרה","תשע עשרה"
]

TENS = [
    "","עשר","עשרים","שלושים","ארבעים",
    "חמישים","שישים","שבעים","שמונים","תשעים"
]

HUNDREDS = [
    "","מאה","מאתיים","שלוש מאות","ארבע מאות",
    "חמש מאות","שש מאות","שבע מאות","שמונה מאות","תשע מאות"
]

THOUSANDS_SPECIAL = {
    3: "שלושת אלפים",
    4: "ארבעת אלפים",
    5: "חמשת אלפים",
    6: "ששת אלפים",
    7: "שבעת אלפים",
    8: "שמונת אלפים",
    9: "תשעת אלפים"
}

# ========= פונקציות המרה =========
def one_digit_tokens(n: int, with_vav=False):
    word = UNITS[n]
    if with_vav and n > 0:
        return [f"ו{word}"]  # יש לך קבצים כאלה (ואחד, ושתיים וכו')
    return [word]

def two_digits_tokens(n: int, with_vav=False):
    if n < 10:
        return one_digit_tokens(n, with_vav)
    if 10 <= n < 20:
        word = TEENS[n - 10]
        return [f"ו{word}"] if with_vav else [word]
    tens = n // 10
    ones = n % 10
    parts = []
    if ones == 0:
        word = TENS[tens]
        parts.append(f"ו{word}" if with_vav else word)
    else:
        parts.append(TENS[tens])
        parts.extend(one_digit_tokens(ones, with_vav=True))
    return parts

def three_digits_tokens(n: int, with_vav=False):
    if n < 100:
        return two_digits_tokens(n, with_vav)
    h = n // 100
    rest = n % 100
    parts = []
    word = HUNDREDS[h]
    parts.append(word)  # מאות אין לך עם ו׳
    if rest > 0:
        parts.extend(two_digits_tokens(rest, with_vav=True))
    return parts

def thousands_tokens(n: int):
    if n < 1000:
        return three_digits_tokens(n)
    thousands = n // 1000
    rest = n % 1000
    parts = []
    if thousands == 1:
        parts.append("אלף")
    elif thousands == 2:
        parts.append("אלפיים")
    elif 3 <= thousands <= 9:
        parts.append(THOUSANDS_SPECIAL[thousands])
    else:
        parts.extend(three_digits_tokens(thousands))
        parts.append("אלף")
    if rest > 0:
        parts.extend(three_digits_tokens(rest, with_vav=True))
    return parts

def hundred_thousands_tokens(n: int):
    if n < 100000:
        return thousands_tokens(n)
    hundred_thousands = n // 1000
    rest = n % 1000
    parts = []
    parts.extend(three_digits_tokens(hundred_thousands))
    parts.append("אלף")
    if rest > 0:
        parts.extend(three_digits_tokens(rest, with_vav=True))
    return parts

def number_to_tokens(n: int):
    if n < 1000:
        return three_digits_tokens(n)
    if n < 1000000:
        return hundred_thousands_tokens(n)
    raise ValueError("המספר גדול מדי – צריך להרחיב פונקציות")

# ========= פונקציות ימות =========
def upload_sequence(tokens, yemot_target_dir):
    """
    tokens: רשימת מילים ["מאה","אלף","שלושים"...]
    """
    with tempfile.TemporaryDirectory() as tmp:
        numbered = []
        for idx, token in enumerate(tokens, start=1):
            filename = f"{idx:03}.wav"
            path = os.path.join("assets/audio", f"{token}.wav")
            if not os.path.exists(path):
                raise FileNotFoundError(f"לא נמצא קובץ: {path}")
            dst = os.path.join(tmp, filename)
            shutil.copy(path, dst)
            numbered.append(dst)

        # העלאה לימות
        for dst in numbered:
            fname = os.path.basename(dst)
            with open(dst, "rb") as f:
                m = MultipartEncoder(fields={
                    "token": TOKEN,
                    "path": yemot_target_dir + fname,
                    "file": (fname, f, "audio/wav")
                })
                r = requests.post(YEMOT_UPLOAD_URL, data=m, headers={"Content-Type": m.content_type})
                if "success" in r.text.lower():
                    print(f"✅ {fname} הועלה בהצלחה ({datetime.now().strftime('%H:%M:%S')})")
                else:
                    print(f"⚠️ שגיאה בהעלאת {fname}: {r.text}")

# ========= שימוש לדוגמה =========
def main():
    # שליפת שער ביטקוין עדכני
    btc = yf.Ticker("BTC-USD")
    price = btc.history(period="1d").iloc[-1]["Close"]
    rounded_price = int(round(price))  # נעגל לשלם

    print("💰 שער ביטקוין:", rounded_price)

    # בניית הטוקנים
    tokens = number_to_tokens(rounded_price) + ["דולר"]

    print("📝 טוקנים:", tokens)

    # העלאה לימות
    upload_sequence(tokens, YEMOT_TARGET_DIR)

if __name__ == "__main__":
    main()
