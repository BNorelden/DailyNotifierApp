import os
import boto3
import requests
import time
from datetime import datetime

# -----------------------------
# API URLs & Keys
# -----------------------------

NEWS_KEY = os.environ["NEWS_API_KEY"]
NEWS_API_URL = f"https://api.thenewsapi.com/v1/news/top?api_token={NEWS_KEY}&locale=us"

WEATHER_API_URL = os.environ["WEATHER_API_URL"]
FACT_API_URL = "https://uselessfacts.jsph.pl/random.json?language=en"
NASA_API_URL = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"

sender = os.environ["SES_EMAIL_FROM"]
recipient = os.environ["SES_EMAIL_TO"]

# -----------------------------
# AWS Clients
# -----------------------------

ses = boto3.client("ses")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["LOG_TABLE"])

# -----------------------------
# Helpers
# -----------------------------

def fetch_with_retry(url, timeout, attempts=2):
    for i in range(attempts):
        try:
            return requests.get(url, timeout=timeout).json()
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(0.5)


def get_quote():
    try:
        data = fetch_with_retry(os.environ["QUOTE_API_URL"], timeout=8)
        data = data[0]  # ZenQuotes returns a list
        return data["q"], data["a"]
    except Exception as e:
        return f"Could not fetch quote ({e})", "Unknown"


def get_weather():
    try:
        data = requests.get(WEATHER_API_URL, timeout=5).json()
        w = data["current_weather"]
        return f"{w['temperature']}°F, Wind {w['windspeed']} mph"
    except Exception as e:
        return f"Could not fetch weather ({e})"


def get_news():
    try:
        response = requests.get(NEWS_API_URL, timeout=5).json()
        articles = response.get("data", [])[:3]

        items = []
        for a in articles:
            title = a.get("title", "No title")
            url = a.get("url", "#")
            source = a.get("source", "Unknown")

            items.append(
                f'<div class="news-item"><a href="{url}" target="_blank">{title}</a><br><small>Source: {source}</small></div>'
            )

        return "".join(items) if items else "No news available."
    except Exception as e:
        return f"<div>Could not fetch news ({e})</div>"


def get_fact():
    try:
        data = requests.get(FACT_API_URL, timeout=5).json()
        return data.get("text", "No fact available.")
    except Exception as e:
        return f"Could not fetch fact ({e})"


def get_nasa():
    try:
        data = fetch_with_retry(NASA_API_URL, timeout=6)
        return (
            data.get("title", "NASA APOD"),
            data.get("explanation", "No explanation available."),
            data.get("url", "#")
        )
    except Exception as e:
        return ("NASA APOD", f"Could not fetch NASA APOD ({e})", "#")


def log_to_dynamodb(mode, quote,fact_text, weather):
    timestamp = datetime.utcnow().isoformat()

    table.put_item(
        Item={
            "id": timestamp,
            "mode": mode,
            "quote": quote,
            "fact": fact_text,
            "weather": weather,
            "timestamp": timestamp
        }
    )


def load_template(digest_title, quote, author, weather, news_html, fact_text, nasa_title, nasa_explanation, nasa_url):
    with open("email_template.html", "r") as f:
        html = f.read()
        html = html.replace("{{digest_title}}", digest_title)
        html = html.replace("{{quote}}", quote)
        html = html.replace("{{author}}", author)
        html = html.replace("{{weather}}", weather)
        html = html.replace("{{news_items}}", news_html)
        html = html.replace("{{fact_text}}", fact_text)
        html = html.replace("{{nasa_title}}", nasa_title)
        html = html.replace("{{nasa_explanation}}", nasa_explanation)
        html = html.replace("{{nasa_url}}", nasa_url)
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
    mode = event.get("time") if isinstance(event, dict) else "morning"

    digest_title = "Daily Morning Digest" if mode == "morning" else "Daily Evening Digest"

    quote_text, quote_author = get_quote()
    weather = get_weather()
    news_html = get_news()
    fact_text = get_fact()
    nasa_title, nasa_explanation, nasa_url = get_nasa()

    now = datetime.now().strftime("%A, %B %d")

    if mode == "morning":
        subject = f"Good Morning — {now}"
    elif mode == "evening":
        subject = f"Good Evening — {now}"
    else:
        subject = f"Manual Test — {now}"

    body_html = load_template(
        digest_title,
        quote_text,
        quote_author,
        weather,
        news_html,
        fact_text,
        nasa_title,
        nasa_explanation,
        nasa_url
    )

    send_email(subject, body_html)
    log_to_dynamodb(mode, f"{quote_text} - {quote_author}", fact_text, weather)

    return {"status": "ok", "mode": mode}
