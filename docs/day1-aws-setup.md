# Day 1+ AWS Setup (Registration + Identity Bootstrap)

## 1) Create DynamoDB Table

- Table name: `employees`
- Partition key: `employee_id` (String)
- Billing mode: On-demand (recommended for early stage)

### AWS CLI (optional)
```bash
aws dynamodb create-table \
  --table-name employees \
  --attribute-definitions AttributeName=employee_id,AttributeType=S \
  --key-schema AttributeName=employee_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## 2) Create Cognito User Pool

Create user pool: `smart-onboarding-users`

Enable:
- Email sign in
- Self password reset
- Temporary password flow

Create custom attribute:
- `employee_id`

Save:
- `UserPoolId`
- `AppClientId`

## 3) Verify Email in SES

Verify sender identity:
- `hr@yourcompany.com` (or a verified Gmail while in SES sandbox)

## 4) Create Lambda Function (`registerEmployee`)

Runtime: Python 3.12 (or 3.11)

Handler:
- file: `register_employee.py`
- function: `lambda_handler`

Environment variables:
- `EMPLOYEES_TABLE=employees`
- `COGNITO_USER_POOL_ID=<your_user_pool_id>`
- `SES_FROM_EMAIL=<verified_sender_email>`

IAM permissions required for Lambda role:
- `dynamodb:PutItem` on table `employees`
- `cognito-idp:AdminCreateUser` on user pool `smart-onboarding-users`
- `ses:SendEmail` for sender identity
- CloudWatch Logs basic execution policy

## 5) Create API Gateway

Create HTTP API or REST API with endpoint:
- `POST /register`

Integration:
- Connect `POST /register` to Lambda `registerEmployee`

Enable CORS if the frontend will call the API directly from browser.

## 6) Test in Postman

Method: `POST`

URL:
`https://<api-id>.execute-api.<region>.amazonaws.com/register`

Headers:
- `Content-Type: application/json`

Body:
```json
{
  "name": "Bharath",
  "email": "bharath@gmail.com",
  "department": "IT",
  "role": "Developer",
  "manager": "Rahul",
  "joining_date": "2026-05-01",
  "employment_type": "Full-Time"
}
```

Expected response:
```json
{
  "message": "Employee registered and account created",
  "employee_id": "uuid-value"
}
```

Outcome:
- Employee row saved in DynamoDB
- Cognito user created with temporary password
- Welcome email sent through SES
