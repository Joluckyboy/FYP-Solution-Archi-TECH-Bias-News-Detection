# 🎯 FYP Solution - Archi-TECH Bias News Detection

A comprehensive AI-powered news bias detection system built with microservices architecture, featuring sentiment analysis, emotion detection, bias detection, propaganda identification, and fact-checking capabilities.

[![Continuous Integration](https://github.com/Joluckyboy/FYP-Solution-Archi-TECH-Bias-News-Detection/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Joluckyboy/FYP-Solution-Archi-TECH-Bias-News-Detection/actions/workflows/ci.yml)
[![Deployment](https://github.com/Joluckyboy/FYP-Solution-Archi-TECH-Bias-News-Detection/actions/workflows/cd.yml/badge.svg?branch=main)](https://github.com/Joluckyboy/FYP-Solution-Archi-TECH-Bias-News-Detection/actions/workflows/cd.yml)

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Chrome Extension Setup](#chrome-extension-setup)
- [Configuration](#configuration)
- [Services Overview](#services-overview)
- [Telegram Bot Setup](#telegram-bot-setup)
- [API Documentation](#api-documentation)
- [Quiz Generation](#quiz-generation)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Team](#team)

## ✨ Features

- 🔍 **Multi-dimensional News Analysis**
  - Sentiment Analysis
  - Emotion Detection
  - Propaganda Identification
  - Political Bias Detection
  - Fact-Checking
- **Supabase Integration** for scalable data storage
- **RESTful APIs** with FastAPI
- **Modern Frontend** with React and Vite
- **Chrome Extension** for browser-based article analysis
- **Telegram Bot** interface
- **Web Scraping** capabilities
- **Quiz Generation** for media literacy engagement
- **Redis Caching** for performance optimization
- **Dockerized Microservices** for deployment and orchestration

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ (React + Vite)
│  Port: 5173 │
└──────┬──────┘
       │
┌──────▼────────────────────────────────────────────┐
│         Application Gateway (Port: 8010)         │
└──────┬────────────────────────────────────────────┘
       │
       ├─► Database Service (Port: 8011)
       ├─► Sentiment Analysis (Port: 8012)
       ├─► Emotion Detection (Port: 8013)
       ├─► Propaganda Detection (Port: 8014)
       ├─► Web Scraper (Port: 8015)
       ├─► Fact-Check Service (Port: 8016)
       ├─► Analyzer Service (Port: 8017)
       ├─► Bias Engine (Port: 9000)
       ├─► Redis Cache (Port: 6379)
       └─► Telegram Bot (Port: 8020)
```

## Project Structure
```
FYP-Solution-Archi-TECH-Bias-News-Detection
│
├── application/                # Gateway service
├── backend/
│   ├── analyzer/               # Analysis orchestration service
│   ├── bias_classifier_task/   # ECS orchestration task (scrape → classify → cluster)
│   ├── database/               # Supabase database service
│   ├── emotion/                # Emotion detection service
│   ├── fact-check/             # LLM fact-checking service
│   ├── political_bias/         # Political bias model / bias engine
│   ├── propaganda/             # Propaganda detection service
│   ├── scraper/                # Web scraping service
│   └── sentiment/              # Sentiment analysis service
│
├── datasets/                   # Training/evaluation datasets
├── frontend/                   # React web application / Chrome extension
├── telebot/                    # Telegram bot
│
├── docker-compose.yaml
├── README.md
└── .github/workflows
```
**Each backend service directory contains:**
```
service_name/
├── app.py                      # FastAPI application (or main script for task)
├── Dockerfile                  # Container image definition
├── requirements.txt            # Python dependencies
├── tests/                      # Unit tests (pytest)
└── Service-specific code (models, helpers, utils, etc.)
```

**Frontend directory:**
```
frontend/
├── src/                        # React components, pages, utilities
├── public/                     # Static assets (images, fonts)
├── Dockerfile                  # Frontend Docker image (Vite dev server)
├── package.json                # Node.js dependencies
├── vite.config.js              # Vite bundler configuration
└── manifest.json               # Chrome extension configuration
```
## 🔧 Prerequisites

Before you begin, ensure you have:

- [Docker](https://www.docker.com/get-started) installed and running
- [Docker Compose](https://docs.docker.com/compose/install/) (usually comes with Docker Desktop)
- [Node.js](https://nodejs.org/) (v16 or higher) for frontend development
- [Python 3.10](https://www.python.org/downloads/) or higher
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
TINYURL_API_TOKEN=your_tinyurl_api_token_here
```

**Getting Your Telegram Bot Token:**
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow instructions
3. Choose a name (e.g., "FYP News Analyzer")
4. Choose a username (must end with `_bot`, e.g., `@fyp_news_bot`)
5. Copy the token provided (format: `123456789:ABCdefGHI...`)
6. Paste it as `TELEBOT_TOKEN` in your `.env`

**Architecture Details:**
- ✅ **Containerized Architecture**: All 12 local services run as Docker containers via `docker-compose`
- ✅ **Frontend (Port 5173)**: React + Vite, containerized using `frontend/Dockerfile`
- ✅ **Application Gateway (Port 8010)**: FastAPI orchestration service (`application/`) routes requests to backend services
- ✅ **Backend Services**: 8 FastAPI microservices (sentiment, emotion, propaganda, scraper, fact-check, analyzer, bias_engine, database) + Redis caching layer
- ✅ **Telegram Bot (Port 8020)**: Flask webhook receiver (not FastAPI)
- ✅ **Redis Cache (Port 6379)**: In-memory cache for response caching and session management
- ⏳ **ECS Bias Classifier Task**: Separate AWS ECS scheduled job (not in local docker-compose; runs daily for batch processing)
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

# S3 / AWS Configuration (used by scraper sync, analyzer, bias engine model loading, ECS task)
S3_BUCKET=your_articles_bucket_name
SCRAPER_S3_KEY=scraped_articles/scraped_articles.csv
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=your_access_key_id        
AWS_SECRET_ACCESS_KEY=your_secret_access_key

# Political Bias model artifact (for backend/political_bias)
S3_MODEL_BUCKET=your_model_bucket_name
S3_MODEL_KEY=bias_model/best_model_ba_12_wd.pt
```

#### Variable Details

| Variable | Purpose | Source | Status |
|----------|---------|--------|--------|
| `SUPABASE_URL` | Database endpoint | [Supabase Dashboard](https://app.supabase.com) → Settings → API | ✅ Required |
| `SUPABASE_KEY` | Anonymous key for client authentication | Supabase Dashboard → API | ✅ Required |
| `SUPABASE_SERVICE_KEY` | Service role key for admin operations | Supabase Dashboard → API | ✅ Required |
| `API_KEYDS` | Groq API key for LLM inference (fact-checking) | [Groq Console](https://console.groq.com) | ✅ Required |
| `API_KEY` | Perplexity API key (alternative LLM) | [Perplexity API](https://www.perplexity.ai/) | ✅ Required |
| `MODEL` | Model identifier | Set to `deepseek` | ✅ Required |
| `S3_BUCKET` | S3 bucket for scraped/enriched article CSV | AWS S3 | ✅ Required for ECS daily pipeline |
| `SCRAPER_S3_KEY` | S3 object key for article CSV | Default: `scraped_articles/scraped_articles.csv` | ✅ Required |
| `AWS_REGION` | AWS region for S3/model operations | AWS Console | ✅ Required (default: `ap-southeast-1`) |
| `AWS_ACCESS_KEY_ID` | AWS access key (required for local dev and ECS task) | AWS IAM | ✅ Required |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key (required for local dev and ECS task) | AWS IAM | ✅ Required |
| `S3_MODEL_BUCKET` | S3 bucket storing political bias model weights | AWS S3 | ✅ Required for `political_bias` service |
| `S3_MODEL_KEY` | S3 key for political bias model file | AWS S3 | ✅ Required (default: `bias_model/best_model_ba_12_wd.pt`) |

#### Getting Your API Keys & Cloud Credentials

1. **Supabase Keys:**
   - Go to https://app.supabase.com
   - Select your project
   - Navigate to Settings → API
   - Copy `Project URL`, `Anon Key`, and `Service Role Key`

2. **Groq API Key:**
   - Visit https://console.groq.com
   - Create an account or sign in
   - Go to API Keys section
   - Generate a new API key
   - Paste it as `API_KEYDS` in your `.env`

3. **Perplexity API Key:**
   - Visit https://www.perplexity.ai/ 
   - This is optional; Groq key is the primary one

4. **AWS Credentials + S3 Buckets (Required for ECS daily pipeline and bias model loading):**
   - Visit https://console.aws.amazon.com
   - Ensure you have:
     - One S3 bucket for article CSVs (`S3_BUCKET`)
     - One S3 bucket/object for bias model weights (`S3_MODEL_BUCKET` and `S3_MODEL_KEY`)
   - Region should match your bucket region (`AWS_REGION`, e.g. `ap-southeast-1`)
   - If running locally (without IAM role), create IAM access keys and set:
     - `AWS_ACCESS_KEY_ID`
     - `AWS_SECRET_ACCESS_KEY`
   - If running in ECS with a task role, you can omit local key pairs

5. **TinyURL API Token (for Telegram URL shortening):**
   - Visit https://tinyurl.com/app/dev
   - Create API token
   - Add token to root `.env` as `TINYURL_API_TOKEN`

### 3. Start All Services

```bash
# Build and start all services
docker compose build
docker compose up -d
```

Wait for all services to initialize. You should see:
- ✅ All services running (`database`, `sentiment`, `bias_engine`, `emotion`, `propaganda`, `factcheck`, `analyzer`, `scraper`, `redis`, `application`, `webapp`, `telebot`)
- ✅ Green status indicators in Docker Desktop

### 4. Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| 🎨 **Frontend** | http://localhost:5173 | React web application |
| 🚪 **Application Gateway** | http://localhost:8010/docs | Main API entry point |
| 📊 **Database API** | http://localhost:8011/docs | Swagger UI for database operations |
| 💭 **Sentiment API** | http://localhost:8012/docs | Sentiment analysis endpoints |
| 😊 **Emotion API** | http://localhost:8013/docs | Emotion detection endpoints |
| 📢 **Propaganda API** | http://localhost:8014/docs | Propaganda identification |
| 🕷️ **Scraper API** | http://localhost:8015/docs | Web scraping service |
| ✅ **Fact-Check API** | http://localhost:8016/docs | Fact-checking service |
| 🧠 **Analyzer API** | http://localhost:8017/docs | Topic clustering, related coverage, dashboard analytics |
| 🏛️ **Bias Engine API** | http://localhost:9000/docs | Political bias inference endpoints |
| 🤖 **Telegram Bot Service** | http://localhost:8020 | Telegram polling service (no Swagger UI) |
| 🔴 **Redis** | localhost:6379 | Cache backend (not an HTTP API) |

### 5. Verify All Services Are Running

```bash
# Show running containers
docker compose ps
```
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

- **Click the extension icon** in your Chrome toolbar to open the **Popup** UI
- From the popup, you can:
   - Analyze the current article URL
   - View quick indicators (bias, sentiment, propaganda)
   - Open full analysis page in a new tab
   - Toggle right-click fact-check menu on/off
- **Right-click Fact-check popup flow:**
   1. Highlight a claim on a supported news article page
   2. Right click and choose **"Fact-check this claim"**
   3. A floating fact-check result popup appears on-page with verdict, explanation, and citations
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

- 🧩 **Toolbar Popup UI** - Quick analysis and controls from extension icon
- 🖱️ **Right-click Fact-check Popup** - Context menu fact-check for selected claims
- 🎯 **Real-time Analysis** - Instant analysis of web content

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Extension shows white screen | Run `npm run build` and reload extension in Chrome |
| Extension doesn't appear | Verify you loaded the `dist/` folder (not `frontend/`) |
| Extension not responding | Check browser console (F12) for errors; rebuild and reload |
| "Cannot interact with extension" | Ensure services are running on correct ports |

## ⚙️ Configuration

### Frontend Configuration

Frontend API selection is configured in `frontend/src/config/config.js`.

- `PROD_HOST` sets the cloud host IP/domain
- `CLOUD_API` / `CLOUD_ANALYZER` are cloud endpoints
- `LOCAL_API` / `LOCAL_ANALYZER` are localhost endpoints

### Extension Backend Configuration

Chrome extension backend detection is configured in `frontend/background.js`.

- Extension uses cloud-first fallback logic:
   - Cloud: `http://<PROD_HOST>:8010` and `http://<PROD_HOST>:8016`
   - Fallback: `http://localhost:8010` and `http://localhost:8016`
- Fact-check context menu and badge updates are handled by the background service worker

### Popup & Right-Click Fact-Check Configuration

Popup behavior and right-click toggle are configured in:

- `frontend/popup.html` (extension popup entry)
- `frontend/src/pages/PopupPage.jsx` (popup UI + controls)
- `frontend/background.js` (context menu creation and click handling)

Key settings:

- `contextMenuEnabled` is stored in `chrome.storage.sync`
- Right-click menu label: **"Fact-check this claim"**
- Menu is shown only on likely news URLs and when toggle is enabled
- Selected text is fact-checked via the fact-check service and shown as an on-page floating popup

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

### Analyzer Service (Port 8017)
Coordinates analysis outputs and supports topic clustering, related article grouping, and dashboard-oriented aggregation.

### Bias Engine (Port 9000)
Runs political bias inference using the trained model loaded from S3 artifacts.

### Bias Classifier Task (AWS ECS Scheduled Task)
Batch orchestration workflow that runs on a schedule (scrape → classify → cluster → persist results).

- **Runtime:** AWS ECS / EventBridge schedule
- **Local API:** None (not exposed via docker-compose as an HTTP service)
- **Swagger `/docs`:** Not available

### Telegram Bot (Port 8020)
Provides a conversational interface for news analysis via Telegram.

**Quick Setup:**
1. Get bot token from [@BotFather](https://t.me/BotFather) on Telegram
2. Add to root `.env`:
   ```env
   TELEBOT_TOKEN=your_bot_token_here
   APPLICATION_URL=http://application:8010
   WEB_APP_URL=http://localhost:5173
   TINYURL_API_TOKEN=your_tinyurl_api_token_here  # Optional
   ```
3. Rebuild: `docker-compose up -d --build telebot`
4. Test: Send `/start` to your bot

**Supported Commands:**
- `/start` — Welcome + usage guide
- `/help` — List all commands
- `/source <domain>` — Source credibility lookup (example: `/source cna.com`)
- `/subscribe` — Subscribe to daily politically-biased-articles digest
- `/unsubscribe` — Stop daily digest

**Daily Digest Subscription (Implemented in Telebot):**
- Digest job runs daily at **08:00 UTC** (equivalent to **4:00 PM SGT**)
- `/subscribe` calls `POST /application/digest/subscribe`
- `/unsubscribe` calls `POST /application/digest/unsubscribe`
- Digest send flow:
   1. Load active subscribers via `GET /application/digest/subscriptions`
   2. Fetch recent biased articles via `GET /application/digest/recent-biased?hours=24`
   3. Send top entries to each subscribed chat

**Subscription Prerequisites:**
- `TELEBOT_TOKEN` configured in root `.env`
- `APPLICATION_URL` points to running application service (`http://application:8010` in Docker)
- `WEB_APP_URL` configured for full result links
- `TINYURL_API_TOKEN` for short links in digest/messages

**Features:**
- Submit article URLs for instant analysis
- Get complete results: sentiment, emotion, propaganda, fact-checking, political-bias and omission-bias
- Receive formatted summaries with percentages
- Direct links to detailed web reports
- Daily subscription digest for recently biased articles

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
| 🧠 **Analyzer** | http://localhost:8017/docs | Topic analysis, clustering, and dashboard support |
| 🏛️ **Bias Engine** | http://localhost:9000/docs | Political bias model endpoints |

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



**Quiz Categories:**

| Category | Focus | Question Format |
|----------|-------|-----------------|
| 🎯 **Bias** | Political bias, selective reporting | Compare 2-3 headlines |
| 💭 **Sentiment** | Emotional tone (positive/negative/neutral) | Identify tone differences |
| 😊 **Emotion** | Emotional manipulation, fear appeals | Detect emotional hooks |
| 📢 **Propaganda** | Propaganda techniques (bandwagon, authority) | Recognize manipulation |
| 👤 **Personality** | News consumption habits | 4-option personality assessment |


## Testing

Tests are organized under each service's own `tests/` folder.

### Run

From each service folder (recommended):

```bash
# Example: application gateway
cd application
python -m pytest tests/test_services.py -v

# Example: sentiment service
cd ../backend/sentiment
python -m pytest tests/test_services.py -v

# Example: telegram bot
cd ../../telebot
python -m pytest tests/test_services.py -v
```
### Test Structure

**Tests are distributed across services, not centralized.** Each service contains its own test suite:

| Service | Test Location | Framework | Approach |
|---------|---------------|-----------|----------|
| Application | [application/tests](application/tests) | pytest + asyncio | Gateway routing, Redis caching |
| Database | [backend/database/tests](backend/database/tests) | pytest | DB CRUD, quiz generation |
| Sentiment | [backend/sentiment/tests](backend/sentiment/tests) | pytest + asyncio | Model inference, edge cases |
| Emotion | [backend/emotion/tests](backend/emotion/tests) | pytest + asyncio | Emotion classification |
| Propaganda | [backend/propaganda/tests](backend/propaganda/tests) | pytest + asyncio | Technique detection |
| Fact-Check | [backend/fact-check/tests](backend/fact-check/tests) | pytest + asyncio | LLM calls (mocked) |
| Scraper | [backend/scraper/tests](backend/scraper/tests) | pytest | Content extraction |
| Analyzer | [backend/analyzer/tests](backend/analyzer/tests) | pytest + asyncio | Clustering logic |
| Bias Engine | [backend/political_bias/tests](backend/political_bias/tests) | pytest | Model inference |
| Bias Classifier Task | [backend/bias_classifier_task/tests](backend/bias_classifier_task/tests) | pytest | ECS workflow (S3/Supabase mocked) |
| Telegram Bot | [telebot/tests](telebot/tests) | pytest + asyncio | Handler functions, webhook logic |

### Running Tests

**Test a specific service:**
```bash
cd backend/sentiment
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-mock
python -m pytest tests/test_services.py -v --cov=. --cov-report=term
```

**Run all service tests (mimics CI/CD):**
```bash
# Run each service from inside its own folder
cd application; python -m pytest tests/test_services.py -v
cd ../backend/database; python -m pytest tests/test_services.py -v
cd ../sentiment; python -m pytest tests/test_services.py -v
cd ../emotion; python -m pytest tests/test_services.py -v
cd ../propaganda; python -m pytest tests/test_services.py -v
cd ../fact-check; python -m pytest tests/test_services.py -v
cd ../scraper; python -m pytest tests/test_services.py -v
cd ../analyzer; python -m pytest tests/test_services.py -v
cd ../political_bias; python -m pytest tests/test_services.py -v
cd ../bias_classifier_task; python -m pytest tests/test_services.py -v
cd ../../telebot; python -m pytest tests/test_services.py -v
```

**GitHub Actions CI/CD:**
- Runs on every PR/push to `main` or `dev` branches
- Matrix strategy: tests run **in parallel** for only changed services
- Each service test runs independently with its own dependencies
- Coverage reports generated automatically

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

Built with ❤️ using FastAPI, React, Docker, Redis, and Supabase
