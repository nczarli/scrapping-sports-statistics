# NBA Team Stats Scraper - AWS Lambda Deployment Guide

This project scrapes NBA team statistics daily using Selenium and uploads the results as a CSV file to an AWS S3 bucket.

## Prerequisites
- AWS Account
- AWS CLI installed & configured
- Docker (for building a Lambda layer)
- Python 3.x with `pip`

---

## 🚀 Deployment Steps

### Step 1: Create an S3 Bucket
1. Go to the **AWS S3 Console**.
2. Click **Create bucket**.
3. Set a unique **Bucket name** (e.g., `nba-team-stats-data`).
4. Leave other settings as default and click **Create bucket**.

---

### Step 2: Create an IAM Role for Lambda
1. Open the **AWS IAM Console**.
2. Navigate to **Roles** → Click **Create Role**.
3. Select **AWS Service** and choose **Lambda** as the trusted entity.
4. Click **Next**, then **Create Policy** and add this JSON:

   ```json
   {
     "Version": "2025-03-16",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject"
         ],
         "Resource": "arn:INPUT YOUR ARN*"
       }
     ]
   }
5. Name the policy **LambdaS3WriteAccess** and attach it to the role.
6. Click **Create Role**

## Step 3: Set Up a Lambda Later for Headless Chrome
1. Set up an Amazon Linux 2 environment:

``` sh
docker run -it amazonlinux:2 bash
```
2. Install Chrome and ChromeDriver:
``` sh
yum install -y unzip curl
curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm -o chrome.rpm
yum localinstall -y chrome.rpm
curl -sSL https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip -o chromedriver.zip
unzip chromedriver.zip
mkdir -p /opt/python/bin
mv chromedriver /opt/python/bin/
mv /usr/bin/google-chrome-stable /opt/python/bin/headless-chromium

```
3. Zip the layer:
``` sh
cd /opt
zip -r chrome-layer.zip .

```

4. Upload the layer to AWS Lambda
- Go to **AWS Lambda Console -> Laters -> Create Layer**
- Upload ``chrome-layer.zip`` and set the runtime to **Python 3.x**

## Step 4: Package Your Python Dependencies
1. Create a new directory
```sh
mkdir lambda_package && cd lambda_package
```
2. Install dependencies:
```sh
pip install selenium beautifulsoup4 boto3 -t .
```
3. Zip everything:
```
zip -r ../nba_scrapper.zip
```
4. Add your script (```scrapper_aws.py```) to the zip file:
```sh
zip -g ../nba_scraper.zip nba_scraper.py
```

## Step 5: Create the AWS Lambda Function
1. Open the **AWS Lambda Console**
2. Click **Create function -> Author from scratch**
3. Set **Function name** to ```nba_stats_scrapper```
4. Choose **Python 3.x** as the runtime
5. Under **Permissions**, attach the IAM role created earlier
6. Click **Create function**

## Step 6: Upload the Deployment Package
1. In the Lambda function, go to the **Code** tab.
2. Click **Upload from -> .zip file**
3. Select ```nba_scrapper.zip``` and click **Save**

## Step 7: Set Environmental Variables
1. In the Lambda function, go to **Configuration -> Environment variables.**
2. Add the following:
```
S3_BUCKET_NAME = nba-team-stats-data
```

## Step 8: Increate Timeout and Memory
1. Go to **Configuration -> General settings**
2. Set:
- Timeout = 5 minutes
- Memory = 1024MB

## Step 9: Schedule Daily Execution with EventBridge
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

