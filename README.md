# 🌍 Geopolitics Dashboard

AI-powered **Geopolitical Intelligence Dashboard** that tracks global conflicts, risks, and strategic developments in real time with Telegram alerts.

---

## 🚀 Features

* 🌍 Real-time global news aggregation (RSS + APIs)
* 🧠 AI-based risk classification (Low / Medium / High)
* 📊 Interactive dashboard with filters & insights
* 🔥 Live breaking news ticker
* 🇮🇳 India impact analysis
* ⚡ Fast performance using caching system
* 🤖 Telegram bot integration (instant updates)
* ⏰ Automated daily summaries (APScheduler)

---

## 🧱 Tech Stack

* **Backend:** FastAPI (Python)
* **Frontend:** HTML, CSS, JavaScript
* **Async:** httpx
* **Scheduler:** APScheduler
* **Database:** SQLite
* **Charts:** Chart.js
* **Bot:** Telegram Bot API

---

## 📂 Project Structure

```
Geo Politics News/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── keywords.py
│   ├── services/
│   │   ├── news_service.py
│   │   ├── summary_service.py
│   │   ├── subscriber_service.py   ← (added, already in your project)
│   │   └── telegram_service.py
│   ├── static/
│   └── templates/
│
├── data/
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Setup (Local)

### 1. Create virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Setup environment variables

Create `.env` file:

```env
NEWSAPI_KEY=your_newsapi_key
TELEGRAM_BOT_TOKEN=your_telegram_token
```

---

### 4. Run the app

```bash
uvicorn app.main:app --reload
```

Open:

```
http://127.0.0.1:8000
```

---

## 🤖 Telegram Bot

👉 Start bot:

https://t.me/WAU_NewsBot

### Commands:

* `/start` → Get latest news instantly
* Auto daily summary supported

---

## ⚡ Performance Optimizations

* Parallel RSS fetching (async)
* Smart caching system
* Background scheduler updates
* Duplicate filtering logic

---

## 🔐 Security

* `.env` is ignored via `.gitignore`
* No API keys exposed
* Safe Telegram token usage

---

## 🚀 Deployment

Recommended platform: **Render**

### Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000
```

---

## 📊 Use Case

* Track global conflicts in one place
* Analyze geopolitical risks
* Stay updated with real-time intelligence

---

## 👨‍💻 Author

**Dhruv Kumar Singh**
B.Tech CSE (Data Science)

---

## 🌟 Future Scope

* 🌍 Global conflict heatmap
* 📈 Predictive analytics
* 🧠 Advanced NLP summarization
* 🚨 Real-time alerts for high-risk events

---

## ⭐ Final Note

This project combines:

```
AI + Data + Real-Time Systems + Automation + Visualization
```

---

## 📬 Connect

* GitHub: https://github.com/dhruvDS13
* LinkedIn: https://www.linkedin.com/in/dhruv-kumar-singh-51a86725a/
* Telegram Bot: https://t.me/WAU_NewsBot
