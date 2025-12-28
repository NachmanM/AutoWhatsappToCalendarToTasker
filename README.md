# Auto-Location Scheduler 📅📍🤖

A comprehensive, automated DevOps pipeline that receives weekly schedules via WhatsApp, uses AI to parse them, updates a Google Calendar, and automates an Android phone to share a live location only when specific classes occur.

---

## 📖 Overview

This project solves the need to provide daily, long-duration live location sharing based on a changing academic or work schedule. Instead of manually checking a schedule and remembering to share location every morning, this system automates the entire process from schedule receipt to on-device execution.

### The Problem it Solves
You receive a complex weekly schedule (often as an image with mixed Hebrew/English text and color codes) on WhatsApp. You need to share your live location via WhatsApp for 8 hours *only* on days where you are physically present at a specific location (e.g., "College/Afeka") and *not* when studying remotely ("Home").

### The Solution
An event-driven architecture that combines local containerized services with serverless cloud functions and on-device Android automation.

## 🏗️ Architecture

Below is a high-level overview of how data flows through the system.

![Architectural Workflow](image_14.png)

## 🌟 Key Features

* **AI-Powered Parsing:** Utilizes Google Gemini 1.5 Pro (Vision & Text) to accurately interpret complex, grid-based schedules from images or text messages sent on WhatsApp.
* **Hybrid Infrastructure:** Combines local Docker containers for heavy lifting (WhatsApp connection, AI processing) with cost-effective serverless AWS Lambda functions for business logic.
* **Secure Design:** Uses AWS Secrets Manager to protect sensitive credentials and custom headers to secure public API endpoints.
* **Smart Android Automation:** The phone acts as an intelligent client, polling the cloud API to decide whether to wake up, unlock, and execute complex UI interactions to share location via WhatsApp.

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Local Host** | Docker Compose | Orchestrating local services. |
| **WhatsApp API** | WAHA (Node.js) | Running a local WhatsApp Web instance. |
| **Scheduler Bot**| Python, Boto3 | Connecting WAHA to Gemini and AWS S3. |
| **AI** | Google Gemini API | Multimodal analysis of schedules. |
| **Cloud Storage**| AWS S3 | Storing parsed schedule data (JSON). |
| **Cloud Logic** | AWS Lambda (Python) | Event-driven calendar updates and API endpoint. |
| **Secrets** | AWS Secrets Manager | Storing Google Service Account keys safely. |
| **Calendar** | Google Calendar API | The source of truth for daily events. |
| **Client Mobile**| Android, Tasker, AutoInput | On-device automation and UI interaction. |

## 📂 Project Structure & Setup Guide

Follow the setup guides in the order presented below to build the system.

### 1. ☁️ Cloud Setup (AWS Lambda)
First, set up the serverless backend that manages your calendar and provides the API for your phone.
* 👉 **Go to:** [`aws-lambda/README.md`](aws-lambda/README.md) (You'll need to create a README in this intermediate folder, or link directly to the two below).
    * Set up the **[Calendar Updater Function](aws-lambda/calendar-updater/README.md)** (triggered by S3).
    * Set up the **[Status Checker API](aws-lambda/status-checker/README.md)** (called by Tasker).

### 2. 🐳 Local Services Setup (Docker)
Next, configure your local server to connect to WhatsApp and process incoming messages.
* 👉 **Go to:** [`waha-service/README.md`](waha-service/README.md) to set up the WhatsApp API container.
* 👉 **Go to:** [`scheduler-bot/README.md`](scheduler-bot/README.md) to set up the Python processor container.
* Once configured, run them together from the root:
    ```bash
    docker-compose up -d
    ```

### 3. 📱 Client Setup (Android Tasker)
Finally, configure your Android phone to query the cloud API every morning and act on the result.
* 👉 **Go to:** [`tasker/README.md`](tasker/README.md) for importable profiles and setup instructions.

## 🔄 Typical Workflow

1.  **Sunday Morning:** A schedule image is received in a specific WhatsApp group.
2.  **Processing:** The local `scheduler-bot` detects the image, sends it to Google Gemini, extracts dates/locations, and saves a `schedule.json` to AWS S3.
3.  **Calendar Update:** The S3 upload triggers the `Calendar Updater` Lambda, which adds "Study: Afeka" events to your Google Calendar for relevant days.
4.  **Daily Trigger (e.g., Tuesday, 07:30 AM):**
    * Your phone's Tasker wakes up and calls the `Status Checker` Lambda API.
    * The Lambda checks your Google Calendar, sees the "Study: Afeka" event for today, and returns `{"trigger": true}`.
    * Tasker receives the "true" signal, unlocks your phone, opens WhatsApp, navigates the menus, and shares your live location for 8 hours.

## 📄 License

[MIT License](LICENSE)
