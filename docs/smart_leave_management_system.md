# Smart Leave Management System

## Overview

A serverless leave management and approval workflow built using AWS services.

### Core AWS Services Used

* AWS Lambda
* AWS Step Functions
* Amazon DynamoDB
* Amazon SES
* Amazon API Gateway
* Amazon S3
* Amazon Cognito
* Amazon EventBridge

---

# Architecture Flow

```text
Employee Applies Leave
        ↓
API Gateway
        ↓
ApplyLeave Lambda
        ↓
DynamoDB (leave_requests)
        ↓
AWS Step Functions
        ↓
Manager Approval Email (SES)
        ↓
Approve/Reject via Email Link
        ↓
Step Function Callback
        ↓
(Optional HR Approval if >5 days)
        ↓
Finalize Leave
        ↓
Update Leave Balances
        ↓
Employee Notification Email
```

---

# DynamoDB Schema

## 1. leave_requests

Stores employee leave requests.

### Partition Key

* `employee_id`

### Sort Key

* `request_id`

### Sample Item

```json
{
  "employee_id": "emp001",
  "request_id": "req001",
  "leave_type": "sick",
  "start_date": "2026-05-10",
  "end_date": "2026-05-12",
  "days": 3,
  "reason": "Fever",
  "status": "PENDING",
  "created_at": "2026-05-07T10:00:00Z"
}
```

---

## 2. leave_balances

Stores leave balances for each employee.

### Partition Key

* `employee_id`

### Sample Item

```json
{
  "employee_id": "emp001",
  "sick": 10,
  "casual": 5,
  "earned": 12
}
```

---

## 3. employee

Stores employee details.

### Partition Key

* `employee_id`

### Sample Item

```json
{
  "employee_id": "emp001",
  "name": "Bharath",
  "email": "employee@gmail.com",
  "manager_email": "manager@gmail.com",
  "department": "Engineering"
}
```

---

## 4. leave_config

Stores configurable leave rules.

### Partition Key

* `leave_type`

### Sample Item

```json
{
  "leave_type": "sick",
  "annual_quota": 10
}
```

---

# Step Functions State Machine Definition

```json
{
  "StartAt": "ManagerApproval",
  "States": {

    "ManagerApproval": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": {
        "FunctionName": "sendApprovalEmail",
        "Payload": {
          "employee_id.$": "$.employee_id",
          "request_id.$": "$.request_id",
          "level": "MANAGER",
          "taskToken.$": "$$.Task.Token"
        }
      },
      "ResultPath": "$.approvalResult",
      "Next": "CheckManagerDecision"
    },

    "CheckManagerDecision": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.approvalResult.status",
          "StringEquals": "APPROVED",
          "Next": "CheckHRNeeded"
        },
        {
          "Variable": "$.approvalResult.status",
          "StringEquals": "REJECTED",
          "Next": "NotifyRejected"
        }
      ]
    },

    "CheckHRNeeded": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.days",
          "NumericGreaterThan": 5,
          "Next": "HRApproval"
        }
      ],
      "Default": "FinalizeLeave"
    },

    "HRApproval": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
      "Parameters": {
        "FunctionName": "sendApprovalEmail",
        "Payload": {
          "employee_id.$": "$.employee_id",
          "request_id.$": "$.request_id",
          "level": "HR",
          "taskToken.$": "$$.Task.Token"
        }
      },
      "ResultPath": "$.hrApprovalResult",
      "Next": "CheckHRDecision"
    },

    "CheckHRDecision": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.hrApprovalResult.status",
          "StringEquals": "APPROVED",
          "Next": "FinalizeLeave"
        },
        {
          "Variable": "$.hrApprovalResult.status",
          "StringEquals": "REJECTED",
          "Next": "NotifyRejected"
        }
      ]
    },

    "FinalizeLeave": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-south-2:ACCOUNT_ID:function:finalizeLeave",
      "Parameters": {
        "employee_id.$": "$.employee_id",
        "request_id.$": "$.request_id",
        "leave_type.$": "$.leave_type",
        "days.$": "$.days"
      },
      "ResultPath": "$.finalizeResult",
      "Next": "NotifyApproved"
    },

    "NotifyApproved": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "sendEmployeeNotification",
        "Payload": {
          "employee_id.$": "$.employee_id",
          "status": "APPROVED"
        }
      },
      "ResultPath": "$.notifyApprovedResult",
      "End": true
    },

    "NotifyRejected": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "sendEmployeeNotification",
        "Payload": {
          "employee_id.$": "$.employee_id",
          "status": "REJECTED"
        }
      },
      "ResultPath": "$.notifyRejectedResult",
      "Next": "RejectLeave"
    },

    "RejectLeave": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:ap-south-2:ACCOUNT_ID:function:rejectLeave",
      "Parameters": {
        "employee_id.$": "$.employee_id",
        "request_id.$": "$.request_id"
      },
      "Next": "Rejected"
    },

    "Rejected": {
      "Type": "Succeed"
    }
  }
}
```

---

# Lambda Functions

| Lambda Function          | Purpose                           |
| ------------------------ | --------------------------------- |
| applyLeave               | Create leave request              |
| sendApprovalEmail        | Send approval/rejection email     |
| approveLeave             | Resume Step Function via callback |
| finalizeLeave            | Deduct balance and approve leave  |
| rejectLeave              | Update rejected status            |
| sendEmployeeNotification | Notify employee via SES           |

---

# API Endpoints

| Method | Endpoint     | Purpose              |
| ------ | ------------ | -------------------- |
| POST   | /apply-leave | Apply leave          |
| GET    | /approve     | Approve/reject leave |

---

# Key Features

* Serverless architecture
* Multi-level approval workflow
* SES email integration
* Callback-based approvals using Step Functions
* Leave overlap detection
* Leave balance validation
* HR approval for long-duration leaves
* Employee email notifications
* DynamoDB-based persistence

---

# Future Enhancements

* Team absence calendar
* Carry-forward leave balances
* EventBridge scheduled reports
* Downloadable leave reports
* Slack/MS Teams notifications
* JWT signed approval links

---

# Demo Flow

1. Employee logs in
2. Employee applies for leave
3. Request stored in DynamoDB
4. Manager receives email
5. Manager approves/rejects using email link
6. HR approval triggered for >5 days
7. Leave balance updated
8. Employee receives final notification email

---

# Repository Structure

```text
smart-leave-management/
│
├── frontend/
├── lambdas/
│   ├── applyLeave/
│   ├── approveLeave/
│   ├── finalizeLeave/
│   ├── rejectLeave/
│   ├── sendApprovalEmail/
│   └── sendEmployeeNotification/
│
├── stepfunctions/
│   └── leave-workflow.json
│
├── docs/
│   ├── architecture.md
│   ├── screenshots/
│   └── edge-cases.md
│
└── README.md
```
