import json
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError


BUCKET_NAME = os.getenv("DOCS_BUCKET_NAME", "smart-onboarding-docs")
TABLE_NAME = os.getenv("EMPLOYEES_TABLE", "employees")
URL_EXPIRY_SECONDS = int(os.getenv("UPLOAD_URL_EXPIRY_SECONDS", "300"))
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

ALLOWED_DOC_TYPES = {
    "id-proof": ["pdf", "jpg", "jpeg", "png"],
    "degree": ["pdf", "jpg", "jpeg", "png"],
    "offer-letter": ["pdf", "jpg", "jpeg", "png"],
    "pan-aadhaar": ["pdf", "jpg", "jpeg", "png"],  # Optional as per policy.
}

s3 = boto3.client("s3")
table = boto3.resource("dynamodb").Table(TABLE_NAME)


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _get_body(event: dict) -> dict:
    raw_body = event.get("body", "{}")
    return json.loads(raw_body) if isinstance(raw_body, str) else raw_body


def _parse_file_name(file_name: str) -> tuple[Optional[str], Optional[str]]:
    lowered = file_name.lower()
    if "." not in lowered:
        return None, None
    base, ext = lowered.rsplit(".", 1)
    return base, ext


def _validate_doc_metadata(file_name: str, file_size: int) -> tuple[bool, str]:
    base_name, extension = _parse_file_name(file_name)
    if not base_name or not extension:
        return False, "file_name must include an extension"

    if base_name not in ALLOWED_DOC_TYPES:
        return False, f"Unsupported document type: {base_name}"

    allowed_extensions = ALLOWED_DOC_TYPES[base_name]
    if extension not in allowed_extensions:
        return False, f"Unsupported file extension .{extension} for {base_name}"

    if file_size > MAX_FILE_SIZE_BYTES:
        return False, "File exceeds 5 MB limit"

    return True, "ok"


def generate_upload_url_handler(event, context):
    try:
        body = _get_body(event)
    except (TypeError, json.JSONDecodeError):
        return _response(400, {"message": "Invalid JSON body"})

    employee_id = body.get("employee_id")
    file_name = body.get("file_name")
    file_size = int(body.get("file_size", 0))
    content_type = body.get("content_type", "application/octet-stream")

    if not employee_id or not file_name:
        return _response(
            400, {"message": "employee_id and file_name are required fields"}
        )

    is_valid, reason = _validate_doc_metadata(file_name, file_size)
    if not is_valid:
        return _response(400, {"message": "Invalid document metadata", "error": reason})

    key = f"{employee_id}/{file_name}"
    try:
        url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=URL_EXPIRY_SECONDS,
        )
    except ClientError as exc:
        return _response(
            500,
            {
                "message": "Failed to generate upload URL",
                "error": exc.response.get("Error", {}).get("Message", "Unknown error"),
            },
        )

    return _response(
        200,
        {
            "upload_url": url,
            "key": key,
            "expires_in_seconds": URL_EXPIRY_SECONDS,
        },
    )


def get_employee_status_handler(event, context):
    employee_id = (event.get("pathParameters") or {}).get("id")
    if not employee_id:
        return _response(400, {"message": "employee id is required in path"})

    try:
        result = table.get_item(Key={"employee_id": employee_id})
    except ClientError as exc:
        return _response(
            500,
            {
                "message": "Failed to fetch employee status",
                "error": exc.response.get("Error", {}).get("Message", "Unknown error"),
            },
        )

    item = result.get("Item")
    if not item:
        return _response(404, {"message": "Employee not found"})

    return _response(
        200,
        {
            "employee_id": employee_id,
            "name": item.get("name"),
            "documents_status": item.get("documents_status", "Pending"),
            "uploaded_docs": item.get("uploaded_docs", []),
            "missing_docs": item.get("missing_docs", []),
            "last_upload_time": item.get("last_upload_time"),
            "status": item.get("status"),
        },
    )


