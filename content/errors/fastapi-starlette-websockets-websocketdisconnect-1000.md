# starlette.websockets.WebSocketDisconnect: 1000
> Encountering `starlette.websockets.WebSocketDisconnect: 1000` means a WebSocket connection was closed normally; this guide explains its implications and how to manage it effectively.

## What This Error Means

When you see `starlette.websockets.WebSocketDisconnect: 1000` in your FastAPI application logs, it signifies that a WebSocket connection has been closed. Crucially, the code `1000` indicates a "Normal Closure" as defined by the WebSocket protocol (RFC 6455, Section 7.4.1). Unlike many other `WebSocketDisconnect` codes (like `1006` for abnormal closure or `1011` for internal error), `1000` is generally *not* an error. Instead, it's an informational message indicating that the connection terminated gracefully and intentionally, either by the client or the server.

From a practical standpoint, this means the WebSocket handshake completed successfully, data was potentially exchanged, and then one party initiated a proper closing handshake. This is the expected behavior for any WebSocket connection that needs to end.

## Why It Happens

The `starlette.websockets.WebSocketDisconnect: 1000` message occurs because the underlying Starlette (which FastAPI builds upon) WebSocket implementation detects a clean shutdown of the connection. This can happen for several legitimate reasons, and understanding the context is key to determining if it's expected behavior or a symptom of something else.

In my experience, this message often appears when:

1.  **Client-Initiated Closure:** The client application explicitly closes the WebSocket connection. This is the most common scenario. For example, a user closes the browser tab, navigates away from the page, the JavaScript application calls `webSocket.close()`, or a mobile app goes into the background and decides to disconnect.
2.  **Server-Initiated Graceful Closure:** The FastAPI server application itself decides to close the connection. This could be due to:
    *   A planned server shutdown or restart (e.g., during a deployment).
    *   The server explicitly calling `await websocket.close()` after completing a task or due to application logic (e.g., a session timeout).
3.  **Application Logic:** Your application might have specific conditions under which it deems a connection no longer necessary and initiates a clean close from either the client or server side.

It's important to differentiate this from unexpected disconnections, which would typically result in different error codes (e.g., `1006` for abnormal closure without a closing handshake, often due to network issues or abrupt termination).

## Common Causes

Let's dive deeper into the specific scenarios that frequently lead to `WebSocketDisconnect: 1000`:

*   **User Interaction:**
    *   A user closing their web browser or a specific tab/window.
    *   Navigating to a different URL within a single-page application (SPA) where the previous WebSocket connection is no longer needed.
    *   Explicitly logging out or performing an action that triggers a client-side `WebSocket.close()`.
*   **Client-Side Application Logic:**
    *   JavaScript frameworks or libraries automatically closing connections when components unmount or become inactive.
    *   Mobile applications disconnecting when backgrounded to conserve resources.
    *   Desktop applications exiting or switching modes that don't require the WebSocket.
*   **Server-Side Application Logic:**
    *   A FastAPI endpoint explicitly calling `await websocket.close()` after fulfilling its purpose (e.g., streaming a finite amount of data).
    *   An internal event triggering a server-side disconnect for a specific client (e.g., user session invalidation).
*   **Deployment and Server Restarts:**
    *   During a CI/CD pipeline, when a new version of your FastAPI application is deployed, the old instances shut down gracefully. This often involves the server initiating `SIGTERM` or similar signals, prompting Uvicorn/Gunicorn to close existing connections, leading to `1000` codes for active WebSockets.
*   **Load Balancer/Proxy Behavior (Indirectly):** While less common for *explicit* `1000` codes, sometimes load balancers or proxies have idle timeouts. If a client is inactive and the proxy closes the connection, the client might then send a clean close, or the server might detect the closure. For true idle timeouts, you'd more often see `1006` or `1001` if not handled correctly, but a well-configured proxy *can* facilitate a clean shutdown.

## Step-by-Step Fix

Since `1000` typically indicates a normal closure, the "fix" isn't about correcting an error but rather about *understanding* and potentially *managing* these disconnections.

1.  **Acknowledge and Understand:**
    *   First and foremost, understand that `WebSocketDisconnect: 1000` is usually a non-error event. Don't immediately treat it as a bug.
    *   Consider the context: Did a user just navigate away? Was the server redeployed? This initial assessment is critical.

2.  **Review Client-Side Closure Logic:**
    *   If you're seeing frequent `1000` disconnections, check your client-side code (JavaScript, mobile app logic, etc.).
    *   Are you explicitly calling `webSocket.close()`? If so, ensure it's at an appropriate time.
    *   Are there frameworks or libraries that might be closing connections automatically (e.g., React component unmount, Vue `beforeDestroy`)? Ensure this behavior aligns with your application's needs.

3.  **Implement Graceful Server Shutdowns:**
    *   When deploying or restarting your FastAPI application, ensure your Uvicorn/Gunicorn setup allows for graceful shutdowns. This gives active WebSocket connections a chance to close properly.
    *   Uvicorn typically handles `SIGTERM` by attempting to shut down gracefully, closing open connections. I've found that ensuring a reasonable `timeout_graceful_shutdown` setting for Gunicorn (if you're using it with Uvicorn workers) is crucial.

    ```bash
    # Example Gunicorn command for graceful shutdown
    gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 --timeout 60 --graceful-timeout 30
    ```
    Here, `graceful-timeout` gives workers time to finish requests and close connections.

4.  **Refine Logging and Monitoring:**
    *   If the volume of `1000` messages is overwhelming or you need to debug specific connection behaviors, adjust your logging levels.
    *   You might want to log these disconnections at an `INFO` or `DEBUG` level rather than `WARNING` or `ERROR` to reduce noise in production.
    *   Consider adding specific logging within your FastAPI WebSocket endpoint to capture client details (e.g., user ID, session ID) upon disconnect. This can help correlate `1000` events with user actions.

    ```python
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    import logging

    logger = logging.getLogger("uvicorn.error") # Or your custom logger

    app = FastAPI()

    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        await websocket.accept()
        logger.info(f"WebSocket connected: {client_id}")
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_text(f"Message text was: {data}")
        except WebSocketDisconnect as e:
            # Check for normal closure code
            if e.code == 1000:
                logger.info(f"WebSocket normally disconnected: {client_id} (code: {e.code})")
            else:
                logger.warning(f"WebSocket disconnected abnormally: {client_id} (code: {e.code}, reason: {e.reason})")
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            logger.info(f"WebSocket handler finished for {client_id}")
    ```

5.  **Proactive Connection Management (If Unexpectedly High Disconnects):**
    *   If you observe a pattern of clients connecting and immediately disconnecting with `1000` *without* apparent user action, it might indicate a client-side bug where it's establishing and closing connections unnecessarily. Review the client's connection lifecycle.
    *   For very long-lived connections, implementing server-side or client-side heartbeats can help detect truly dead connections proactively, which might prevent eventual `1006` errors and ensure `1000` is used for intentional closes.

## Code Examples

Here are some concise, copy-paste ready examples for both server and client illustrating graceful WebSocket closures.

### FastAPI Server Endpoint

This example shows a basic FastAPI WebSocket endpoint that logs disconnections, differentiating between normal and abnormal closures.

```python
# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import logging

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("my_fastapi_app")

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Client</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <button onclick="closeConnection()">Close Connection</button>
        <script>
            var ws = null;
            var client_id = Date.now();
            document.addEventListener('DOMContentLoaded', (event) => {
                ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
                ws.onopen = (event) => {
                    var messages = document.getElementById('messages');
                    var item = document.createElement('li');
                    item.textContent = `Connected to server (Client ID: ${client_id})`;
                    messages.appendChild(item);
                };
                ws.onmessage = (event) => {
                    var messages = document.getElementById('messages');
                    var item = document.createElement('li');
                    item.textContent = event.data;
                    messages.appendChild(item);
                };
                ws.onclose = (event) => {
                    var messages = document.getElementById('messages');
                    var item = document.createElement('li');
                    item.textContent = `Disconnected from server (Code: ${event.code}, Reason: ${event.reason})`;
                    messages.appendChild(item);
                    ws = null; // Clear WebSocket instance
                };
                ws.onerror = (error) => {
                    var messages = document.getElementById('messages');
                    var item = document.createElement('li');
                    item.textContent = `WebSocket Error: ${error}`;
                    messages.appendChild(item);
                };
            });

            function sendMessage(event) {
                var input = document.getElementById("messageText");
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(input.value);
                    input.value = '';
                } else {
                    alert("WebSocket is not connected or closing.");
                }
                event.preventDefault();
            }

            function closeConnection() {
                if (ws) {
                    ws.close(1000, "Client initiated close"); // Explicitly close with code 1000
                    ws = null;
                }
            }
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for client: {client_id}")
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from {client_id}: {data}")
            await websocket.send_text(f"You said: {data}")
    except WebSocketDisconnect as e:
        if e.code == 1000:
            logger.info(f"Client {client_id} disconnected normally (code: {e.code}, reason: {e.reason})")
        else:
            logger.warning(f"Client {client_id} disconnected with code: {e.code}, reason: {e.reason}")
    except Exception as e:
        logger.error(f"An unexpected error occurred with client {client_id}: {e}")
    finally:
        logger.info(f"WebSocket handler ending for client: {client_id}")

```

To run this:
1.  Save the code as `main.py`.
2.  Install FastAPI and Uvicorn: `pip install "fastapi[all]" uvicorn`
3.  Run the server: `uvicorn main:app --reload`
4.  Open `http://localhost:8000` in your browser.
5.  Send messages, then click "Close Connection" or simply close the browser tab. Observe the server logs. You should see `Client <ID> disconnected normally (code: 1000, reason: Client initiated close)` or similar.

## Environment-Specific Notes

The interpretation and management of `WebSocketDisconnect: 1000` can vary slightly across different deployment environments.

*   **Local Development:**
    *   This is the easiest environment to debug. Disconnections are usually direct consequences of your client-side actions (browser refresh, tab close) or server restarts.
    *   Logs are immediately visible in your terminal, making it straightforward to correlate client behavior with server-side disconnect events.

*   **Docker Containers:**
    *   When stopping a Docker container running your FastAPI application (e.g., `docker stop <container_id>`), Docker sends a `SIGTERM` signal.
    *   A well-behaved Uvicorn or Gunicorn process inside the container will catch `SIGTERM` and attempt a graceful shutdown, leading to `1000` codes for active WebSocket connections as it closes them.
    *   If `docker kill` is used or the process doesn't handle `SIGTERM` correctly, you might see `1006` (Abnormal Closure) instead, as the connection is abruptly severed. Ensure your container's entrypoint or `CMD` allows the Python process to receive and handle `SIGTERM`.

*   **Cloud Environments (AWS, GCP, Azure):**
    *   **Load Balancers:** Cloud load balancers (e.g., AWS ALB, GCP Load Balancer, Azure Application Gateway) handle routing WebSocket traffic. They often have idle timeouts. While a `1000` typically comes from an explicit close, if a load balancer terminates an idle connection *without* a clean WebSocket close handshake, you'd typically see `1006`. If your client is configured to send a clean close *before* the LB timeout, then `1000` is possible.
    *   **Container Orchestration (E.g., Kubernetes - GKE, EKS, AKS):** When pods are scaled down, redeployed, or evicted, Kubernetes sends `SIGTERM` to the container's main process. Similar to Docker, a graceful shutdown strategy for your application within the pod is critical to ensure `1000` (normal closure) rather than `1006` (abnormal closure) or other unexpected errors. Configure `terminationGracePeriodSeconds` in your deployment manifest to give your application enough time to close connections. I've seen issues in production when this period is too short for long-lived WebSocket connections.
    *   **Serverless (E.g., AWS Lambda, GCP Cloud Functions with API Gateway):** While direct WebSockets are less common in traditional serverless functions (which are request-response based), platforms like AWS API Gateway support WebSocket APIs. Disconnections here are managed by the gateway, and client-side closes would still result in a `1000` if the gateway correctly relays the close frame. The challenge is more about persistent connection management on the serverless side rather than the `1000` code itself.

## Frequently Asked Questions

**Q: Is `WebSocketDisconnect: 1000` always a good thing?**
A: Generally, yes. It means the WebSocket connection was closed gracefully, as per the protocol. It's an informational event rather than an error that needs fixing.

**Q: How can I distinguish between an intentional client close and a server restart?**
A: Implement detailed logging. On the client side, log when `WebSocket.close()` is called. On the server side, within your `WebSocketDisconnect` exception handler, log the client ID and the reason. For server restarts, your application's startup/shutdown logs should indicate when processes are being terminated, helping you correlate disconnections with deployments.

**Q: Could a high volume of `1000` disconnects indicate a problem?**
A: Potentially. While `1000` is a normal close, if you're seeing a rapid connect-disconnect cycle for many clients, it might point to a client-side bug (e.g., incorrectly re-establishing connections, or connecting to a service it immediately realizes it doesn't need). Review client application logic for such patterns.

**Q: What if I'm getting other codes like `1001`, `1006`, or `1011`?**
A: Those codes *do* typically indicate problems.
*   `1001`: Going Away (client leaving, e.g., browser navigating).
*   `1006`: Abnormal Closure (no close frame sent, often network issues, abrupt client/server termination). This one often requires investigation.
*   `1011`: Internal Error (server-side issue preventing fulfillment of request).
Each of these warrants a deeper dive into client or server logs and network conditions.

## Related Errors