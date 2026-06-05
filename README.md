DailyNotifierApp — Automated Morning & Evening Email Digest
A serverless AWS application that sends automated morning and evening digest emails containing:

A motivational quote

Local weather

Top news headlines

A daily fact

NASA Astronomy Picture of the Day

A clean HTML email template (dynamic morning/evening title)

Logged entries in DynamoDB for every run

All infrastructure is deployed using Terraform, and all automation is handled by AWS Lambda + EventBridge + SES + DynamoDB.

🚀 Features
Scheduled emails (8 AM & 5 PM) via EventBridge

Dynamic digest title: Daily Morning Digest / Daily Evening Digest

Integrated APIs: Weather, Quotes, Facts, News, NASA APOD

Clean HTML email template rendered by Lambda

DynamoDB logging for every run (mode, quote, fact, weather, timestamp)

SES email delivery

Terraform IaC for full reproducibility

Manual test mode for debugging

🌐 Integrated APIs
Weather — Open‑Meteo

Quotes — ZenQuotes

Facts — UselessFacts API

News — TheNewsAPI

NASA APOD — NASA Astronomy Picture of the Day

🧱 Architecture Overview
EventBridge triggers Lambda twice daily

Lambda fetches:

Quote

Weather

News

Fact

NASA APOD

Lambda renders the HTML template and sends via SES

DynamoDB stores metadata for each run:

timestamp

mode (morning/evening/manual)

quote

fact

weather

Terraform provisions all AWS resources

📸 Screenshots
All screenshots are stored in /screenshots.

Morning Email
/screenshots/MorningEmail.png

Evening Email
/screenshots/EveningEmail.png

Manual Test Email
/screenshots/ManualTest.png

Latest Digest Screenshot
/screenshots/evening_latest.png

DynamoDB Entry
/screenshots/DynamoDB.png

EventBridge Rules
/screenshots/EventBridge.png

🛠️ Tech Stack
AWS Lambda (Python 3.12)

AWS EventBridge Scheduler

AWS SES

AWS DynamoDB

Terraform

Python Requests

📦 Deployment (Terraform)
Update variables in variables.tf.

Zip Lambda code:

Code
zip lambda.zip notifier.py
Deploy:

Code
terraform init
terraform apply
🧪 Testing
Trigger Lambda manually:

Manual test

json
{ "time": "manual" }
Morning simulation

json
{ "time": "morning" }
Evening simulation

json
{ "time": "evening" }
📚 DynamoDB Schema
Each entry contains:

id — timestamp

mode — morning / evening / manual

quote

fact

weather

timestamp

🔧 Future Enhancements
✔️ Add retry logic

✔️ Add additional APIs (news, facts, NASA APOD, weather)

⬜ Exit SES sandbox

⬜ Add DynamoDB TTL expiration

⬜ Add cleanup Lambda

📄 License
MIT License.
