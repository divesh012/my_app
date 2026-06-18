import random
import requests

FAST2SMS_API = "YOUR_FAST2SMS_KEY_HERE"

def send_sms(number, message):
    try:
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "sender_id": "TXTIND",
            "message": message,
            "route": "v3",
            "numbers": number
        }
        headers = {
            "authorization": FAST2SMS_API,
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        print("SMS Response:", response.text)
    except Exception as e:
        print("SMS Error:", e)


def generate_otp():
    return str(random.randint(1000, 9999))
