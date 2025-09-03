import time
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# פרטי ימות
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"

# קובץ שמע מתוך GitHub RAW
FILE_URL = "https://raw.githubusercontent.com/yn6733212/ivr-audio/main/assets/audio/שתי.wav"

# שלוחה יעד
TARGET_PATH = "ivr2:/7/"

def upload_to_yemot(file_bytes, target_filename):
    m = MultipartEncoder(fields={
        'token': TOKEN,
        'path': TARGET_PATH + target_filename,
        'file': (target_filename, file_bytes, 'audio/wav')
    })
    resp = requests.post(
        "https://www.call2all.co.il/ym/api/UploadFile",
        data=m,
        headers={'Content-Type': m.content_type}
    )
    print(f"סטטוס ({target_filename}):", resp.text)

# שליפת הקובץ פעם אחת מה-GitHub
resp = requests.get(FILE_URL)
if resp.status_code != 200:
    raise Exception(f"שגיאה בשליפת הקובץ מ-GitHub: {resp.status_code}")
file_bytes = resp.content

# העלאה ראשונית כ-001.wav
upload_to_yemot(file_bytes, "001.wav")

# לולאה ל-4 חזרות נוספות
for i in range(2, 6):  # 002 עד 005
    time.sleep(10)  # מחכה 10 שניות
    print("⏳ מתחיל מחדש...")
    filename = f"{i:03}.wav"  # מייצר שם קובץ עם אפסים מובילים (002, 003...)
    upload_to_yemot(file_bytes, filename)
