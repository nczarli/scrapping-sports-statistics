# NBA Team Stats Scraper - AWS Lambda (Containerized Deployment)

This project scrapes NBA team statistics using headless Chrome/Selenium and uploads CSV results to S3. Deployed as a Docker container to AWS Lambda.

## 📋 Prerequisites
- AWS Account with CLI configured
- Docker installed locally
- AWS IAM permissions for:
  - Lambda
  - ECR
  - S3
  - EventBridge

## 🚀 Deployment Steps

### 1. Create S3 Bucket
```bash
aws s3api create-bucket --bucket nba-team-stats-$(date +%s) --region us-east-1
```

### 2. Create ECR Repository
```bash
aws ecr create-repository --repository-name nba-scraper-lambda
```

### 3. Build & Push Docker Image
```bash
# Authenticate Docker with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com

# Build image
docker buildx build --platform linux/amd64 --provenance=false -t  nba-scraper-lambda .

# Tag and push
docker tag nba-scraper-lambda:latest [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/nba-scraper-lambda:latest
docker push [ACCOUNT_ID].dkr.ecr.us-east-1.amazonaws.com/nba-scraper-lambda:latest
```
### 4. Add IAM Lambda to Access S3

### 5. Create Lambda Function

### 6. Add environment variables
```bash
S3_BUCKET_NAME=YOUR_BUCKET_NAME
```
### 7: Schedule Daily Execution with EventBridge
1. Open **Amazon EventBridge**
2. Click **Create rule**
3. Set **Rule name** to ```DailyNBAScrapper```
4. Choose **Schedule rule**
5. Set the cron expression
```
cron(0 12 * * ? *)
```
This runs the function every day at **12 PM UTC**
6. Select **Lambda function** as the target and choose **nba_stats_scrapper**
7. Click **Create rule**

