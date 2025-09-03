import os
import tempfile
import requests
import yfinance as yf
import wave
import contextlib
from datetime import datetime
from requests_toolbelt.multipart.encoder import MultipartEncoder

# ========= הגדרות =========
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"
YEMOT_UPLOAD_URL = "https://www.call2all.co.il/ym/api/UploadFile"
YEMOT_TARGET_DIR = "ivr2:/7/"  # שלוחה לדוגמה
AUDIO_DIR = "assets/audio"

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
        return [f"ו{word}"]
    return [word]

def two_digits_tokens(n: int, with_vav=False):
    if n < 10:
        return one_digit_tokens(n, with_vav)
    if 10 <= n < 20:
        w = TEENS[n - 10]
        return [f"ו{w}"] if with_vav else [w]
    tens = n // 10
    ones = n % 10
    if ones == 0:
        w = TENS[tens]
        return [f"ו{w}"] if with_vav else [w]
    return [TENS[tens]] + one_digit_tokens(ones, with_vav=True)

def three_digits_tokens(n: int, with_vav=False):
    if n < 100:
        return two_digits_tokens(n, with_vav)

    h = n // 100
    rest = n % 100
    parts = []

    # במקום טוקן "תשע מאות" -> ["תשע", "מאה"]
    if h > 0:
        parts += one_digit_tokens(h) + ["מאה"]

    if rest > 0:
        parts += two_digits_tokens(rest, with_vav=True)

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
        parts += three_digits_tokens(thousands)
        parts.append("אלף")
    if rest > 0:
        parts += three_digits_tokens(rest, with_vav=True)
    return parts

def hundred_thousands_tokens(n: int):
    if n < 100000:
        return thousands_tokens(n)
    high = n // 1000
    rest = n % 1000
    parts = three_digits_tokens(high) + ["אלף"]
    if rest > 0:
        parts += three_digits_tokens(rest, with_vav=True)
    return parts

def number_to_tokens(n: int):
    if n < 1000:
        return three_digits_tokens(n)
    if n < 1000000:
        return hundred_thousands_tokens(n)
    raise ValueError("המספר גדול מדי – צריך להרחיב פונקציות")

# ========= מיזוג WAVים =========
def merge_wavs(token_list, out_path):
    files = []
    for t in token_list:
        p = os.path.join(AUDIO_DIR, f"{t}.wav")
        if not os.path.exists(p):
            raise FileNotFoundError(f"לא נמצא קובץ: {p}")
        files.append(p)

    with contextlib.ExitStack() as stack:
        readers = [stack.enter_context(wave.open(f, "rb")) for f in files]
        n_channels = readers[0].getnchannels()
        sampwidth  = readers[0].getsampwidth()
        framerate  = readers[0].getframerate()
        comptype, compname = readers[0].getcomptype(), readers[0].getcompname()

        # בדיקות תאימות
        for w in readers[1:]:
            assert w.getnchannels() == n_channels
            assert w.getsampwidth() == sampwidth
            assert w.getframerate() == framerate
            assert w.getcomptype() == comptype

        with wave.open(out_path, "wb") as out:
            out.setnchannels(n_channels)
            out.setsampwidth(sampwidth)
            out.setframerate(framerate)
            out.setcomptype(comptype, compname)
            for w in readers:
                out.writeframes(w.readframes(w.getnframes()))

# ========= העלאת קובץ בודד =========
def upload_single_wav(local_wav_path, yemot_target_dir, filename="001.wav"):
    if not yemot_target_dir.endswith("/"):
        yemot_target_dir += "/"
    with open(local_wav_path, "rb") as f:
        m = MultipartEncoder(fields={
            "token": TOKEN,
            "path": yemot_target_dir + filename,
            "file": (filename, f, "audio/wav")
        })
        r = requests.post(YEMOT_UPLOAD_URL, data=m, headers={"Content-Type": m.content_type})
        if "success" in r.text.lower():
            print(f"✅ {filename} הועלה בהצלחה ({datetime.now().strftime('%H:%M:%S')})")
        else:
            print(f"⚠️ שגיאה בהעלאת {filename}: {r.text}")

# ========= שימוש לדוגמה =========
def main():
    # שליפת שער ביטקוין עדכני
    btc = yf.Ticker("BTC-USD")
    price = btc.history(period="1d").iloc[-1]["Close"]
    rounded_price = int(round(price))

    print("💰 שער ביטקוין:", rounded_price)

    # בניית הטוקנים
    tokens = number_to_tokens(rounded_price) + ["דולר"]
    print("📝 טוקנים:", tokens)

    # מיזוג והעלאה כקובץ בודד
    with tempfile.TemporaryDirectory() as tmp:
        merged = os.path.join(tmp, "full_message.wav")
        merge_wavs(tokens, merged)
        upload_single_wav(merged, YEMOT_TARGET_DIR, filename="001.wav")

if __name__ == "__main__":
    main()
