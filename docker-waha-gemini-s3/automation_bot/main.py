
import os
import requests
import boto3
import subprocess
import json
import glob
from datetime import datetime, timedelta
from dotenv import load_dotenv

# --- LOAD SECRETS ---
load_dotenv()

# WAHA Config
WAHA_BASE_URL = os.getenv("WAHA_BASE_URL", "http://waha:3000")
SESSION_NAME = os.getenv("WAHA_SESSION", "default")
CHAT_ID = os.getenv("WAHA_CHAT_ID")
WAHA_API_KEY = os.getenv("WAHA_API_KEY")

# AWS Config
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# Gemini Config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Local Temp Directory
TEMP_DIR = "./waha_images"
S3_FILE_NAME = f"whatsapp_summary_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.json"

headers = ""
# --- PROMPT INSTRUCTION ---
GEMINI_PROMPT = """
### PERSONA
You are an Expert Visual Document Intelligence Analyst specializing in parsing Hebrew/English academic schedules. You possess advanced OCR capabilities for grid-based data and understand Hebrew date formats.

### OBJECTIVE
Analyze the provided schedule image to extract a strict JSON list of study dates and their corresponding physical locations. You must distinguish between "Home" (Remote) and "Afeka" (On-campus/College).

### VISUAL ANALYSIS INSTRUCTIONS (CRITICAL)
The schedule relies on **Position** and **Color** for context. Follow this scanning logic:
1. **Scan Headers:** Identify dates (DD.MM.YY) in the top row.
2. **Scan Footers (The Bottom Row):** Look at the very bottom cell of each day's column.
   - If the footer says **"\\u05d1\\u05d9\\u05ea"** (Home), the location is **"Home"**.
   - If the footer has a name (e.g., "Tal", "Ido", "Yaniv") or **"\\u05de\\u05d3\\u05e8\\u05d9\\u05da"** (Instructor), the location is likely **"Afeka"**.
3. **Scan Colors (The Legend):**
   - The legend on the left marks **Orange/Peach** as **"\\u05dc\\u05de\\u05d9\\u05d3\\u05d4 \\u05de\\u05d4\\u05d1\\u05d9\\u05ea"** (Learning from Home).
   - If a column's background is Orange, map it to **"Home"**.
4. **Text Fallback:**
   - Keywords like "Zoom", "Online", "**\\u05de\\u05e7\\u05d5\\u05d5\\u05df**" (Online) -> **"Home"**.
   - Keywords like "Lab", "Class", "Exercise", "Room" -> **"Afeka"**.

### RULES
1. **Valid Days:** Sunday (**\\u05e8\\u05d0\\u05e9\\u05d5\\u05df**) through Thursday (**\\u05d7\\u05de\\u05d9\\u05e9\\u05d9**).
2. **Date Format:** Convert "DD.MM.YY" (e.g., "25.12.25") to strict "YYYY-MM-DD" (2025-12-25).
3. **Priority:** Explicit "Home" text or Orange color overrides all other signals.

### OUTPUT FORMAT
Return ONLY a raw, parseable JSON list. No markdown, no conversation.

**Schema:**
[
  {"date": "YYYY-MM-DD", "location": "Home" | "Afeka"}
]

### ERROR HANDLING
- If NO extractable schedule info is found, return exactly:
  'No info for setting: "Home" | "Afeka" '

### CHAIN OF THOUGHT
1. Detect the date in the header.
2. Check the bottom of that specific column for "**\\u05d1\\u05d9\\u05ea**".
3. Check the background color of that column.
4. If "Home" (Hebrew) or "Orange" is found -> Home. Else -> Afeka.
5. Format date and append to list.
""" 
# --- HELPER FUNCTIONS ---

def run_gemini_cli(prompt):
    """Executes the gemini CLI command using subprocess."""
    print("Running Gemini CLI...")
    
    env = os.environ.copy()
    if GEMINI_API_KEY:
        env["GOOGLE_API_KEY"] = GEMINI_API_KEY

    command = [
        "gemini", 
        "-p", prompt, 
        "-m", "pro", 
        "--output-format", "json"
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                print(f"JSON Error. Raw Output: {result.stdout}")
                return None
        else:
            print(f"CLI Error: {result.stderr}")
            return None
    except FileNotFoundError:
        print("Error: 'gemini' command not found. Ensure CLI is installed.")
        return None

def get_messages():
    """Fetch messages from WAHA."""
    if not WAHA_API_KEY or not CHAT_ID:
        print("Error: Missing WAHA_API_KEY or CHAT_ID in .env file.")
        return []

    url = f"{WAHA_BASE_URL}/api/{SESSION_NAME}/chats/{CHAT_ID}/messages"
    params = {"limit": 100} 
    global headers
    headers = {"X-Api-Key": WAHA_API_KEY, "accept": "application/json"}
    
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching WAHA messages: {e}")
        return []

def download_image(url, msg_id):
    """Downloads image to a temp file."""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        
    try:
        if "localhost" in url:
            url = url.replace("localhost", "waha")
            print(f"🔗 Docker Network Fix: Rewrote URL to {url}")
        response = requests.get(url, headers=headers)
        print(response.status_code)
        if response.status_code == 200:
            # Create a safe filename 
            print("Creating a image")
            safe_id = "".join([c for c in msg_id if c.isalnum() or c in ('-','_')])
            filename = f"{TEMP_DIR}/{safe_id}.jpg"
            with open(filename, 'wb') as f:
                f.write(response.content)
                print("Downloaded the image")
            return filename
    except Exception as e:
        print(f"Failed to download image: {e}")
    return None

def cleanup_temp_files():
    files = glob.glob(f"{TEMP_DIR}/*")
    for f in files:
        try:
            os.remove(f)
        except OSError:
            pass

# --- MAIN LOGIC ---

def process_messages():
    messages = get_messages()
    if not messages:
        print("No messages found or API failed.")
        return

    cutoff_time = datetime.now() - timedelta(hours=24)
    print(f"Filtering messages newer than: {cutoff_time}")

    # Initialize prompt with the strict instruction set
    prompt_parts = [GEMINI_PROMPT, "\n--- USER INPUT START ---"]
    message_count = 0

    for msg in messages:
        ts = msg.get('timestamp')
        msg_time = datetime.fromtimestamp(ts)

        if msg_time < cutoff_time:
            continue 

        message_count += 1
        sender = msg.get('from')
        # Correctly get ID as string
        msg_id = msg.get('id', 'unknown')
        text_body = msg.get('body', '')
        
        # Handle Images
        image_tag = ""
        if msg.get('hasMedia'):
            media_info = msg.get('media')
            media_url = media_info.get('url')
            mime_type = media_info.get('mimetype')

            if media_url and mime_type and mime_type.startswith('image'):
                local_path = download_image(media_url, msg_id)
                if local_path:
                    # CLI syntax for local file inclusion
                    image_tag = f" [Attached Image: @{local_path}]"

        if text_body or image_tag:
            line = f"[{msg_time.strftime('%Y-%m-%d %H:%M')}] {sender}: {text_body}{image_tag}"
            prompt_parts.append(line)

    if message_count == 0:
        print("No new messages to process.")
        cleanup_temp_files()
        return

    prompt_parts.append("--- USER INPUT END ---")
    full_prompt = "\n".join(prompt_parts)

    # --- GEMINI CLI ---
    print(f"Sending {message_count} messages to Gemini...")
    cli_response = run_gemini_cli(full_prompt)

    if cli_response:
        # Check for 'response' or 'text'
        summary_text = cli_response.get("response") or cli_response.get("text")
        
        if summary_text:
            print("-" * 20)
            print("Gemini Output:", summary_text)
            print("-" * 20)

            # --- AWS S3 UPLOAD ---
            print(f"Uploading to S3 Bucket: {AWS_BUCKET_NAME}...")
            try:
                s3_client = boto3.client(
                    's3', 
                    region_name=AWS_REGION,
                    aws_access_key_id=AWS_ACCESS_KEY,
                    aws_secret_access_key=AWS_SECRET_KEY
                )
                
                s3_client.put_object(
                    Bucket=AWS_BUCKET_NAME, 
                    Key=S3_FILE_NAME, 
                    Body=summary_text,
                    ContentType='application/json' # Since output is JSON
                )
                print("Upload Successful.")
            except Exception as e:
                print(f"S3 Error: {e}")
        else:
            print("Gemini response did not contain 'text' or 'response'.")
            print("Full Response Keys:", list(cli_response.keys()))
    else:
        print("Failed to get valid response from Gemini.")

    cleanup_temp_files()

if __name__ == "__main__":
    process_messages()
