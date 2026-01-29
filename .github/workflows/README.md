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
  - Uses caching for faster builds
- **code-quality**: Python code quality checks
  - Flake8 for linting
  - Black for formatting
  - isort for import organization

### 2. CD Pipeline (`deploy.yml`)

**Triggers:** Push to `main`, Version tags (`v*`), Manual

**Jobs:**

- **build-and-push**: Builds and pushes Docker images to GitHub Container Registry
  - Creates multi-platform images
  - Tags with version, branch, and SHA
  - Publishes to `ghcr.io`

**Required Secrets:**

- `GITHUB_TOKEN` (automatically provided)

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

## Setup Instructions

### 1. Configure Secrets

Add these secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

- `API_KEY`: API key for fact-check service (optional, uses placeholder if not set)
- `API_KEYDS`: Additional API key for fact-check service (optional)

### 2. Enable GitHub Container Registry

1. Go to `Settings > Packages`
2. Ensure packages are set to public or configure access as needed
3. Docker images will be pushed to `ghcr.io/<your-org>/bias-news-*`

### 3. Configure Branch Protection

Recommended branch protection rules for `main`:

1. Require pull request reviews
2. Require status checks to pass:
   - `unit-tests`
   - `frontend-tests`
   - `code-quality`
   - `pr-checks`
3. Require branches to be up to date before merging

### 4. Optional: Codecov Integration

For coverage reports:

1. Sign up at [codecov.io](https://codecov.io)
2. Add your repository
3. Coverage reports will be automatically uploaded

## Workflow Status Badges

Add these badges to your main README.md:

\`\`\`markdown
![CI Pipeline](https://github.com/<your-org>/<your-repo>/actions/workflows/ci.yml/badge.svg)
![Deploy](https://github.com/<your-org>/<your-repo>/actions/workflows/deploy.yml/badge.svg)
\`\`\`

## Manual Workflow Triggers

You can manually trigger workflows from the Actions tab:

1. Go to `Actions` tab
2. Select the workflow
3. Click `Run workflow`
4. Choose the branch and click `Run workflow`

## Troubleshooting

### Tests Failing

- Check the test logs in the Actions tab
- Ensure all dependencies are in `requirements.txt`
- Verify environment variables are set correctly

### Docker Build Failing

- Check the Dockerfile in the failing service
- Ensure all required files are present
- Check for missing dependencies

### Deployment Issues

- Verify GitHub Container Registry permissions
- Check that secrets are configured correctly
- Ensure Docker images are being built successfully

## Customization

### Adding New Services

To add a new service to CI/CD:

1. Add to the matrix in `ci.yml` under `unit-tests`:
   \`\`\`yaml

   - path: backend/new-service
     name: new-service
     \`\`\`

2. Add to the matrix in `ci.yml` under `docker-build`:
   \`\`\`yaml

   - name: new-service
     context: ./backend/new-service
     \`\`\`

3. Add to the matrix in `deploy.yml`:
   \`\`\`yaml
   - name: new-service
     context: ./backend/new-service
     \`\`\`

### Modifying Python Version

Change the Python version in all workflows:
\`\`\`yaml
python-version: '3.11' # Change to your desired version
\`\`\`

### Changing Trigger Branches

Modify the `on` section in workflows:
\`\`\`yaml
on:
push:
branches: [ main, develop, staging ] # Add your branches
\`\`\`
