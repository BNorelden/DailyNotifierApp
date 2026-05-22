import os
import json
import boto3
import requests
from datetime import datetime

ses = boto3.client("ses")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["LOG_TABLE"])

sender = os.environ["SES_EMAIL_FROM"]
recipient = os.environ["SES_EMAIL_TO"]

# -----------------------------
# Helpers
# -----------------------------

def get_quote():
    try:
        response = requests.get(os.environ["QUOTE_API_URL"], timeout=5)
        data = response.json()[0]  # ZenQuotes /today returns a list
        return data["q"], data["a"]
    except Exception as e:
        return f"Could not fetch quote ({e})", "Unknown"


def get_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=40.82&longitude=-74.00"
        "&current_weather=true"
        "&temperature_unit=fahrenheit"
        "&windspeed_unit=mph"
    )
    try:
        data = requests.get(url, timeout=5).json()
        w = data["current_weather"]
        return f"{w['temperature']}°F, Wind {w['windspeed']} mph"
    except Exception as e:
        return f"Could not fetch weather ({e})"


def log_to_dynamodb(mode, quote, weather):
    timestamp = datetime.utcnow().isoformat()

    table.put_item(
        Item={
            "id": timestamp,
            "mode": mode,
            "quote": quote,
            "weather": weather,
            "timestamp": timestamp
        }
    )


def load_template(quote, author, weather):
    with open("email_template.html", "r") as f:
        html = f.read()
        html = html.replace("{{quote}}", quote)
        html = html.replace("{{author}}", author)
        html = html.replace("{{weather}}", weather)
        return html


def send_email(subject, body_html):
    try:
        print("Sending email via SES...")
        response = ses.send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Html": {"Data": body_html}}
            }
        )
        print("SES response:", response)
    except Exception as e:
        print("SES ERROR:", e)


# -----------------------------
# Lambda Handler
# -----------------------------

def lambda_handler(event, context):
    mode = event.get("time", "morning")

    quote_text, quote_author = get_quote()
    weather = get_weather()
    now = datetime.now().strftime("%A, %B %d")

    # Build subject
    if mode == "morning":
        subject = f"Good Morning — {now}"
    elif mode == "evening":
        subject = f"Good Evening — {now}"
    else:
        subject = f"Manual Test — {now}"

    # Build HTML body
    body_html = load_template(quote_text, quote_author, weather)

    # Send email
    send_email(subject, body_html)

    # Log to DynamoDB
    log_to_dynamodb(mode, f"{quote_text} - {quote_author}", weather)

    return {"status": "ok", "mode": mode}
