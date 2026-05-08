# Smart Employee Onboarding & Identity Service

## Overview

This project is a serverless onboarding system that automates the employee onboarding process from registration to completion.

It acts as the identity backbone of an HRMS by creating a central employee record and coordinating onboarding steps like document collection and IT provisioning.

---

## Features

### 1. Employee Identity

* Create employee profile in DynamoDB
* Auto-generate employee ID (UUID)
* Create Cognito user with login access

### 2. Document Collection

* Upload documents (ID Proof, Degree, Offer Letter)
* Files stored securely in S3
* File type and size validation

### 3. Workflow Automation

* AWS Step Functions controls onboarding stages:

  * Document Collection
  * IT Provisioning
  * Policy Sign-off
* Moves forward only when previous step is completed

### 4. Notifications

* Email sent to user on account creation (SES)
* Reminder emails for pending tasks
* SNS notification to HR when documents are completed

### 5. Dashboard

* Employee view: upload documents and track progress
* Admin view: see onboarding status of all employees

---

## Architecture

Frontend → API Gateway → Lambda → DynamoDB
↓
S3 (Documents)
↓
Step Functions (Workflow)
↓
SES / SNS (Notifications)

---

## Tech Stack

* AWS Lambda
* Amazon DynamoDB
* Amazon S3
* Amazon Cognito
* AWS Step Functions
* Amazon SES
* Amazon SNS
* API Gateway
* HTML / JavaScript (Frontend)

---

## Project Flow

1. Admin creates employee
2. User receives login credentials
3. User logs in and uploads documents
4. Documents are validated and stored in S3
5. Step Functions advances workflow:

   * Document → IT → Policy
6. HR is notified after completion

---

## Setup Instructions

1. Configure AWS services:

   * Create DynamoDB table (`employee`)
   * Create S3 bucket
   * Setup Cognito User Pool
   * Configure SES and SNS

2. Deploy Lambda functions:

   * registerEmployee
   * uploadDocument
   * checkDocument
   * updateIT
   * updatePolicy

3. Setup API Gateway routes

4. Deploy frontend (S3 static hosting)

---

## Output

* Fully working onboarding system
* Automated workflow using Step Functions
* Document upload and tracking
* Admin dashboard

---

## Author

Bharath

- Cognito login wiring (role-based: employee/admin via Cognito groups)
- Employee dashboard with onboarding progress and stage cards
- Document upload screen using pre-signed upload URLs
- HR dashboard with employee list, search, and pending-only filter

### Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Set in `.env`:

- `VITE_API_BASE_URL`
- `VITE_COGNITO_USER_POOL_ID`
- `VITE_COGNITO_APP_CLIENT_ID`

### API Routes Expected

- `GET /employee/{id}/status`
- `POST /generate-upload-url`
- `GET /admin/employees`

### S3 Static Hosting (Build)

```bash
cd frontend
npm run build
```

Upload `frontend/dist/` files to your static website S3 bucket.
Optionally front it with CloudFront for HTTPS and edge caching.
