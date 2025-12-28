# Tasker Client (Android Automation) 📱

This directory documents the client-side automation running on the Android device. Unlike the server-side code, this logic resides in the **Tasker** app and the **AutoInput** plugin.

## 📖 Overview
The Android phone acts as the final execution agent. It polls the AWS Lambda Status Checker to see if a specific event ("Afeka") is scheduled for today. If true, it automatically wakes up, unlocks the screen, and shares a live location via WhatsApp.

## 🛠️ Prerequisites
* **App:** Tasker (Paid)
* **Plugin:** AutoInput (Paid)
* **Permissions:** Accessibility Service (for AutoInput), Draw Over Other Apps, Location.

## ⚙️ Task Logic Breakdown

The task **"Send Live Location"** follows this strict sequence:

### 1. Check Status (AWS)
* **Action:** `HTTP Request` (GET)
* **URL:** Your Lambda Function URL.
* **Headers:** `x-secret-header: <YOUR_SECRET>`
* **Logic:** The task proceeds **only** if the response contains `%http_data.trigger ~ true`.

### 2. Wake Up Sequence
Since AutoInput requires an active screen to "click" buttons, the phone must be awake.
* **Turn On:** Wakes the screen.
* **Test Display:** Checks if the keyguard (lock screen) is active.

### 3. Unlock Sequence (If Locked)
*This section handles the PIN/Pattern bypass.*
* **Swipe:** AutoInput performs a gesture to dismiss the lock screen overlay.
* **PIN Entry:** If a PIN is required, AutoInput simulates taps on specific coordinates or number keys (Actions 11-16).
    * *⚠️ Security Warning:* Storing your PIN in Tasker actions is visible to anyone with access to the app.

### 4. WhatsApp Automation
* **Launch Chat:** Uses `Browse URL` with `https://wa.me/972587488444` to open the specific chat immediately.
* **Navigate UI (AutoInput):**
    1.  Clicks **Attach** (Paperclip icon).
    2.  Clicks **Location**.
    3.  Clicks **Share Live Location**.
    4.  Clicks **Select Time** (e.g., 8 hours).
    5.  Clicks **Send**.

## 🚀 Setup Guide

1.  **Create Profile (Trigger):**
    * **Time:** Set to `07:30` (or your desired departure time).
    * **Link:** Connect to the "Send Live Location" Task.

2.  **Configure HTTP Request:**
    * Ensure the `x-secret-header` matches your Lambda environment variable `MY_APP_SECRET`.

3.  **Calibrate AutoInput:**
    * The "Click" actions in the screenshots (Actions 21-29) rely on specific screen elements. If WhatsApp updates its UI, you may need to re-scan these buttons using AutoInput's "Easy Setup" mode.

## ⚠️ Known Limitations
* **Screen On Required:** This task **cannot** run purely in the background. The screen MUST turn on for AutoInput to work.
* **Smart Lock:** It is highly recommended to use **Android Smart Lock** (Trusted Places/Devices) to disable the PIN requirement at home. This makes the automation 100% reliable as it skips the complex PIN entry steps.
