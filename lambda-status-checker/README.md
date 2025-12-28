# Lambda: Status Checker 🚦

This function is the **Reader**. It provides a lightweight public API for your phone (Tasker) to check where you are supposed to be.

## ⚡ Trigger
* **Type:** Lambda Function URL (Public HTTP Endpoint).
* **Auth:** `NONE` (Publicly accessible URL, secured by Custom Header).

## 🔒 Security
To prevent unauthorized access, this function requires a custom header in every request.
* **Header Name:** `x-secret-header`
* **Header Value:** Must match the `MY_APP_SECRET` environment variable defined in Lambda.

## ⚙️ Configuration

### Environment Variables
You must set these in the AWS Lambda Console:

| Variable | Description |
| :--- | :--- |
| `MY_APP_SECRET` | **(Required)** A random password string (e.g., `MySuperSecretPassword123`). |
| `SECRET_NAME` | The exact name of your secret in AWS Secrets Manager containing the Google credentials. |
| `CALENDAR_ID` | The ID of the calendar to check. |
| `AWS_REGION` | The region where your Secrets Manager is located. |

## 📱 Tasker Integration Guide
You must update your Tasker HTTP Request to include the header.

1.  **Action:** `Net` > `HTTP Request`
2.  **Method:** `GET`
3.  **URL:** Your Lambda Function URL
4.  **Headers:**
    ```text
    x-secret-header: MySuperSecretPassword123
    ```
5.  **Variable Setup:** Tasker stores the JSON response in `%http_data`.

## 🛡️ Permissions Required
* `secretsmanager:GetSecretValue`
* `logs:CreateLogGroup` & `logs:PutLogEvents`
