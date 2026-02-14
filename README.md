# 🎯 FYP Solution - Archi-TECH Bias News Detection

A comprehensive AI-powered news bias detection system built with microservices architecture, featuring sentiment analysis, emotion detection, propaganda identification, and fact-checking capabilities.

[![Continuous Integration](https://github.com/Joluckyboy/FYP-Solution-Archi-TECH-Bias-News-Detection/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Joluckyboy/FYP-Solution-Archi-TECH-Bias-News-Detection/actions/workflows/ci.yml)
[![Deployment](https://github.com/Joluckyboy/FYP-Solution-Archi-TECH-Bias-News-Detection/actions/workflows/cd.yml/badge.svg?branch=main)](https://github.com/Joluckyboy/FYP-Solution-Archi-TECH-Bias-News-Detection/actions/workflows/cd.yml)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Chrome Extension Setup](#-chrome-extension-setup)
- [Configuration](#-configuration)
- [Services Overview](#-services-overview)
- [Telegram Bot Setup](#telegram-bot-port-8020)
- [API Documentation](#-api-documentation)

## ✨ Features

- 🔍 **Multi-dimensional News Analysis**
  - Sentiment Analysis
  - Emotion Detection
  - Propaganda Identification
  - Fact-Checking
- 🗄️ **Supabase Integration** for scalable data storage
- 🌐 **RESTful API** with FastAPI
- 🎨 **Modern Frontend** with React & Vite
- 🤖 **Telegram Bot** interface
- 📊 **Web Scraping** capabilities
- 🐳 **Dockerized Microservices** for easy deployment

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ (React + Vite)
│  Port: 5173 │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│         Application Gateway (Port: 8010)     │
└──────┬──────────────────────────────────────┘
       │
       ├─► Database Service (Port: 8011)
       ├─► Sentiment Analysis (Port: 8012)
       ├─► Emotion Detection (Port: 8013)
       ├─► Propaganda Detection (Port: 8014)
       ├─► Web Scraper (Port: 8015)
       ├─► Fact-Check Service (Port: 8016)
       └─► Telegram Bot (Port: 8020)
```

## 🔧 Prerequisites

Before you begin, ensure you have:

- [Docker](https://www.docker.com/get-started) installed and running
- [Docker Compose](https://docs.docker.com/compose/install/) (usually comes with Docker Desktop)
- [Node.js](https://nodejs.org/) (v16 or higher) for frontend development
- A [Supabase](https://supabase.com/) account and project

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd FYP-Solution-Archi-TECH-Bias-News-Detection
```

### 2. Environment Configuration

Create environment files with the following credentials:

#### Root `.env` File (for Telegram Bot)

Create `.env` in the project root:

```env
# Telegram Bot Configuration
TELEBOT_TOKEN=your_telegram_bot_token_here
APPLICATION_URL=http://application:8010
WEB_APP_URL=http://localhost:5173
```

**Getting Your Telegram Bot Token:**
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Choose a name (e.g., "FYP News Analyzer")
4. Choose a username (must end with `_bot`, e.g., `@fyp_news_bot`)
5. Copy the token provided (format: `123456789:ABCdefGHI...`)
6. Paste it as `TELEBOT_TOKEN` in your `.env`

#### Backend `.env` File (for Analysis Services)

Create `.env` in the `backend/` directory:

```env
# Supabase Configuration (Database)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# LLM API Keys (for fact-checking and analysis)
API_KEY=pplx-xxxxxxxxxxxxx                    # Perplexity API Key (optional, for alternative LLM)
API_KEYDS=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxx     # Groq API Key (REQUIRED for fact-checking)

# Model Configuration
MODEL=deepseek                                # Uses Groq API with Llama model (deepseek is a label)
```

#### Variable Details

| Variable | Purpose | Source | Status |
|----------|---------|--------|--------|
| `SUPABASE_URL` | Database endpoint | [Supabase Dashboard](https://app.supabase.com) → Settings → API | ✅ Required |
| `SUPABASE_KEY` | Anonymous key for client authentication | Supabase Dashboard → API | ✅ Required |
| `SUPABASE_SERVICE_KEY` | Service role key for admin operations | Supabase Dashboard → API | ✅ Required |
| `API_KEYDS` | Groq API key for LLM inference (fact-checking) | [Groq Console](https://console.groq.com) | ✅ **CRITICAL** |
| `API_KEY` | Perplexity API key (alternative LLM) | [Perplexity API](https://www.perplexity.ai/) | ⚠️ Optional |
| `MODEL` | Model identifier | Set to `deepseek` | ✅ Fixed |

#### Getting Your API Keys

1. **Supabase Keys:**
   - Go to https://app.supabase.com
   - Select your project
   - Navigate to Settings → API
   - Copy `Project URL`, `Anon Key`, and `Service Role Key`

2. **Groq API Key (ESSENTIAL):**
   - Visit https://console.groq.com
   - Create an account or sign in
   - Go to API Keys section
   - Generate a new API key
   - Paste it as `API_KEYDS` in your `.env`

3. **Perplexity API Key (Optional):**
   - Visit https://www.perplexity.ai/ (if needed)
   - This is optional; Groq key is the primary one

### 3. Start All Services

```bash
# Build and start all services
docker compose build
docker compose up -d
```

Wait for all services to initialize. You should see:
- ✅ All 8 services running
- ✅ Green status indicators in Docker Desktop

### 4. Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| 🎨 **Frontend** | http://localhost:5173 | React web application |
| 🚪 **Application Gateway** | http://localhost:8010 | Main API entry point |
| 📊 **Database API** | http://localhost:8011/docs | Swagger UI for database operations |
| 💭 **Sentiment API** | http://localhost:8012/docs | Sentiment analysis endpoints |
| 😊 **Emotion API** | http://localhost:8013/docs | Emotion detection endpoints |
| 📢 **Propaganda API** | http://localhost:8014/docs | Propaganda identification |
| 🕷️ **Scraper API** | http://localhost:8015/docs | Web scraping service |
| ✅ **Fact-Check API** | http://localhost:8016/docs | Fact-checking service |

## 🧩 Chrome Extension Setup

The FYP system includes a **Chrome extension** for analyzing news directly from your browser.

### Installation

#### 1. Build the Extension

```bash
cd frontend
npm install
npm run build
```

This generates the `dist` folder with all compiled extension files.

#### 2. Load Extension in Chrome

1. Open Chrome and navigate to: **`chrome://extensions/`**
2. Enable **"Developer mode"** (toggle switch in top right corner)
3. Click **"Load unpacked"** button
4. Navigate to and select: `frontend/dist` folder
5. Click **"Select Folder"**

✅ The extension should now appear in your Chrome toolbar!

#### 3. Using the Extension

- **Click the extension icon** in your Chrome toolbar to open the side panel
- The extension displays:
  - Quiz system for media literacy
  - Bias detection analysis
  - Real-time article analysis
- **Current URL is automatically captured** when you switch tabs

### Development Workflow

When you make code changes:

```bash
# Rebuild the extension
npm run build

# Then reload the extension:
# 1. Go to chrome://extensions/
# 2. Click the Reload icon (⟳) on the extension
```

### ⚠️ Important Notes

- **DO NOT use `npm run dev`** - The dev server causes WebSocket errors with the CRX plugin
- Always use **`npm run build`** and load the `dist` folder
- After building, reload the extension in Chrome to see changes

### Extension Features

- 📚 **Quiz Generation** - Auto-generated media literacy quizzes
- 🔍 **Bias Detection** - Analyze current article for bias
- 💾 **Quiz Data** - Store and track quiz responses
- 🎯 **Real-time Analysis** - Instant analysis of web content
- 📊 **Side Panel UI** - Seamless Chrome integration

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Extension shows white screen | Run `npm run build` and reload extension in Chrome |
| Extension doesn't appear | Verify you loaded the `dist/` folder (not `frontend/`) |
| Extension not responding | Check browser console (F12) for errors; rebuild and reload |
| "Cannot interact with extension" | Ensure services are running on correct ports |

## ⚙️ Configuration

### Frontend Configuration

The frontend is configured to use `localhost:8010` for API requests. This is set in:
- `frontend/src/config/config.js`

### React Router Configuration

The app uses React Router with v7 future flags enabled for better performance:
- `v7_startTransition` - Wraps state updates in React.startTransition
- `v7_relativeSplatPath` - Updated relative route resolution

### Chrome Extension Support

The application can run as both a web app and a Chrome extension. Extension-specific features are automatically disabled when running in browser mode.

---

## 🔍 Services Overview

### Application Gateway (Port 8010)
Main orchestration service that coordinates requests across microservices.

### Database Service (Port 8011)
- **Technology:** FastAPI + Supabase
- **Purpose:** Centralized data storage and retrieval
- **Features:** 
  - News article storage
  - URL existence checking
  - Quiz data management

### Sentiment Analysis (Port 8012)
Analyzes the emotional tone of news articles (positive, negative, neutral).

### Emotion Detection (Port 8013)
Identifies specific emotions in text (joy, anger, sadness, fear, etc.).

### Propaganda Detection (Port 8014)
Detects propaganda techniques and biased language patterns.

### Web Scraper (Port 8015)
Extracts content from news URLs for analysis.

### Fact-Check Service (Port 8016)
Verifies claims and cross-references information.

### Telegram Bot (Port 8020)
Provides a conversational interface for news analysis via Telegram.

**Quick Setup:**
1. Get bot token from [@BotFather](https://t.me/BotFather) on Telegram
2. Add to root `.env`:
   ```env
   TELEBOT_TOKEN=your_bot_token_here
   APPLICATION_URL=http://application:8010
   WEB_APP_URL=http://localhost:5173
   ```
3. Rebuild: `docker-compose up -d --build telebot`
4. Test: Send `/start` to your bot

**Features:**
- Submit article URLs for instant analysis
- Get complete results: sentiment, emotion, propaganda, fact-checking
- Receive formatted summaries with percentages
- Direct links to detailed web reports

## 📚 API Documentation

All backend services are built with **FastAPI** and include **interactive Swagger UI** documentation. Once your services are running, you can access the API docs for each service:

### 🔗 Accessing API Documentation

Each service exposes its API documentation at the `/docs` endpoint:

| Service | API Documentation URL | Description |
|---------|----------------------|-------------|
| 📊 **Database** | http://localhost:8011/docs | CRUD operations for news articles and quizzes |
| 💭 **Sentiment** | http://localhost:8012/docs | Analyze sentiment (positive/negative/neutral) |
| 😊 **Emotion** | http://localhost:8013/docs | Detect emotions (joy, anger, fear, etc.) |
| 📢 **Propaganda** | http://localhost:8014/docs | Identify propaganda techniques |
| 🕷️ **Scraper** | http://localhost:8015/docs | Extract content from news URLs |
| ✅ **Fact-Check** | http://localhost:8016/docs | Verify claims and fact-check |

### 📖 How to Use API Documentation

1. **Start your services**: Make sure Docker containers are running
   ```bash
   docker compose up -d
   ```

2. **Open your browser** and navigate to any service's `/docs` endpoint
   - Example: http://localhost:8011/docs

3. **Interactive Testing**: The Swagger UI allows you to:
   - View all available endpoints
   - See request/response schemas
   - Test endpoints directly in the browser
   - View example requests and responses
   - Download OpenAPI specification

### 🧪 Example: Testing Database Service

**Using Swagger UI (Browser):**
1. Go to http://localhost:8011/docs
2. Expand the `POST /database/check_exists/` endpoint
3. Click "Try it out"
4. Enter the request body:
   ```json
   {
     "url": "https://bbc.com/news/test-123"
   }
   ```
5. Click "Execute"
6. View the response below

**Expected Response:**
```json
{
  "exists": true
}
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 🎯 Quiz Generation

The system includes an AI-powered quiz generator that creates media literacy questions for 5 categories: bias, sentiment, emotion, propaganda, and personality.

### Generating Quiz Questions

**Prerequisites:**
- Database service must be running (`docker compose up -d database`)
- Groq API key must be configured in `backend/.env` (API_KEYDS)

**Run the generator:**

```bash
# From project root
python backend/database/generate_quiz.py
```

**What it does:**
- Generates 10 questions per category (50 total)
- Uses Groq's `llama-3.1-8b-instant` model for efficient token usage
- Automatically saves questions to Supabase database
- Provides detailed progress output with success/failure tracking

```

**Quiz Categories:**

| Category | Focus | Question Format |
|----------|-------|-----------------|
| 🎯 **Bias** | Political bias, selective reporting | Compare 2-3 headlines |
| 💭 **Sentiment** | Emotional tone (positive/negative/neutral) | Identify tone differences |
| 😊 **Emotion** | Emotional manipulation, fear appeals | Detect emotional hooks |
| 📢 **Propaganda** | Propaganda techniques (bandwagon, authority) | Recognize manipulation |
| 👤 **Personality** | News consumption habits | 4-option personality assessment |

```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is part of a Final Year Project (FYP) for academic purposes.

## 👥 Team

**Solution Archi TECH Team**

---

Built with ❤️ using FastAPI, React, and Docker
