# Smart Onboarding

Day 1+ implementation for **Foundation + Employee Identity Core**.

## Project Structure

```text
smart-onboarding/
│── frontend/
│── backend/
│   │── register_employee.py
│   │── create_user.py
│   │── upload_docs.py
│   │── validate_document.py
│   │── workflow_handlers.py
│   │── stepfunctions_onboarding_flow.json
│── docs/
│   │── day1-aws-setup.md
│   │── day3-doc-upload.md
│── README.md
```

## Current Goal

Create employee registration and account bootstrap flow:

`HR Form -> API Gateway -> Lambda -> DynamoDB + Cognito + SES`

## Lambda: `registerEmployee`

Source file: `backend/register_employee.py`

Responsibilities:
- receives employee form data
- generates UUID
- stores record in DynamoDB table `employees`
- creates Cognito user with temporary password
- sends welcome email via SES
- returns:
  - `message: "Employee registered and account created"`
  - generated `employee_id`

## Deploy Quick Steps

1. Create DynamoDB table `employees` with partition key `employee_id` (String).
2. Create Lambda function `registerEmployee` (Python 3.11/3.12) and paste code from `backend/register_employee.py`.
3. Create Cognito User Pool `smart-onboarding-users`:
   - enable email sign-in
   - enable self password reset
   - allow temporary passwords
   - create custom attribute `employee_id`
   - save `UserPoolId` and `AppClientId`
4. Verify sender email in Amazon SES (sandbox-safe):
   - `hr@yourcompany.com` (or your verified test Gmail)
5. Set Lambda environment variables:
   - `EMPLOYEES_TABLE=employees`
   - `COGNITO_USER_POOL_ID=<your_user_pool_id>`
   - `SES_FROM_EMAIL=<verified_sender_email>`
6. Attach IAM permissions to Lambda execution role:
   - `dynamodb:PutItem` on `employees`
   - `cognito-idp:AdminCreateUser` on your user pool
   - `ses:SendEmail` on your sender identity
   - CloudWatch logs permissions
7. Create API Gateway endpoint:
   - `POST /register`
   - Integration target: Lambda `registerEmployee`
8. Deploy API and copy invoke URL.
9. Test with Postman using the sample payload in `docs/day1-aws-setup.md`.

## Expected Result

- DynamoDB table created
- Lambda executes all downstream actions
- API Gateway endpoint works
- Employee record is stored in `employees`
- Cognito account is created with temporary password
- Welcome email is sent to employee

## Day 3 Document Upload APIs

### 1) Generate Upload URL

- Endpoint: `POST /generate-upload-url`
- Lambda handler: `backend/upload_docs.generate_upload_url_handler`
- Input:
  - `employee_id`
  - `file_name` (e.g. `id-proof.pdf`, `degree.jpg`, `offer-letter.pdf`, `pan-aadhaar.pdf`)
  - `file_size` (bytes)
  - `content_type` (recommended)
- Output:
  - pre-signed S3 `upload_url` (expires in 5 minutes by default)

### 2) Employee Document Status

- Endpoint: `GET /employee/{id}/status`
- Lambda handler: `backend/upload_docs.get_employee_status_handler`
- Output:
  - `documents_status`
  - `uploaded_docs`
  - `missing_docs`
  - `last_upload_time`
  - onboarding `status`

### 3) S3 Upload Validation + Progress Update

- Lambda file: `backend/validate_document.py`
- Trigger: S3 `ObjectCreated:*` on bucket `smart-onboarding-docs`
- Behavior:
  - validates extension (`pdf/jpg/jpeg/png`) and max size (5MB)
  - updates DynamoDB document progress
  - sets:
    - `documents_status = In Progress` on partial upload
    - `documents_status = Complete` + `status = Documents Verified` when required docs complete
  - sends SNS notification to HR topic when all required docs are complete

## Day 4 Workflow Automation (Step Functions)

### State Machine

- Name: `smart-onboarding-flow`
- Type: Standard workflow
- Definition file: `backend/stepfunctions_onboarding_flow.json`
- Reminder loop:
  - if documents incomplete -> wait 24 hours -> send reminder -> recheck

### Required Workflow Lambdas

All handlers are in `backend/workflow_handlers.py`:

- `check_documents`
- `send_reminder`
- `it_provisioning`
- `assign_asset`
- `policy_signoff`
- `manager_intro`
- `mark_day1_ready`

### Auto Start on Employee Registration

`backend/register_employee.py` now starts Step Functions after successful employee + account creation.

Set this env var on registration Lambda:
- `ONBOARDING_STATE_MACHINE_ARN=<your_state_machine_arn>`

### DynamoDB Stage Fields Used

- `documents_stage`
- `it_stage`
- `policy_stage`
- `manager_stage`
- `overall_status`
- `workflow_execution_id`

## Day 5 IT Provisioning + Ready Automation

### Employee IT Fields

The employee item now tracks:

- `email_id`
- `vpn_ready`
- `chat_ready`
- `asset_assigned`
- `asset_id`
- `software_access`
- `day1_ready`

### Step Functions Stage Order

`Documents -> IT Provisioning -> Asset Assignment -> Policy Signoff -> Manager Intro -> Ready`

### Assets Inventory (optional table)

Use DynamoDB table `assets` with schema:
- partition key: `asset_id` (String)
- sample attributes: `type`, `status` (`Available` / `Assigned`)

`assign_asset` picks an available asset and marks it assigned.

### Notifications

When `mark_day1_ready` determines all gates are complete, it:
- sets `day1_ready = true`
- updates `status = Ready for Joining`
- publishes completion notification to IT/HR SNS topics
- sends final readiness email to employee

## Day 6 Frontend (React)

Frontend app is in `frontend/` with:

- `src/pages/Login.jsx`
- `src/pages/EmployeeDashboard.jsx`
- `src/pages/UploadDocs.jsx`
- `src/pages/AdminDashboard.jsx`
- `src/components/Navbar.jsx`
- `src/components/ProgressBar.jsx`
- `src/components/StatusCard.jsx`

### Features Implemented

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
