# Bias News Detection System

An AI-powered system to detect and analyze bias in news articles using advanced machine learning techniques.

##  Tech Stack

### Frontend
- **Next.js** - React framework for production
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework

### Backend & API
- **FastAPI** - Modern Python web framework
- **Python** - Core programming language
- **Dramatiq** - Background task processing

### Databases
- **Supabase (PostgreSQL)** - Managed PostgreSQL database with built-in auth
- **Redis** - Caching and message broker
- **Elasticsearch** - Full-text search and analytics

### Orchestration
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## 📋 Prerequisites

- **Supabase Account** (free at [supabase.com](https://supabase.com))
- **Docker Desktop** installed and running
- **Node.js 20+** installed
- **Git** for version control

## 🛠️ Team Setup Guide

### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd FYP-Solution-Archi-TECH-Bias-News-Detection
```

### Step 2: Configure Environment Variables

```bash
# Create .env under backend folder
```

Add your Supabase credentials:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here
REDIS_URL=redis://localhost:6379
ELASTICSEARCH_URL=http://localhost:9200
```

```bash
# Create .env under root folder
```

Add your Supabase credentials:
```env
# Supabase Configuration
# Get these from your Supabase project settings: https://app.supabase.com
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Elasticsearch Configuration
ELASTICSEARCH_URL=http://localhost:9200

# API Configuration
API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000

# JWT Secret (generate a secure random string)
# JWT_SECRET=your-secret-key-change-this-in-production

# Environment
ENVIRONMENT=development
```

### Step 3: Start Backend Services

```bash
# Navigate to backend folder
cd backend

# Start all backend services (FastAPI, Redis, Elasticsearch, Dramatiq Worker)
docker-compose up -d

# Wait ~30 seconds for services to be ready
# Check if services are running
docker-compose ps
```

You should see all 4 containers running:
- `bias-news-backend` - FastAPI API server
- `bias-news-dramatiq-worker` - Background task processor
- `bias-news-redis` - Cache and message broker
- `bias-news-elasticsearch` - Search engine

### Step 4: Start Frontend

```bash
# Open a new terminal, navigate to frontend folder
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Frontend will start at http://localhost:3000

### Step 6: Verify Everything is Connected

Open your browser and test these URLs:

1. **Frontend**: http://localhost:3000
2. **Backend API Docs**: http://localhost:8000/docs
3. **Health Check**: http://localhost:8000/api/v1/health

## ✅ Testing the Connection

### Test 1: Check Backend Health
```bash
curl http://localhost:8000/api/v1/health
```
Expected response: `{"status":"healthy"}`

### Test 2: Check Supabase Connection
```bash
curl http://localhost:8000/api/v1/news/
```
Expected response: `[]` (empty array, because no data yet)

### Test 3: Create a Test Article
```bash
curl -X POST http://localhost:8000/api/v1/news/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Article",
    "content": "This is a test article to verify the connection.",
    "source": "Manual Test",
    "author": "Test User"
  }'
```
Expected: Returns the created article with an ID

### Test 4: Verify in Supabase Dashboard
- Go to your Supabase project
- Click "Table Editor" → "news_articles"
- You should see your test article!

### Test 5: Frontend Connection
- Open http://localhost:3000
- Frontend should be able to fetch data from http://localhost:8000

## 📁 Project Structure

```
.
├── backend/                    ← Python FastAPI backend
│   ├── docker-compose.yml     ← Backend services orchestration
│   ├── Dockerfile             ← Backend container config
│   ├── requirements.txt       ← Python dependencies
│   └── app/
│       ├── main.py            ← FastAPI application
│       ├── api/v1/endpoints/  ← API routes
│       ├── core/              ← Configuration
│       ├── db/                ← Database connections (Supabase)
│       └── tasks.py           ← Background tasks (Dramatiq)
│
├── frontend/                   ← Next.js React frontend
│   ├── package.json           ← Node.js dependencies
│   ├── src/app/               ← Pages & components
│   └── public/                ← Static assets
│
├── datasets/                   ← Training data and models
│   └── datasets visualization/
│
├── .env                        ← Environment variables (Supabase credentials)
└── README.md                  ← This file
```

## 🌐 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | User interface |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive API documentation |
| Supabase Dashboard | https://app.supabase.com | Database management |
| Redis | localhost:6379 | Cache (internal) |
| Elasticsearch | http://localhost:9200 | Search (internal) |

## 🔧 API Endpoints

### News Endpoints
- `GET /api/v1/news/` - Get all news articles
- `GET /api/v1/news/{article_id}` - Get specific article
- `POST /api/v1/news/` - Create new article
- `POST /api/v1/news/ingest` - Trigger news ingestion

### Analysis Endpoints
- `POST /api/v1/analysis/bias` - Analyze bias in article
- `GET /api/v1/analysis/bias/{article_id}` - Get bias analysis

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📊 Database Management

### Using Supabase Dashboard
- **Visual Table Editor**: Manage data through the web UI
- **SQL Editor**: Run queries and migrations
- **Database Backups**: Automatic daily backups

## 🐳 Docker Commands

```bash
# Start backend services (from backend/ folder)
cd backend
docker-compose up -d

# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend

# Check service status
docker-compose ps

# Stop all services
docker-compose down

# Restart after code changes
docker-compose restart backend

# Rebuild containers after dependency changes
docker-compose up -d --build

# Stop and remove all containers, networks, volumes
docker-compose down -v
```

## 🔧 Common Issues & Solutions

### Issue: Port 8000 already in use
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Stop the conflicting process or use different port in docker-compose.yml
```

### Issue: Docker containers won't start
```bash
# Check Docker Desktop is running
# View detailed logs
docker-compose logs

# Remove old containers and restart
docker-compose down -v
docker-compose up -d --build
```

### Issue: Frontend can't connect to backend
- Verify backend is running: http://localhost:8000/docs
- Check `.env` file exists and has correct Supabase credentials
- Ensure frontend is using `http://localhost:8000` in API calls

### Issue: Supabase connection errors
- Verify Supabase credentials in `.env`
- Check if Supabase project is active (not paused)
- Confirm tables are created in Supabase dashboard

## 🔄 Daily Development Workflow

```bash
# Morning: Start everything
cd backend
docker-compose up -d

cd ../frontend  
npm run dev

# Work on your code...

# Evening: Stop everything
cd backend
docker-compose down
```

## 📝 Development Notes

- **Database**: Supabase-hosted PostgreSQL (cloud, no local Docker needed)
- **Frontend**: Runs natively with Node.js for faster development
- **Backend**: FastAPI with async/await in Docker
- **Background Jobs**: Dramatiq handles async tasks (news ingestion, analysis)
- **Cache**: Redis for caching and Dramatiq message broker
- **Search**: Elasticsearch for full-text search capabilities

## 🎯 Architecture Overview

```
Frontend (Next.js)     Backend (FastAPI)     Database (Supabase)
    Port 3000     →       Port 8000      →    Cloud PostgreSQL
                            ↓ ↑
                     Redis + Elasticsearch
                     (Docker containers)
                            ↓
                     Dramatiq Worker
                  (Background processing)
```

## 🔐 Security Best Practices

- ✅ Never commit `.env` file to Git (already in `.gitignore`)
- ✅ Use `SUPABASE_SERVICE_KEY` only in backend, never in frontend
- ✅ Frontend should only use `SUPABASE_KEY` (anon key)
- ✅ Enable Row Level Security (RLS) in Supabase for production
- ✅ Use environment variables for all sensitive data

## 👥 Team Collaboration

### Before Pushing Code
```bash
# Make sure your code works locally
docker-compose ps  # All services should be "Up"
npm run dev        # Frontend should start without errors
```

### Sharing Updates
1. Test your changes locally
2. Commit with clear messages: `git commit -m "Add feature X"`
3. Push to your branch: `git push origin your-branch`
4. Create Pull Request for team review

## 🧪 Testing

```bash
# Backend API testing (use API docs)
# Open: http://localhost:8000/docs
# Click "Try it out" on any endpoint

# Or use curl:
curl http://localhost:8000/api/v1/news/

# Frontend testing
cd frontend
npm test
```

## 📄 License

[Your License Here]

## 👥 Contributors

[Your Team Names]

---

**Need Help?** 
- Check logs: `docker-compose logs -f`
- Test API: http://localhost:8000/docs  
- Check database: https://app.supabase.com
