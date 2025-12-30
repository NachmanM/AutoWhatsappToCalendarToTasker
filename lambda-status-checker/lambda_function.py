import json
import os
import logging
import datetime
import boto3
from botocore.exceptions import ClientError
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configure Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Configuration ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SECRET_NAME = os.environ.get('SECRET_NAME', 'Google-Calendar-API-Key')
SECRET_HEADER = 'SECRET_HEADER'
REGION_NAME = "us-east-1" # Ensure this matches your AWS Region

def get_secret(secret_name):
    """Retrieves the secret from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=REGION_NAME)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        logger.error(f"Unable to retrieve secret: {e}")
        raise e

    if 'SecretString' in get_secret_value_response:
        return get_secret_value_response['SecretString']
    return base64.b64decode(get_secret_value_response['SecretBinary'])

def get_google_creds():
    """Robust credential retrieval (handles wrapped/unwrapped secrets)."""
    try:
        secret_content = get_secret(SECRET_NAME)
        try:
            data = json.loads(secret_content)
        except json.JSONDecodeError:
            logger.error(f"Secret is not valid JSON.")
            raise

        required_keys = ["type", "project_id", "private_key", "client_email"]
        
        def is_valid_cred(d):
            if not isinstance(d, dict): return False
            return all(k in d for k in required_keys)

        final_creds = None
        if is_valid_cred(data):
            final_creds = data
        else:
            for key, value in data.items():
                if isinstance(value, dict) and is_valid_cred(value):
                    final_creds = value
                    break
                elif isinstance(value, str):
                    try:
                        nested = json.loads(value)
                        if is_valid_cred(nested):
                            final_creds = nested
                            break
                    except: continue

        if not final_creds:
            raise ValueError("Could not find valid Google Credentials in Secret.")

        return service_account.Credentials.from_service_account_info(
            final_creds, scopes=SCOPES
        )

    except Exception as e:
        logger.error(f"Credential Error: {e}")
        raise

def check_calendar_status():
    """Checks the current event on the calendar."""
    creds = get_google_creds()
    service = build('calendar', 'v3', credentials=creds)
    calendar_id = os.environ.get('CALENDAR_ID', 'primary')

    # Get current time in UTC
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=1,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])

    if not events:
        return "NO_EVENT"

    # Strict check: Is 'now' actually inside the event duration?
    # (Optional: You can remove this if you just want the 'next' event)
    event = events[0]
    # start = event['start'].get('dateTime', event['start'].get('date'))
    # end = event['end'].get('dateTime', event['end'].get('date'))
    # logic to compare timestamps could go here if needed.
    return event.get('summary', '')

def lambda_handler(event, context):
    logger.info("Function started (Calendar Check Only).")

    logger.info(get_secret(SECRET_HEADER))
    EXPECTED_SECRET = json.loads(get_secret(SECRET_HEADER))[SECRET_HEADER]
    
    # Check for the custom header in the 'headers' object
    actual_secret = event.get('headers', {}).get('x-secret-header')

    if actual_secret != EXPECTED_SECRET:
        return {
            'statusCode': 403,
            'body': 'Unauthorized'
        }

    # 1. Check Calendar
    try:
        current_event_title = check_calendar_status()
        logger.info(f"Current Calendar Event: {current_event_title}")
    except Exception as e:
        logger.error(f"Calendar check failed: {e}")
        # Fail safe: Do NOT trigger location sharing if error
        return {'statusCode': 200, 'body': json.dumps({'trigger': False, 'error': str(e)})}

    # 2. Logic Decision
    title_lower = current_event_title.lower()
    should_share = False

    if "afeka" in title_lower or "college" in title_lower:
        should_share = True

    if "home" in title_lower:
        should_share = False

    # 3. Return JSON for Tasker
    response = {
        'trigger': should_share,
        'reason': current_event_title
    }

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(response)
    }