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

# ========= אוצר מילים =========
UNITS = ["אפס","אחד","שתיים","שלוש","ארבע","חמש","שש","שבע","שמונה","תשע"]

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
    3: "שלושת",
    4: "ארבעת",
    5: "חמשת",
    6: "ששת",
    7: "שבעת",
    8: "שמונת",
    9: "תשעת"
}

# ========= פונקציות המרה =========
def one_digit_tokens(n: int):
    return [UNITS[n]]

def two_digits_tokens(n: int):
    if n < 10:
        return one_digit_tokens(n)
    if 10 <= n < 20:
        return [TEENS[n - 10]]
    tens = n // 10
    ones = n % 10
    if ones == 0:
        return [TENS[tens]]
    return [TENS[tens], "ו", UNITS[ones]]

def three_digits_tokens(n: int):
    if n < 100:
        return two_digits_tokens(n)
    h = n // 100
    rest = n % 100
    parts = []
    if h > 0:
        parts.append(HUNDREDS[h])
    if rest > 0:
        parts.append("ו")
        parts.extend(two_digits_tokens(rest))
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
        parts.append("אלפים")
    else:
        parts.extend(three_digits_tokens(thousands))
        parts.append("אלף")

    if rest > 0:
        parts.append("ו")
        parts.extend(three_digits_tokens(rest))
    return parts

def hundred_thousands_tokens(n: int):
    if n < 100000:
        return thousands_tokens(n)
    hundred_thousands = n // 1000  # כל מה שמעל 1000
    rest = n % 1000
    parts = []

    parts.extend(three_digits_tokens(hundred_thousands))
    parts.append("אלף")

    if rest > 0:
        parts.append("ו")
        parts.extend(three_digits_tokens(rest))
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
    tokens: רשימת מילים [ "מאה","אלף","ושלוש מאות"... ]
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

    # הרכבת טוקנים
    tokens = ["הביטקוין","עומד","כעת","על"] + number_to_tokens(rounded_price) + ["דולר"]

    print("📝 טוקנים:", tokens)

    # העלאה לימות
    upload_sequence(tokens, YEMOT_TARGET_DIR)

if __name__ == "__main__":
    main()
