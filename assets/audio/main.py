import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# פרטי ימות
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"

# הקישור הקבוע ל-GitHub RAW (ענף main)
FILE_URL = "https://raw.githubusercontent.com/yn6733212/ivr-audio/main/assets/audio/שתי.wav"

# הנתיב בימות המשיח (שלוחה 7 → הקובץ ייקרא 001.wav)
TARGET_PATH = "ivr2:/7/001.wav"

# שליפת הקובץ מגיטהב
resp = requests.get(FILE_URL)
if resp.status_code != 200:
    raise Exception(f"שגיאה בשליפת הקובץ מ-GitHub: {resp.status_code}")

# העלאה לימות
m = MultipartEncoder(fields={
    'token': TOKEN,
    'path': TARGET_PATH,
    'file': ("001.wav", resp.content, 'audio/wav')
})

upload_resp = requests.post(
    "https://www.call2all.co.il/ym/api/UploadFile",
    data=m,
    headers={'Content-Type': m.content_type}
)

print("סטטוס מהשרת:", upload_resp.text)
