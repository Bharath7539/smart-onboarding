# Day 3 AWS Setup (Secure Document Upload)

## 1) Create S3 Bucket

- Bucket name: `smart-onboarding-docs`
- Settings:
  - Block public access: ON
  - Default encryption: ON
  - Versioning: recommended

Key layout:
- `<employee_id>/id-proof.pdf`
- `<employee_id>/degree.pdf`
- `<employee_id>/offer-letter.pdf`
- `<employee_id>/pan-aadhaar.pdf` (optional)

## 2) DynamoDB Document Attributes

Store these fields in `employees` items:
- `documents_status` (`Pending | In Progress | Complete`)
- `uploaded_docs` (String list)
- `missing_docs` (String list)
- `last_upload_time` (ISO datetime)

Initial state (set during registration):
- `documents_status: Pending`
- `uploaded_docs: []`
- `missing_docs: ["degree", "id-proof", "offer-letter"]`

## 3) Lambda: Generate Upload URL

- File: `backend/upload_docs.py`
- Handler: `generate_upload_url_handler`
- API route: `POST /generate-upload-url`

Environment variables:
- `DOCS_BUCKET_NAME=smart-onboarding-docs`
- `EMPLOYEES_TABLE=employees`
- `UPLOAD_URL_EXPIRY_SECONDS=300`

Request body:
```json
{
  "employee_id": "uuid-value",
  "file_name": "id-proof.pdf",
  "file_size": 2048000,
  "content_type": "application/pdf"
}
```

## 4) Lambda: Validate Uploads

- File: `backend/validate_document.py`
- Handler: `lambda_handler`
- Trigger: S3 Event `ObjectCreated:*` on bucket `smart-onboarding-docs`

Validation rules:
- Allowed extensions: `pdf`, `jpg`, `jpeg`, `png`
- Max size: 5 MB
- Required docs: `id-proof`, `degree`, `offer-letter`
- Optional docs: `pan-aadhaar`

Progress logic:
- partial uploads -> `documents_status = In Progress`
- all required docs uploaded -> `documents_status = Complete`, `status = Documents Verified`

## 5) HR Notification (SNS)

- Topic name: `hr-onboarding-alerts`
- Lambda env var:
  - `HR_ALERTS_TOPIC_ARN=<sns-topic-arn>`

When required docs are complete, Lambda sends an SNS message:
- `Employee <name> (<employee_id>) has submitted all required onboarding documents.`

## 6) IAM Permissions

For generate URL Lambda:
- `s3:PutObject` (for pre-signed URL workflow policy scope)
- `s3:GetObject` (optional if later read checks are added)
- `dynamodb:GetItem` (for status endpoint)

For validation Lambda:
- `dynamodb:GetItem`
- `dynamodb:UpdateItem`
- `sns:Publish`

Plus CloudWatch Logs permissions for both.
