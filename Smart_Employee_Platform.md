# Smart Employee Platform

AI-powered serverless employee management platform built on AWS.

The platform integrates:

* employee onboarding
* face recognition attendance
* leave management
* attendance analytics
* workflow automation
* admin reporting

into one unified cloud-native system.

---

# Features

## Employee Management

* Employee onboarding
* Employee profile management
* Document uploads
* Face registration

---

## Face Recognition Attendance

* Real-time webcam attendance
* Amazon Rekognition face matching
* Clock IN / Clock OUT workflow
* Confidence threshold validation
* Duplicate prevention

---

## Leave Management

* Apply leave
* Approve/reject leave
* Leave balance tracking
* Leave history

---

## Attendance Analytics

* Daily attendance logs
* Weekly attendance summaries
* Late employee detection
* Attendance percentage calculation

---

## Automation

* Automatic absent marking
* EventBridge scheduled workflows
* Analytics aggregation

---

# AWS Services Used

| Service               | Purpose                |
| --------------------- | ---------------------- |
| AWS Lambda            | Serverless backend     |
| API Gateway           | REST APIs              |
| DynamoDB              | Data storage           |
| Amazon Rekognition    | Face recognition       |
| Amazon S3             | Image/document storage |
| Amazon Cognito        | Authentication         |
| EventBridge Scheduler | Scheduled automation   |
| IAM                   | Security & permissions |
| CloudWatch            | Logging & monitoring   |

---

# Architecture

## Multi-Region Setup

### Hyderabad (ap-south-2)

Handles:

* onboarding
* employee management
* leave workflows

### Mumbai (ap-south-1)

Handles:

* attendance services
* Rekognition
* analytics
* scheduled automation

---

# Project Structure

```text id="1q2w3e"
project/
│
├── frontend/
│   ├── login.html
│   ├── dashboard.html
│   ├── styles.css
│   └── script.js
│
├── lambda/
│   ├── register-face/
│   ├── mark-attendance/
│   ├── weekly-summary/
│   ├── mark-absent/
│   └── upload-url/
│
├── docs/
│   ├── architecture-diagram.png
│   ├── technical-design-doc.pdf
│   └── aws-cost-sheet.pdf
│
└── README.md
```

---

# Attendance Workflow

```text id="4r5t6y"
Webcam Capture
      │
      ▼
Upload to S3
      │
      ▼
AWS Rekognition
      │
      ▼
Employee Match
      │
      ▼
Attendance Write
      │
      ▼
Dashboard Update
```

---

# APIs

| Endpoint          | Method | Description            |
| ----------------- | ------ | ---------------------- |
| /register         | POST   | Register employee face |
| /attendance       | POST   | Mark attendance        |
| /upload-url       | GET    | Generate S3 upload URL |
| /today-attendance | GET    | Get today's attendance |
| /weekly-summary   | GET    | Get analytics summary  |
| /apply-leave      | POST   | Apply leave            |
| /approve-leave    | POST   | Approve leave          |

---

# DynamoDB Tables

| Table          | Purpose              |
| -------------- | -------------------- |
| employee       | Employee master data |
| attendance     | Attendance logs      |
| leave_requests | Leave workflows      |
| leave_balances | Leave tracking       |
| leave_config   | Leave rules          |

---

# Security Features

* IAM least-privilege access
* S3 lifecycle cleanup policy
* S3 versioning enabled
* DynamoDB encryption
* Secure Rekognition integration
* Temporary attendance image storage

---

# Deployment Instructions

## 1. Clone Repository

```bash id="7u8i9o"
git clone <repository-url>
```

---

# 2. Configure AWS Services

Create:

* S3 bucket
* DynamoDB tables
* Rekognition collection
* Lambda functions
* API Gateway routes
* Cognito User Pool

---

# 3. Deploy Lambda Functions

Upload Lambda source code through:

* AWS Console
  or
* AWS CLI

---

# 4. Configure API Gateway

Create APIs:

* /attendance
* /register
* /upload-url
* /weekly-summary
* /today-attendance

Deploy to:

```text id="0p9l8k"
ap-south-1
```

---

# 5. Enable S3 Features

Enable:

* lifecycle rules
* bucket versioning
* static website hosting

---

# 6. Run Frontend

Open:

```text id="3j4h5g"
login.html
```

or host frontend using:

* S3 Static Website Hosting
* CloudFront

---

# Attendance Rules

| Scan Count  | Result   |
| ----------- | -------- |
| First scan  | IN       |
| Second scan | OUT      |
| More scans  | Rejected |

---

# Analytics Rules

## Late Attendance

Clock-IN after:

```text id="6u7i8o"
10:00 AM
```

is considered late.

---

# Scheduled Automation

## EventBridge Scheduler

Runs daily:

```text id="9p0l1k"
11:59 PM IST
```

Automatically:

* identifies absentees
* updates attendance table
* generates summaries

---

# Estimated Monthly Cost

For:

* 100 employees
* 2 scans/day

Approximate monthly cost:

```text id="2c3v4b"
₹750–₹950/month
```

---

# Future Enhancements

* Mobile app
* Payroll integration
* Geo-fencing
* QR backup attendance
* Amazon QuickSight dashboards
* Notification system
* HRMS integration

---

# Demo Workflow

1. Login to platform
2. Create employee
3. Register face
4. Open webcam attendance
5. Mark IN attendance
6. Mark OUT attendance
7. View analytics dashboard
8. Review leave workflows

---

# Conclusion

The Smart Employee Platform demonstrates a scalable serverless enterprise architecture using AWS managed services.

The platform successfully integrates:

* AI attendance
* onboarding
* automation
* analytics
* leave management
* admin reporting

into one unified cloud-native employee management solution.
