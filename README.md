# Finwatch 2.0 — Automated UPI Expense Tracker Bot

A cloud-ready **Telegram Bot** that turns your UPI payment screenshots (**Google Pay, PhonePe, Paytm, BHIM**) into an automated, categorized expense ledger in **Google Sheets** using **Google Gemini 2.5 Flash Multimodal Vision**.

---

## ✨ Features

- 📸 **Screenshot Ingestion:** Send or share payment success screenshots directly from any UPI app.
- ⚡ **Gemini 2.5 Flash Vision:** Instantly extracts:
  - Amount (₹)
  - Merchant / Payee
  - Payment App (GPay / PhonePe / Paytm / BHIM)
  - UPI Reference / UTR ID
  - Date & Time
  - Bank Account
- 🏷️ **Flexible Categorization (3 Ways):**
  1. **Caption on Share:** Add a note or tag when sharing (e.g. `Dinner with friends` or `Sports gear`).
  2. **Interactive Inline Keyboard:** Tap one-click category buttons (`[Food]`, `[Travel]`, `[Sports]`, `[Shopping]`, `[Bills]`, etc.) to update Google Sheets instantly.
  3. **Follow-up Messages:** Send a follow-up text (e.g. `travel` or `badminton`) within 5 minutes to update the last transaction.
- 📊 **Real-time Google Sheets Sync:** Formatted headers, automatic new row insertion, and in-place category cell updates.
- 🔒 **Private & Secure:** Restricts access to your designated Telegram User ID so unauthorized users cannot tamper with your sheet.
- 🚀 **100% Free Tier Compatible:** Gemini API (1,500 req/day free) + Google Sheets API (300 req/min free) + Telegram Bot API (free).

---

## 🛠️ Project Structure

```
Finwatch/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Telegram bot handlers & event loop
│   ├── config.py        # Environment & credentials manager
│   ├── vision.py        # Gemini 2.5 Flash multimodal receipt parser
│   ├── sheets.py        # Google Sheets gspread client & ledger sync
│   └── session.py       # Follow-up message & category keyword engine
├── tests/               # 14 automated unit & async handler tests
├── Dockerfile           # Production container for Render / Docker
├── render.yaml          # Render 1-click blueprint deployment
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README.md
```

---

## 🚀 Quick Setup Guide

### 1. Telegram Bot Token
1. Open Telegram and search for [`@BotFather`](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to name your bot (e.g., `FinwatchLedgerBot`).
3. Copy the HTTP API token provided.

### 2. Google Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** → **Create API key**.
3. Copy the key (Free tier provides 1,500 requests per day at $0 cost).

### 3. Google Sheets & Service Account
1. Create a new Google Sheet at [sheets.google.com](https://sheets.google.com).
2. Copy the **Spreadsheet ID** from the URL:
   `https://docs.google.com/spreadsheets/d/`**`<SPREADSHEET_ID>`**`/edit`
3. Go to [Google Cloud Console](https://console.cloud.google.com/).
4. Create a project and enable the **Google Sheets API** and **Google Drive API**.
5. Go to **IAM & Admin** → **Service Accounts** → **Create Service Account**.
6. Click into the service account → **Keys** tab → **Add Key** → **Create new key** (JSON).
7. Save the downloaded JSON file as `credentials.json` in this folder.
8. **Crucial:** Open your Google Sheet, click **Share**, and paste the service account's email address (e.g., `finwatch@your-project.iam.gserviceaccount.com`) with **Editor** permissions.

### 4. Find Your Telegram User ID
1. Search for [`@userinfobot`](https://t.me/userinfobot) on Telegram and send `/start`.
2. Copy your numeric `Id` (e.g. `123456789`).

---

## 💻 Running Locally

1. **Clone, create virtual environment & install dependencies:**
   ```powershell
   git clone https://github.com/Vishesh-Nagar/Finwatch.git
   cd Finwatch
   python -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   ```

2. **Configure `.env`:**
   Copy `.env.example` to `.env` and fill in your keys:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdef...
   ALLOWED_TELEGRAM_USER_IDS=123456789
   GEMINI_API_KEY=AIzaSy...
   SPREADSHEET_ID=1A2B3C4D5E...
   SHEET_NAME=Transactions
   GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
   ```

3. **Start the bot:**
   ```powershell
   .\.venv\Scripts\python -m bot.main
   ```

---

## ☁️ Deploying to Render

This repo contains a pre-configured [`render.yaml`](./render.yaml) blueprint:

1. Push your repository to GitHub.
2. Sign up / log into [Render](https://render.com/).
3. In Render Dashboard, click **New +** → **Blueprint**.
4. Connect this GitHub repository.
5. In the Environment Variables screen, fill in:
   - `TELEGRAM_BOT_TOKEN`
   - `ALLOWED_TELEGRAM_USER_IDS`
   - `GEMINI_API_KEY`
   - `SPREADSHEET_ID`
   - `GOOGLE_SERVICE_ACCOUNT_JSON`: Paste the entire content of `credentials.json` as a single-line JSON string.
6. Click **Apply**. Render will build and run the Docker worker 24/7!

---

## 🧪 Running Tests

To run the automated test suite using the virtual environment:
```powershell
.\.venv\Scripts\python -m pytest tests/
```
All 14 tests verify configuration parsing, Gemini vision schemas, Google Sheets mutations, session TTLs, and Telegram bot handlers.
