import os
from typing import Dict

import boto3
from botocore.exceptions import ClientError


TABLE_NAME = os.getenv("EMPLOYEES_TABLE", "employees")
ASSETS_TABLE_NAME = os.getenv("ASSETS_TABLE_NAME", "assets")
FROM_EMAIL = os.getenv("SES_FROM_EMAIL", "")
IT_ALERTS_TOPIC_ARN = os.getenv("IT_ALERTS_TOPIC_ARN", "")
HR_ALERTS_TOPIC_ARN = os.getenv("HR_ALERTS_TOPIC_ARN", "")
COMPANY_EMAIL_DOMAIN = os.getenv("COMPANY_EMAIL_DOMAIN", "company.com")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
assets_table = dynamodb.Table(ASSETS_TABLE_NAME)
ses = boto3.client("ses")
sns = boto3.client("sns")


def _get_employee(employee_id: str) -> Dict:
    result = table.get_item(Key={"employee_id": employee_id})
    return result.get("Item", {})


def _update_stages(employee_id: str, fields: Dict):
    set_parts = []
    expr_values = {}
    for idx, (field, value) in enumerate(fields.items(), start=1):
        token = f":v{idx}"
        set_parts.append(f"{field} = {token}")
        expr_values[token] = value

    table.update_item(
        Key={"employee_id": employee_id},
        UpdateExpression=f"SET {', '.join(set_parts)}",
        ExpressionAttributeValues=expr_values,
    )


def _publish_notification(subject: str, message: str):
    for topic_arn in [IT_ALERTS_TOPIC_ARN, HR_ALERTS_TOPIC_ARN]:
        if not topic_arn:
            continue
        try:
            sns.publish(TopicArn=topic_arn, Subject=subject, Message=message)
        except ClientError as exc:
            print(
                "SNS publish failed",
                exc.response.get("Error", {}).get("Message", "Unknown error"),
            )


def _build_corporate_email(name: str) -> str:
    user = ".".join(name.lower().strip().split())
    return f"{user}@{COMPANY_EMAIL_DOMAIN}"


def _assign_next_asset() -> str:
    try:
        response = assets_table.scan(
            FilterExpression="#st = :available",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":available": "Available"},
            Limit=1,
        )
        items = response.get("Items", [])
        if not items:
            return "LT-PENDING"

        asset_id = items[0]["asset_id"]
        assets_table.update_item(
            Key={"asset_id": asset_id},
            UpdateExpression="SET #st = :assigned",
            ExpressionAttributeNames={"#st": "status"},
            ExpressionAttributeValues={":assigned": "Assigned"},
        )
        return asset_id
    except ClientError as exc:
        print(
            "Asset assignment lookup failed",
            exc.response.get("Error", {}).get("Message", "Unknown error"),
        )
        return "LT-PENDING"


def check_documents(event, context):
    employee_id = event["employee_id"]
    employee = _get_employee(employee_id)

    documents_status = employee.get("documents_status", "Pending")
    complete = documents_status == "Complete"

    _update_stages(
        employee_id,
        {
            "documents_stage": "Complete" if complete else "In Progress",
            "overall_status": "20%" if complete else "10%",
        },
    )

    return {
        "employee_id": employee_id,
        "email": employee.get("email", event.get("email")),
        "complete": complete,
    }


def send_reminder(event, context):
    employee_id = event["employee_id"]
    employee = _get_employee(employee_id)
    to_email = employee.get("email", event.get("email"))

    if FROM_EMAIL and to_email:
        try:
            ses.send_email(
                Source=FROM_EMAIL,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": "Onboarding document reminder"},
                    "Body": {
                        "Text": {
                            "Data": (
                                "Please complete your pending onboarding documents "
                                "to continue your onboarding workflow."
                            )
                        }
                    },
                },
            )
        except ClientError as exc:
            print(
                "Reminder email failed",
                exc.response.get("Error", {}).get("Message", "Unknown error"),
            )

    return {"employee_id": employee_id, "email": to_email, "complete": False}


def it_provisioning(event, context):
    employee_id = event["employee_id"]
    employee = _get_employee(employee_id)
    email_id = _build_corporate_email(employee.get("name", "new.hire"))

    _update_stages(
        employee_id,
        {
            "it_stage": "Complete",
            "email_id": email_id,
            "vpn_ready": True,
            "chat_ready": True,
            "software_access": ["Jira", "GitHub", "HRMS"],
            "overall_status": "60%",
        },
    )
    return {
        "employee_id": employee_id,
        "email": event.get("email", employee.get("email")),
        "email_id": email_id,
    }


def assign_asset(event, context):
    employee_id = event["employee_id"]
    asset_id = _assign_next_asset()
    assigned = asset_id != "LT-PENDING"

    _update_stages(
        employee_id,
        {
            "asset_assigned": assigned,
            "asset_id": asset_id,
            "overall_status": "75%" if assigned else "65%",
        },
    )
    return {
        "employee_id": employee_id,
        "email": event.get("email"),
        "email_id": event.get("email_id"),
        "asset_id": asset_id,
    }


def policy_signoff(event, context):
    employee_id = event["employee_id"]
    employee = _get_employee(employee_id)
    to_email = employee.get("email", event.get("email"))

    if FROM_EMAIL and to_email:
        try:
            ses.send_email(
                Source=FROM_EMAIL,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": "Policy sign-off required"},
                    "Body": {
                        "Text": {
                            "Data": (
                                "Please review and sign the onboarding policy "
                                "documents to continue."
                            )
                        }
                    },
                },
            )
        except ClientError as exc:
            print(
                "Policy email failed",
                exc.response.get("Error", {}).get("Message", "Unknown error"),
            )

    _update_stages(employee_id, {"policy_stage": "Complete", "overall_status": "85%"})
    return {"employee_id": employee_id, "email": to_email}


def manager_intro(event, context):
    employee_id = event["employee_id"]
    employee = _get_employee(employee_id)
    to_email = employee.get("email", event.get("email"))

    if FROM_EMAIL and to_email:
        try:
            ses.send_email(
                Source=FROM_EMAIL,
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": "Manager introduction"},
                    "Body": {
                        "Text": {
                            "Data": (
                                "Your manager introduction will be scheduled shortly. "
                                "Welcome to the team."
                            )
                        }
                    },
                },
            )
        except ClientError as exc:
            print(
                "Manager intro email failed",
                exc.response.get("Error", {}).get("Message", "Unknown error"),
            )

    _update_stages(employee_id, {"manager_stage": "Complete", "overall_status": "95%"})
    return {"employee_id": employee_id, "email": to_email}


def mark_day1_ready(event, context):
    employee_id = event["employee_id"]
    employee = _get_employee(employee_id)

    documents_complete = employee.get("documents_status") == "Complete"
    it_complete = employee.get("it_stage") == "Complete"
    asset_assigned = bool(employee.get("asset_assigned"))
    policy_complete = employee.get("policy_stage") == "Complete"

    day1_ready = all([documents_complete, it_complete, asset_assigned, policy_complete])
    final_status = "Ready for Joining" if day1_ready else "Pending Actions"

    _update_stages(
        employee_id,
        {
            "day1_ready": day1_ready,
            "status": final_status,
            "overall_status": "100%" if day1_ready else "95%",
        },
    )

    if day1_ready:
        message = (
            f"Employee {employee.get('name', employee_id)} provisioning completed.\n"
            f"Laptop {employee.get('asset_id', 'NA')} assigned.\n"
            f"Email {employee.get('email_id', 'NA')} created."
        )
        _publish_notification("Employee provisioning completed", message)

        to_email = employee.get("email")
        if FROM_EMAIL and to_email:
            try:
                ses.send_email(
                    Source=FROM_EMAIL,
                    Destination={"ToAddresses": [to_email]},
                    Message={
                        "Subject": {"Data": "Your Day 1 setup is ready"},
                        "Body": {
                            "Text": {
                                "Data": (
                                    "Welcome!\n\n"
                                    "Your corporate account is ready.\n"
                                    f"Email: {employee.get('email_id', 'NA')}\n"
                                    f"Laptop: {employee.get('asset_id', 'NA')}\n"
                                    f"VPN: {'Enabled' if employee.get('vpn_ready') else 'Pending'}\n"
                                    f"Joining Status: {final_status}"
                                )
                            }
                        },
                    },
                )
            except ClientError as exc:
                print(
                    "Ready email failed",
                    exc.response.get("Error", {}).get("Message", "Unknown error"),
                )

    return {"employee_id": employee_id, "day1_ready": day1_ready, "status": final_status}

