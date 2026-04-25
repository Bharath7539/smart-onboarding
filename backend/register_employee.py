import json
import os
import secrets
import string
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


TABLE_NAME = os.getenv("EMPLOYEES_TABLE", "employees")
USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
FROM_EMAIL = os.getenv("SES_FROM_EMAIL", "")
STATE_MACHINE_ARN = os.getenv("ONBOARDING_STATE_MACHINE_ARN", "")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
cognito = boto3.client("cognito-idp")
ses = boto3.client("ses")
stepfunctions = boto3.client("stepfunctions")

REQUIRED_FIELDS = [
    "name",
    "email",
    "department",
    "role",
    "manager",
    "joining_date",
    "employment_type",
]


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _generate_temporary_password(length: int = 12) -> str:
    # Cognito temp passwords must include lowercase, uppercase, number, and symbol.
    lower = secrets.choice(string.ascii_lowercase)
    upper = secrets.choice(string.ascii_uppercase)
    number = secrets.choice(string.digits)
    symbol = secrets.choice("@#$%^&*()-_+=!")
    remaining = "".join(
        secrets.choice(string.ascii_letters + string.digits + "@#$%^&*()-_+=!")
        for _ in range(length - 4)
    )
    password = lower + upper + number + symbol + remaining
    shuffled = list(password)
    secrets.SystemRandom().shuffle(shuffled)
    return "".join(shuffled)


def lambda_handler(event, context):
    if not USER_POOL_ID or not FROM_EMAIL:
        return _response(
            500,
            {
                "message": "Missing required Lambda environment variables",
                "required": ["COGNITO_USER_POOL_ID", "SES_FROM_EMAIL"],
            },
        )

    try:
        raw_body = event.get("body", "{}")
        body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except (TypeError, json.JSONDecodeError):
        return _response(400, {"message": "Invalid JSON body"})

    missing = [field for field in REQUIRED_FIELDS if not body.get(field)]
    if missing:
        return _response(
            400,
            {"message": "Missing required fields", "missing_fields": missing},
        )

    employee_id = str(uuid.uuid4())
    email = body["email"]
    temp_password = _generate_temporary_password()
    item = {
        "employee_id": employee_id,
        "name": body["name"],
        "email": email,
        "department": body["department"],
        "role": body["role"],
        "manager": body["manager"],
        "joining_date": body["joining_date"],
        "employment_type": body["employment_type"],
        "status": "Registered",
        "documents_status": "Pending",
        "uploaded_docs": [],
        "missing_docs": ["degree", "id-proof", "offer-letter"],
        "last_upload_time": None,
        "documents_stage": "Pending",
        "it_stage": "Pending",
        "policy_stage": "Pending",
        "manager_stage": "Pending",
        "email_id": None,
        "vpn_ready": False,
        "chat_ready": False,
        "asset_assigned": False,
        "asset_id": None,
        "software_access": [],
        "day1_ready": False,
        "overall_status": "0%",
        "workflow_execution_id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        table.put_item(Item=item)
    except ClientError as exc:
        return _response(
            500,
            {
                "message": "Failed to store employee",
                "error": exc.response.get("Error", {}).get("Message", "Unknown error"),
            },
        )

    try:
        cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            TemporaryPassword=temp_password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "custom:employee_id", "Value": employee_id},
            ],
            MessageAction="SUPPRESS",
        )
    except ClientError as exc:
        return _response(
            500,
            {
                "message": "Employee saved but Cognito user creation failed",
                "employee_id": employee_id,
                "error": exc.response.get("Error", {}).get("Message", "Unknown error"),
            },
        )

    welcome_text = (
        "Welcome aboard!\n\n"
        f"Username: {email}\n"
        f"Temporary Password: {temp_password}\n\n"
        "Please log in and change your password at first sign-in."
    )

    try:
        ses.send_email(
            Source=FROM_EMAIL,
            Destination={"ToAddresses": [email]},
            Message={
                "Subject": {"Data": "Welcome to Company"},
                "Body": {"Text": {"Data": welcome_text}},
            },
        )
    except ClientError as exc:
        return _response(
            500,
            {
                "message": "Employee and Cognito user created, but email delivery failed",
                "employee_id": employee_id,
                "error": exc.response.get("Error", {}).get("Message", "Unknown error"),
            },
        )

    workflow_execution_id = None
    if STATE_MACHINE_ARN:
        try:
            execution = stepfunctions.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                input=json.dumps({"employee_id": employee_id, "email": email}),
            )
            workflow_execution_id = execution.get("executionArn")
            table.update_item(
                Key={"employee_id": employee_id},
                UpdateExpression="SET workflow_execution_id = :execution_arn",
                ExpressionAttributeValues={":execution_arn": workflow_execution_id},
            )
        except ClientError as exc:
            return _response(
                500,
                {
                    "message": "Employee created but onboarding workflow start failed",
                    "employee_id": employee_id,
                    "error": exc.response.get("Error", {}).get("Message", "Unknown error"),
                },
            )

    return _response(
        200,
        {
            "message": "Employee registered and account created",
            "employee_id": employee_id,
            "workflow_execution_id": workflow_execution_id,
        },
    )
