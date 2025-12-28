# Scheduler Bot (Python Processor) 🧠

This container runs the logic for the Auto-Location Scheduler. It connects to the WAHA service to fetch messages, processes them with Google Gemini, and uploads the results to AWS S3.

## 📋 Prerequisites
* The **WAHA Service** must be running (see `../waha-service/README.md`).
* You must have an AWS S3 bucket created.
* You need a Google Gemini API Key.

## 🛠️ Setup

1.  **Environment Variables:**
    Create a `.env` file with your secrets.
    ```bash
    cp .env.example .env
    ```
    *Important:* Pay attention to `WAHA_BASE_URL`. Since this bot runs in a separate container, it cannot reach WAHA via `localhost`. Use `host.docker.internal` (Docker Desktop) or your machine's IP address.

2.  **Build the Image:**
    This image includes Python, Node.js, and the Gemini CLI.
    ```bash
    docker build -t scheduler-bot .
    ```

## 🏃 Usage

### Run Manually (Testing)
Run the bot interactively to see logs and test the connection.
```bash
docker run --rm --env-file .env scheduler-bot
