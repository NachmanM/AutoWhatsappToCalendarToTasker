# WAHA Service (WhatsApp API) 📱

This is the standalone service that runs the WhatsApp HTTP API (WAHA). It runs in its own Docker container and exposes port 3000 for other services to connect to.

## 🚀 Setup & Run

1.  **Configure Environment:**
    Copy the example file and adjust settings if needed.
    ```bash
    cp .env.example .env
    ```

2.  **Start the Container:**
    ```bash
    docker-compose up -d
    ```

3.  **Authenticate:**
    * View the logs to see the QR Code:
        ```bash
        docker logs -f waha-plus
        ```
    * Or go to your browser: `http://localhost:3000/dashboard`
    * Scan the QR code with your phone (WhatsApp > Linked Devices).

## 🔗 Networking Note
Once running, this service is accessible at `http://localhost:3000` on your host machine.
If you are connecting from *another* Docker container (like the Python Bot), you may need to use your machine's local IP address or `host.docker.internal` instead of `localhost`.
