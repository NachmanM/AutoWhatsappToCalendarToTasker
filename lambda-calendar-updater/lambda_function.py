import json
import logging
import os
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Google Auth for Calendar
from google.oauth2 import service_account
from googleapiclient.discovery import build
from botocore.exceptions import ClientError

# --- Configuration ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)

SECRET_NAME = os.environ.get("SECRET_NAME", "Secret-for-Set-home-or-afeka-With-Whatsapp-Gemini-Calendar")
REGION_NAME = os.environ.get("AWS_REGION", "us-east-1")
CALENDAR_ID = "c8cd5d56e9bb6d244670b112aa68015b79321b3f5725bf8385fce6c4292deaca@group.calendar.google.com" 
BUCKET_NAME = "docker-volume-nachman"

s3_client = boto3.client('s3')

def get_secrets() -> Dict[str, Any]:
    """Retrieves Google Credentials from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=REGION_NAME)

    try:
        response = client.get_secret_value(SecretId=SECRET_NAME)
        # Parse the inner JSON string if your secret is nested
        secret_string = response['SecretString']
        try:
            data = json.loads(secret_string)
            # If your secret is double-nested (common in AWS console), unwrap it
            if 'Secret-for-Set-home-or-afeka-With-Whatsapp-Gemini-Calendar' in data:
                 return json.loads(data['Secret-for-Set-home-or-afeka-With-Whatsapp-Gemini-Calendar'])
            return data
        except json.JSONDecodeError:
            return secret_string # Fallback if it's just a raw string
            
    except ClientError as e:
        logger.error(f"Failed to retrieve secrets: {e}")
        raise e

def get_data_from_s3(bucket: str, key: str) -> List[Dict]:
    """Reads the JSON schedule file directly from S3."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8').strip()
        logger.info(f"Read content from S3: {content}")
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()
        return json.loads(content)
    except Exception as e:
        logger.error(f"Failed to read S3 object {key} from {bucket}: {e}")
        raise e

def update_google_calendar(service_account_info: Dict, calendar_id: str, schedule_data: List[Dict]):
    """Updates Google Calendar with All-Day events, checking for duplicates."""
    if not schedule_data:
        logger.info("No schedule data found in file.")
        return

    try:
        # Check if the service account info is a string (JSON) or dict
        if isinstance(service_account_info, str):
            service_account_info = json.loads(service_account_info)
        else:
            logger.info(f"Did not load service_account_info, beacause it is not a str")
        
        bot_email = service_account_info.get('client_email')
        logger.info(f"🤖 BOT LOGGING IN AS: {bot_email}")
        logger.info(f"📅 TRYING TO UPDATE CALENDAR ID: {calendar_id}")

        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=creds)

        for entry in schedule_data:
            date_str = entry.get('date')
            location = entry.get('location')
            
            if not date_str or not location:
                continue

            # 1. Check for duplicates to prevent spamming calendar
            time_min = f"{date_str}T00:00:00Z"
            time_max = f"{date_str}T23:59:59Z"
            
            events_result = service.events().list(
                calendarId=calendar_id, 
                timeMin=time_min, 
                timeMax=time_max,
                singleEvents=True, 
                q=location 
            ).execute()
            
            existing_events = events_result.get('items', [])
            
            if existing_events:
                logger.info(f"Event '{location}' already exists for {date_str}. Skipping.")
                continue

            # 2. Create Event
            # Google Calendar All-Day events require start date YYYY-MM-DD and end date (start + 1 day)
            start_date = datetime.strptime(date_str, "%Y-%m-%d")
            end_date = start_date + timedelta(days=1)
            
            event_body = {
                'summary': f"Study: {location}", # Added prefix for clarity
                'start': {'date': date_str},
                'end': {'date': end_date.strftime("%Y-%m-%d")},
                'description': 'Auto-added from WhatsApp Schedule Analysis',
                'transparency': 'transparent' # Show as "Free" so it doesn't block meetings, or remove for "Busy"
            }
            
            service.events().insert(calendarId=calendar_id, body=event_body).execute()
            logger.info(f"✅ Added {location} on {date_str}")

    except Exception as e:
        logger.error(f"Google Calendar API Error: {e}")
        raise e

# --- Main Handler ---
def lambda_handler(event, context):
    logger.info("Starting S3 Event Handler")
    logger.info(f"Received Event: {json.dumps(event)}")

    try:
        # 1. Get Secrets (Only need Google Creds now)
        secrets = get_secrets()
        google_creds = secrets.get('google_service_account_json')
        
        if not google_creds:
            raise ValueError("google_service_account_json not found in secrets.")

        # 2. Parse S3 Event
        # S3 trigger events are list of records
        for record in event.get('Records', []):
            bucket_name = BUCKET_NAME
            file_key = record['s3']['object']['key']
            
            logger.info(f"Processing file: {file_key} from bucket: {bucket_name}")

            # 3. Read JSON from S3
            schedule_data = get_data_from_s3(bucket_name, file_key)

            # 4. Update Calendar
            update_google_calendar(google_creds, CALENDAR_ID, schedule_data)

        return {"statusCode": 200, "body": "Calendar updated successfully"}

    except Exception as e:
        logger.error(f"Lambda Execution Failed: {e}")
        return {"statusCode": 500, "body": str(e)}
