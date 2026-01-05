# 🎯 FYP Solution - Archi-TECH Bias News Detection

A comprehensive AI-powered news bias detection system built with microservices architecture, featuring sentiment analysis, emotion detection, propaganda identification, and fact-checking capabilities.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Services Overview](#-services-overview)
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

Create a `.env` file in the `backend/` directory with your Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

> 💡 **Tip:** Get these credentials from your [Supabase Dashboard](https://app.supabase.com) → Settings → API

### 3. Start All Services

```bash
# Build and start all services
docker-compose up --build
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

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is part of a Final Year Project (FYP) for academic purposes.

## 👥 Team

**Archi-TECH Team**

---

Built with ❤️ using FastAPI, React, and Docker
