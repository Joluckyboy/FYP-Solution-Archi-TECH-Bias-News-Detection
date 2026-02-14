# GitHub Actions CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment.

## Workflows

### 1. CI Pipeline (`ci.yml`)

**Triggers:** Push to `main`/`develop`, Pull Requests, Manual

**Jobs:**

- **unit-tests**: Runs tests for all backend services in parallel using matrix strategy
  - Database, Fact-Check, Sentiment, Emotion, Propaganda, Scraper, Application
  - Generates coverage reports and uploads to Codecov
- **frontend-tests**: Lints and builds the React frontend
  - Runs ESLint
  - Creates production build
  - Uploads build artifacts
- **docker-build**: Validates Docker builds for all services (PR only)
  - Tests that all services can be built successfully
  - Uses GHA caching for faster builds
- **Path filtering optimization**: Skips slow ML service builds (sentiment, emotion, propaganda) unless their specific directories changed
  | PR Changes | Build Behavior |
  |------------|----------------|
  | Only `frontend/` | Entire docker-build job skipped |
  | `backend/database/` | Only database builds, ML services skipped |
  | `backend/sentiment/` | Sentiment builds, other ML services skipped |
  | Multiple backend dirs | Only affected services build |
  - Uses `dorny/paths-filter` to determine affected services
  - Outputs used to conditionally skip unnecessary builds
- **code-quality**: Python code quality checks
  - Flake8 for linting
  - Black for formatting
  - isort for import organization

### 2. CD Pipeline (`cd.yml`)

**Triggers:** Push to `main`, Manual

**Jobs:**

- **changes**: Detects which services have changed files using `dorny/paths-filter`
- **build-and-push**: Builds and pushes Docker images to Amazon ECR (only for changed services)
  - Tags images with both `latest` and commit SHA for rollback
  - Uses GHA caching for faster builds
  - All 11 services supported: database, sentiment, emotion, propaganda, political-bias, factcheck, analyzer, scraper, application, webapp, telebot
- **deploy**: SSHs into the EC2 instance and pulls/restarts updated services
  - Logs into ECR on the instance
  - Runs `docker-compose pull` and `docker-compose up -d`
  - Cleans up old Docker images

| Push Changes | What Gets Deployed |
|-------------|-------------------|
| Only `application/` | Only application image rebuilt & deployed |
| Only `frontend/` | Only webapp image rebuilt & deployed |
| `backend/sentiment/` + `backend/emotion/` | Both sentiment and emotion rebuilt & deployed |
| Multiple directories | All affected services rebuilt & deployed |

**Required GitHub Secrets:**

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |
| `EC2_SSH_KEY` | Contents of the EC2 .pem key file |

### 3. PR Validation (`pr-validation.yml`)

**Triggers:** Pull Request events

**Jobs:**

- **pr-checks**: Basic PR validation
  - Validates semantic PR titles (feat, fix, docs, etc.)
  - Checks for merge conflicts
  - Detects large files (>5MB)
- **security-scan**: Security vulnerability scanning
  - Runs Trivy scanner
  - Uploads results to GitHub Security tab
- **dependency-review**: Reviews dependency changes
  - Checks for security vulnerabilities in new dependencies
  - Fails on moderate+ severity issues

