import os
import urllib.parse
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


TABLE_NAME = os.getenv("EMPLOYEES_TABLE", "employees")
HR_ALERTS_TOPIC_ARN = os.getenv("HR_ALERTS_TOPIC_ARN", "")
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

REQUIRED_DOCS = {"id-proof", "degree", "offer-letter"}
OPTIONAL_DOCS = {"pan-aadhaar"}
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
sns = boto3.client("sns")


def _parse_key(key: str):
    parts = key.split("/")
    if len(parts) != 2:
        return None, None
    return parts[0], parts[1]


def _parse_document_name(file_name: str):
    lowered = file_name.lower()
    if "." not in lowered:
        return None, None
    base, ext = lowered.rsplit(".", 1)
    return base, ext


def _publish_hr_notification(employee_name: str, employee_id: str):
    if not HR_ALERTS_TOPIC_ARN:
        return
    sns.publish(
        TopicArn=HR_ALERTS_TOPIC_ARN,
        Subject="Onboarding documents complete",
        Message=(
            f"Employee {employee_name} ({employee_id}) has submitted all required "
            "onboarding documents."
        ),
    )


def lambda_handler(event, context):
    records = event.get("Records", [])
    for record in records:
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        size = int(record["s3"]["object"].get("size", 0))
        employee_id, file_name = _parse_key(key)
        if not employee_id or not file_name:
            print(f"Skipping invalid object key format: {key}")
            continue

        doc_name, extension = _parse_document_name(file_name)
        if not doc_name or not extension:
            print(f"Skipping unsupported file naming for key: {key}")
            continue

        if extension not in ALLOWED_EXTENSIONS:
            print(f"Skipping disallowed extension for key: {key}")
            continue

        if doc_name not in REQUIRED_DOCS and doc_name not in OPTIONAL_DOCS:
            print(f"Skipping unknown document type for key: {key}")
            continue

        if size > MAX_FILE_SIZE_BYTES:
            print(f"File too large (>5MB), key={key}, size={size}")
            continue

        try:
            current = table.get_item(Key={"employee_id": employee_id}).get("Item", {})
            uploaded_docs = set(current.get("uploaded_docs", []))
            uploaded_docs.add(file_name)

            uploaded_doc_types = {doc.rsplit(".", 1)[0].lower() for doc in uploaded_docs}
            missing_docs = sorted(REQUIRED_DOCS - uploaded_doc_types)
            docs_status = "Complete" if not missing_docs else "In Progress"
            employee_status = (
                "Documents Verified" if docs_status == "Complete" else current.get("status")
            )

            update_values = {
                ":uploaded_docs": sorted(uploaded_docs),
                ":missing_docs": missing_docs,
                ":documents_status": docs_status,
                ":last_upload_time": datetime.now(timezone.utc).isoformat(),
                ":status": employee_status,
            }

            table.update_item(
                Key={"employee_id": employee_id},
                UpdateExpression=(
                    "SET uploaded_docs = :uploaded_docs, "
                    "missing_docs = :missing_docs, "
                    "documents_status = :documents_status, "
                    "last_upload_time = :last_upload_time, "
                    "#status = :status"
                ),
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues=update_values,
            )

            if docs_status == "Complete":
                _publish_hr_notification(
                    employee_name=current.get("name", "Unknown"), employee_id=employee_id
                )
        except ClientError as exc:
            print(
                "Failed to process document",
                key,
                exc.response.get("Error", {}).get("Message", "Unknown error"),
            )

    return {"statusCode": 200, "body": "Processed S3 upload events"}

