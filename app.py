from flask import Flask, request, jsonify
import smtplib
from email.message import EmailMessage
import os
import logging
import threading
from dotenv import load_dotenv

# ---------------- ENV ----------------
load_dotenv()

EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO = "sandesh.vlcs@gmail.com"

# ---------------- LOGGING ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

if not EMAIL_FROM or not EMAIL_PASS:
    logger.error("EMAIL_FROM or EMAIL_PASS not set")
else:
    logger.info("Email environment variables loaded successfully")

# ---------------- FLASK ----------------
app = Flask(__name__)

# ---------------- EMAIL WORKER ----------------
def send_email_async(client_ip, domain, timestamp):
    try:
        msg = EmailMessage()
        msg["Subject"] = "Website Access Detected"
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO

        msg.set_content(f"""
Website access detected

Client IP: {client_ip}
Domain: {domain}
Time: {timestamp}
""")

        # IMPORTANT: timeout prevents Render worker hang
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
            smtp.login(EMAIL_FROM, EMAIL_PASS)
            smtp.send_message(msg)

        logger.info("Email sent successfully (async)")

    except Exception:
        logger.exception("Async email sending failed")

# ---------------- ROUTES ----------------
@app.route("/notify", methods=["POST"])
def notify():
    logger.info("Received /notify request")

    data = request.get_json(silent=True)
    if not data:
        logger.warning("Invalid or missing JSON")
        return jsonify({"error": "Invalid JSON"}), 400

    client_ip = data.get("client_ip")
    domain = data.get("domain")
    timestamp = data.get("timestamp")

    logger.info(f"Event detected | IP={client_ip} | Domain={domain}")

    # Run email in background thread (NON-BLOCKING)
    threading.Thread(
        target=send_email_async,
        args=(client_ip, domain, timestamp),
        daemon=True
    ).start()

    # Immediate response (prevents Gunicorn timeout)
    return jsonify({"status": "event accepted"}), 202


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting service on port {port}")
    app.run(host="0.0.0.0", port=port)
