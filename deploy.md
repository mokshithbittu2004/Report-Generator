# Deployment Guide – Artifact Report Generator (.env.cloud)

This document explains how to deploy the FastAPI service to Google Cloud Run using a production-safe `.env.cloud` configuration.

This guide assumes:
- No prior Docker experience
- Windows or macOS environment
- A Google Cloud account

This version uses environment variables from a local file instead of Secret Manager. This is acceptable for controlled production environments but requires disciplined handling.

---

# 1. Architecture Overview

This deployment uses:

- Docker (containerization)
- Google Cloud Run (serverless compute)
- Google Artifact Registry (container image storage)
- Local `.env.cloud` file for runtime configuration

Security model:

- Secrets are NOT baked into Docker image
- `.env.cloud` is NOT committed to Git
- Environment variables injected at deploy time
- Cloud Run IAM controls access

---

# 2. Security Requirements

Before proceeding:

1. Ensure `.env.cloud` is added to `.gitignore`
2. Do NOT commit secrets to version control
3. Restrict Cloud Run access via IAM if sensitive
4. Rotate API keys periodically

Add to `.gitignore`:

```
.env*
```

---

# 3. Prerequisites

## 3.1 Install Docker

Download:
https://www.docker.com/products/docker-desktop/

Verify:

```bash
docker --version
```

---

## 3.2 Install Google Cloud CLI

Download:
https://cloud.google.com/sdk/docs/install

Initialize:

```bash
gcloud init
```

Set project explicitly:

```bash
gcloud config set project YOUR_PROJECT_ID
```

Recommended region:

```
asia-south1
```

---

# 4. Enable Required Services

```bash
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

---

# 5. Create Artifact Registry (One Time)

```bash
gcloud artifacts repositories create artifact-repo \
  --repository-format=docker \
  --location=asia-south1 \
  --description="Docker repository for Artifact Reporter"
```

---

# 6. Configure Docker Authentication

```bash
gcloud auth configure-docker asia-south1-docker.pkg.dev
```

---

# 7. Create Production Environment File

Create a file in project root:

```
.env.cloud
```

Example:

```
DEBUG=false
LOG_LEVEL=INFO
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
RATE_LIMIT_PER_MINUTE=30
MAX_ZIP_SIZE_MB=500
UPLOAD_TIMEOUT_SECONDS=300
API_KEY_ENABLED=true
API_KEY=your-secure-api-key
SENTRY_ENABLED=false
SENTRY_DSN=
```

Important:

- Replace all placeholder values
- Do NOT commit this file
- Store securely on deployment machine or CI system

---

# 8. Build Docker Image

From project root (where Dockerfile exists):

```bash
docker build -t artifact-reporter:latest .
```

---

# 9. Tag Image for Artifact Registry

```bash
docker tag artifact-reporter:latest \
asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/artifact-repo/artifact-reporter:latest
```

---

# 10. Push Image to Artifact Registry

```bash
docker push \
asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/artifact-repo/artifact-reporter:latest
```

---

# 11. Deploy to Cloud Run (Production Configuration)

Private deployment (recommended):

```bash
gcloud run deploy artifact-reporter \
  --image asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/artifact-repo/artifact-reporter:latest \
  --platform managed \
  --region asia-south1 \
  --no-allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10 \
  --env-vars-file .env.cloud
```

Public deployment (if API key protection is enabled):

```bash
--allow-unauthenticated
```

Key production flags:

- `--min-instances 0` enables scale-to-zero
- `--max-instances 10` prevents runaway cost
- `--timeout 300` supports long ZIP processing
- `--memory 2Gi` ensures stability for large artifacts

---

# 12. Access Service URL

Retrieve service URL:

```bash
gcloud run services describe artifact-reporter \
  --region asia-south1 \
  --format="value(status.url)"
```

Test:

```
https://SERVICE_URL/health
```

---

# 13. Redeploy After Code Changes

```bash
docker build -t artifact-reporter:latest .
docker tag artifact-reporter:latest asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/artifact-repo/artifact-reporter:latest
docker push asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/artifact-repo/artifact-reporter:latest

gcloud run deploy artifact-reporter \
  --image asia-south1-docker.pkg.dev/YOUR_PROJECT_ID/artifact-repo/artifact-reporter:latest \
  --region asia-south1 \
  --platform managed \
  --env-vars-file .env.cloud
```

Cloud Run performs zero-downtime rolling deployment automatically.

---

# 14. Logging and Monitoring

View logs:

```bash
gcloud run services logs read artifact-reporter --region asia-south1
```

Cloud Run integrates automatically with:

- Cloud Logging
- Cloud Monitoring
- Error Reporting

---

# 15. Rollback to Previous Revision

List revisions:

```bash
gcloud run revisions list --service artifact-reporter --region asia-south1
```

Rollback:

```bash
gcloud run services update-traffic artifact-reporter \
  --to-revisions REVISION_NAME=100 \
  --region asia-south1
```

---

# 16. Delete Service

```bash
gcloud run services delete artifact-reporter --region asia-south1
```

Delete Artifact Registry repository:

```bash
gcloud artifacts repositories delete artifact-repo --location=asia-south1
```

---

# 17. Production Hardening Checklist

Before going live:

- `.env.cloud` excluded from Git
- DEBUG=false
- LOG_LEVEL set to INFO or WARNING
- Rate limiting enabled
- File size limits enforced
- Proper error handling implemented
- Health endpoint implemented
- max-instances configured
- Budget alerts configured in Google Cloud
- API key rotated and stored securely

---

# 18. When to Upgrade to Secret Manager

Migrate to Secret Manager if:

- Multiple developers deploy
- CI/CD is introduced
- Customer data is processed
- Compliance requirements exist
- IAM-based secret control is required

---

# 19. Recommended Enterprise Enhancements

- CI/CD pipeline (GitHub Actions or Cloud Build)
- Custom domain with managed SSL
- Cloud Armor for additional protection
- VPC connector for internal services
- Autoscaling optimization
- Load testing validation
- Budget monitoring alerts

---
