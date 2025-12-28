# Lambda: Calendar Updater 📅

This function is the **Writer**. It is event-driven and runs automatically whenever a new schedule file is uploaded to S3.

## ⚡ Trigger
* **Source:** AWS S3
* **Event:** `s3:ObjectCreated:Put`
* **Filter:** Suffix `.json` (optional but recommended)

## 🔄 Logic
1.  **Read S3:** Downloads the JSON file uploaded by the Docker Processor.
2.  **Auth:** Retrieves Google Service Account credentials securely from AWS Secrets Manager.
3.  **Check Duplicates:** Checks Google Calendar to see if an event already exists for that day/location to prevent duplicates.
4.  **Create Event:** Adds an "All Day" event to the specified Google Calendar (e.g., "Study: Afeka").

## 📦 Dependencies & Lambda Layers
To keep the function code lightweight and fast, all external Python libraries are installed via an **AWS Lambda Layer**, rather than being bundled in the function zip.

### `requirements.txt` (for the Layer)
The Lambda Layer was built using these requirements:
```text
google-api-python-client
google-auth
google-auth-oauthlib
google-auth-httplib2
requests
