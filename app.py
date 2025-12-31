from flask import Flask, request, jsonify
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import logging

# ----------------- ENV SETUP -----------------
load_dotenv()

EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO   = "sandesh.vlcs@gmail.com"

# ----------------- LOGGING -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

# ----------------- VALIDATION -----------------
if not EMAIL_FROM or not EMAIL_PASS:
    logger.error("EMAIL_FROM or EMAIL_PASS not set in environment")
else:
    logger.info("Email environment variables loaded successfully")

# ----------------- FLASK APP -----------------
app = Flask(__name__)

@app.route("/notify", methods=["POST"])
def notify():
    logger.info("Received /notify request")

    data = request.json
    if not data:
        logger.warning("Request received without JSON body")
        return jsonify({"error": "Invalid JSON"}), 400

    client_ip = data.get("client_ip")
    domain = data.get("domain")
    timestamp = data.get("timestamp")

    logger.info(f"Event detected | IP={client_ip} | Domain={domain}")

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

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_FROM, EMAIL_PASS)
            smtp.send_message(msg)

        logger.info("Email sent successfully")

        return jsonify({"status": "email sent"})

    except Exception as e:
        logger.exception("Failed to send email")
        return jsonify({"error": "email failed"}), 500


# ----------------- SERVER START -----------------
if __name__ == "__main__":
    logger.info("Starting Flask notification service on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
