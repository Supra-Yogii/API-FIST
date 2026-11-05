import smtplib
import os
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def send_email(to: str, subject: str, body: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # ✅ Connect ke server Gmail
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.ehlo()                
        server.starttls()             
        server.ehlo()                 
        server.login(EMAIL_USER, EMAIL_PASS) 
        server.sendmail(EMAIL_USER, to, msg.as_string())
        server.quit()

        print(f"✅ Email sent to {to}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        raise


def get_image_url(name: str) -> str:
    try:
        # Contoh API pakai Unsplash atau dummyimage
        url = f"https://picsum.photos/seed/{name}/400/400"

        response = requests.get(url, timeout=5)

        # Beberapa layanan tidak kirim JSON, jadi langsung return URL hasilnya
        if response.status_code == 200:
            return response.url  # ambil URL final dari redirect Unsplash

        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Gagal ambil gambar untuk {name}: {e}")
        return None