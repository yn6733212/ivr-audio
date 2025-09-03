import requests
from urllib.parse import quote
from requests_toolbelt.multipart.encoder import MultipartEncoder
from datetime import datetime
import math

# ========= הגדרות =========
# ימות
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"
YEMOT_UPLOAD_URL = "https://www.call2all.co.il/ym/api/UploadFile"
YEMOT_TARGET_DIR = "ivr2:/7/"   # שלוחה 7; ודא שיש "/" בסוף

# מאגר האודיו שלך ב-GitHub (RAW)
BASE_URL = "https://raw.githubusercontent.com/yn6733212/ivr-audio/main/assets/audio/"

# שם קובץ הפתיח אצלך במאגר:
OPENING_CLIP = "הביטקוין עומד כעת על"  # קובץ בשם "הביטקוין עומד כעת על.wav"

# ========= עזר: מיפויי שמות =========
# התאמות לשמות הקבצים שהצגת (כדי לא ליפול על כתיבים שונים)
ALIASES = {
    # בסיס
    "אפס": "אפס",
    "אחד": "אחד",
    "שתיים": "שתיים",   # יש לך גם "שתי.wav" – נעדיף "שתיים"
    "שתי": "שתי",
    "שלוש": "שלוש",
    "ארבע": "ארבע",
    "חמש": "חמש",
    "שש": "שש",
    "שבע": "שבע",
    "שמונה": "שמונה",
    "תשע": "תישע",      # אצלך הקובץ נקרא "תישע.wav"
    # ו׳ חיבור ליחידות
    "ואחד": "ואחד",
    "ושתיים": "ושתיים",
    "ושלוש": "ושלוש",
    "וארבע": "וארבע",
    "וחמש": "וחמש",
    "ושש": "ושש",
    "ושבע": "ושבע",
    "ושמונה": "ושמונה",
    "ותשע": "ותישע",     # אצלך: "ותישע.wav"
    # 10–19
    "עשר": "עשר",
    "אחד עשרה": "אחד עשרה",
    "שתים עשרה": "שתים עשרה",
    "שלוש עשרה": "שלוש עשרה",
    "ארבע עשרה": "ארבע עשרה",
    "חמש עשרה": "חמש עשרה",
    "שש עשרה": "שש עשרה",
    "שבע עשרה": "שבע עשרה",
    "שמונה עשרה": "שמונה עשרה",
    "תשע עשרה": "תשע עשרה",
    # ו׳ ל-10–19
    "ועשר": "ועשר",
    "ואחד עשרה": "ואחד עשרה",
    "ושתים עשרה": "ושתים עשרה",
    "ושלוש עשרה": "ושלוש עשרה",
    "וארבע עשרה": "וארבע עשרה",
    "וחמש עשרה": "וחמש עשרה",
    "ושש עשרה": "ושש עשרה",
    "ושבע עשרה": "ושבע עשרה",
    "ושמונה עשרה": "ושמונה עשרה",
    "ותשע עשרה": "ותשע עשרה",
    # עשרות
    "עשרים": "עשרים",
    "שלושים": "שלושים",
    "ארבעים": "ארבעים",
    "חמישים": "חמישים",
    "שישים": "שישים",
    "שבעים": "שבעים",
    "שמונים": "שמונים",
    "תשעים": "תשעים",
    # ו׳ לעשרות
    "ועשרים": "ועשרים",
    "ושלושים": "ושלושים",   # אצלך זה כתוב עם ו׳ שונה – "ושלושים.wav"
    "וארבעים": "וארבעים",
    "וחמישים": "וחמישים",
    "ושישים": "ושישים",
    "ושבעים": "ושבעים",
    "ושמונים": "ושמונים",
    "ותשעים": "ותשעים",
    # מאות
    "מאה": "מאה",
    "מאתיים": "מאתיים",
    "שלוש מאות": "שלוש מאות",
    "ארבע מאות": "ארבע מאות",
    "חמש מאות": "חמש מאות",
    "שש מאות": "שש מאות",
    "שבע מאות": "שבע מאות",
    "שמונה מאות": "שמונה מאות",
    # שים לב: "תשע מאות" אין ברשימה שלך – אם תוסיף, תרחיב פה
    # אלפים
    "אלף": "אלף",
    "אלפיים": "אלפיים",
    "שלושת אלפים": "שלושת אלפים",
    "ארבעת אלפים": "ארבעת אלפים",
    "חמשת אלפים": "חמשת אלפים",
    "ששת אלפים": "ששת אלפים",
    "שבעת אלפים": "שבעת אלפים",
    "שמונת אלפים": "שמונת אלפים",
    "תשעת אלפים": "תשעת אלפים",
    # מילים כלליות
    "נקודה": "נקודה",
    "דולר": "דולר",
    "אחוז": "אחוז",
    # פתיח
    "הביטקוין עומד כעת על": "הביטקוין עומד כעת על",
}

UNITS = ["אפס","אחד","שתיים","שלוש","ארבע","חמש","שש","שבע","שמונה","תשע"]
TEENS = ["עשר","אחד עשרה","שתים עשרה","שלוש עשרה","ארבע עשרה","חמש עשרה","שש עשרה","שבע עשרה","שמונה עשרה","תשע עשרה"]
TENS  = ["","עשר","עשרים","שלושים","ארבעים","חמישים","שישים","שבעים","שמונים","תשעים"]
HUNDREDS = ["","מאה","מאתיים","שלוש מאות","ארבע מאות","חמש מאות","שש מאות","שבע מאות","שמונה מאות"]  # אין "תשע מאות" אצלך כרגע

def build_raw_url(word: str) -> str:
    """בונה URL לקובץ במאגר, כולל קידוד שם הקובץ בעברית."""
    name = ALIASES.get(word, word)
    return BASE_URL + quote(name + ".wav", safe="/:")

def fetch_clip_bytes(word: str) -> bytes:
    url = build_raw_url(word)
    r = requests.get(url)
    if r.status_code != 200:
        raise FileNotFoundError(f"לא נמצא קובץ עבור '{word}' ({url})")
    return r.content

def upload_clip(file_bytes: bytes, target_filename: str):
    m = MultipartEncoder(fields={
        "token": TOKEN,
        "path": YEMOT_TARGET_DIR + target_filename,
        "file": (target_filename, file_bytes, "audio/wav")
    })
    resp = requests.post(YEMOT_UPLOAD_URL, data=m, headers={"Content-Type": m.content_type})
    if "success" in resp.text.lower():
        print(f"✅ {target_filename} הועלה בהצלחה ({datetime.now().strftime('%H:%M:%S')})")
    else:
        print(f"⚠️ שגיאה בהעלאת {target_filename}: {resp.text}")

# ===== פירוק מספר → מילים (מותאם לקבצים שיש לך) =====
def two_digits_tokens(n: int, with_leading_vav: bool=False) -> list[str]:
    """0..99. אם with_leading_vav=True ננסה להשתמש בצורת 'ועשרים/ושתיים' וכו'."""
    if n < 10:
        if with_leading_vav and n != 0:
            vmap = ["", "ואחד","ושתיים","ושלוש","וארבע","וחמש","ושש","ושבע","ושמונה","ותשע"]
            return [vmap[n]]
        return [UNITS[n]]

    if 10 <= n < 20:
        teens = TEENS[n-10]
        if with_leading_vav:
            return ["ו"+teens]  # יש לך קבצים כמו "ועשר","ואחד עשרה","ועוד..."
        return [teens]

    tens = n // 10
    ones = n % 10
    if ones == 0:
        t = TENS[tens]
        return [("ו"+t) if with_leading_vav else t]

    # 21..99: "עשרים ושתיים"
    tokens = [TENS[tens]]
    tokens += two_digits_tokens(ones, with_leading_vav=True)  # ליחידה נוסיף ו׳-חיבור
    if with_leading_vav:
        tokens[0] = "ו" + tokens[0]  # להפוך "עשרים" ל"ועשרים" כשזה בא עם חיבור מהקודם
    return tokens

def three_digits_tokens(n: int, with_leading_vav: bool=False) -> list[str]:
    """0..999. לא נשתמש ב'ומאה/ומאתיים' כי אין לך את הקבצים הללו."""
    if n < 100:
        return two_digits_tokens(n, with_leading_vav=with_leading_vav)

    h = n // 100
    rest = n % 100
    parts = [HUNDREDS[h]]
    if rest == 0:
        if with_leading_vav:
            # אין לנו 'ומאה' וכו' – נשאיר בלי ו׳ (יהיה: "... וארבעים | מאה")
            pass
        return parts

    # בין מאות לשאר – **נימנע** מו׳ לפני ה"מאות" (אין קליפים כאלה),
    # אבל כן נוסיף ו׳ לפני החלק שמתחת למאה:
    parts += two_digits_tokens(rest, with_leading_vav=True)
    if with_leading_vav:
        # היינו רוצים 'ו[מאות]' אבל אין קליפ כזה – נשאיר בלי.
        pass
    return parts

def thousands_tokens(n: int) -> list[str]:
    """0..999,999"""
    if n < 1000:
        return three_digits_tokens(n)

    thousands = n // 1000
    below = n % 1000
    parts = []

    if thousands == 1:
        parts += ["אלף"]
    elif thousands == 2:
        parts += ["אלפיים"]
    elif 3 <= thousands <= 9:
        spec = {
            3: "שלושת אלפים", 4: "ארבעת אלפים", 5: "חמשת אלפים",
            6: "ששת אלפים", 7: "שבעת אלפים", 8: "שמונת אלפים", 9: "תשעת אלפים"
        }
        parts += [spec[thousands]]
    else:
        # 10..99 אלף
        parts += two_digits_tokens(thousands) + ["אלפים"]

    if below > 0:
        # נעדיף ו׳ לפני מה שמתחת לאלפים, אבל בלי ו׳ לפני מאות (אין קליפ 'ומאה')
        # לכן: אם below < 100 → נכניס עם ו׳; אם 100..999 → מאות בלי ו׳ ואז השאר עם ו׳
        if below < 100:
            parts += two_digits_tokens(below, with_leading_vav=True)
        else:
            parts += three_digits_tokens(below)  # מאות בלי ו׳
    return parts

def number_to_tokens(n: int) -> list[str]:
    if n == 0:
        return ["אפס"]
    if n < 0:
        n = abs(n)  # אפשר להוסיף "מינוס" אם תקליט
    if n >= 1_000_000:
        # אפשר להרחיב אם תוסיף קליפים לעשרות/מאות אלפים
        raise ValueError("נכון לעכשיו תומך עד 999,999")
    return thousands_tokens(n)

# ========= שליפת מחיר הביטקוין =========
def fetch_btc_usd() -> float:
    """פשוט ומהיר: CoinGecko API."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids":"bitcoin", "vs_currencies":"usd"}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    price = float(data["bitcoin"]["usd"])
    return price

# ========= מהלך ראשי =========
def main():
    # 1) פתיח
    sequence_words = [OPENING_CLIP]

    # 2) מחיר הביטקוין (נעגל לש"ח? לא – כרגע דולר שלם בלבד, אפשר לשנות)
    price_usd = fetch_btc_usd()

    # אם תרצה עיגול לאלפים: n = round(price_usd, -3)
    # כאן נעגל לשלם (ללא נקודה). אפשר גם להשמיע עשרוניים אם תרצה.
    n = int(round(price_usd))

    # 3) המספר כמילים
    num_words = number_to_tokens(n)

    # 4) הוספת "דולר" (אם יש לך הקלטה)
    sequence_words += num_words + ["דולר"]

    # ====== העלאה לימות כרצף 001..00N ======
    print("📝 טוקנים:", " | ".join(sequence_words))

    # הורדה והעלאה אחד-אחד לפי אינדקס
    idx = 1
    for w in sequence_words:
        clip_bytes = fetch_clip_bytes(w)
        fname = f"{idx:03}.wav"
        upload_clip(clip_bytes, fname)
        idx += 1

    print("🎉 סיימתי להעלות עד", f"{idx-1:03}.wav")

if __name__ == "__main__":
    main()
