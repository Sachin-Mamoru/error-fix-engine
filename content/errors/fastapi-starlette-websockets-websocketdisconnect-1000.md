# starlette.websockets.WebSocketDisconnect: 1000
> Encountering `starlette.websockets.WebSocketDisconnect: 1000` means a WebSocket connection was closed normally; this guide explains its implications and how to manage it effectively.

## What This Error Means

The `starlette.websockets.WebSocketDisconnect: 1000` message is often misunderstood as an error, but in reality, it signifies a *normal, expected closure* of a WebSocket connection. The `1000` in the message refers to a specific WebSocket close code defined in RFC 6455, indicating "Normal Closure." This means that the client or server (or both) explicitly initiated the disconnection in a clean and anticipated manner.

Unlike other WebSocket disconnect codes (e.g., `1006` for "Abnormal Closure" or `1001` for "Going Away" due to a server or client closing a tab), a `1000` code suggests that the communication handshake for closing the connection was completed successfully. It's the equivalent of hanging up a phone call politely after the conversation is over, rather than the line suddenly going dead.

For a DevOps and Cloud specialist, understanding this distinction is crucial. When you see `1000`, your first instinct shouldn't be to panic and search for a bug. Instead, it should prompt you to confirm whether this closure was intended by your application's logic or your user's behavior. If it was intended, then this "error" is merely an informational event, not a problem requiring a fix.

## Why It Happens

`starlette.websockets.WebSocketDisconnect: 1000` occurs because either the client or the server, or sometimes an intermediary, decided to end the WebSocket connection gracefully. The key here is "gracefully."

Here are the primary scenarios I've observed that lead to a `1000` code:

1.  **Client-Initiated Normal Closure:**
    *   The user closes the browser tab or navigates away from the page that established the WebSocket connection.
    *   The client-side JavaScript code explicitly calls `WebSocket.close()`. This might happen after the client has received all necessary data, or as part of a logout/disconnect sequence.

2.  **Server-Initiated Normal Closure:**
    *   Your FastAPI application logic explicitly calls `websocket.close()`. This is common if the server has completed a specific task for that client, or if the client's session has expired, or the server needs to gracefully shed connections before a shutdown.
    *   The server detects an idle connection and, rather than abruptly terminating it (which might result in a `1006`), it sends a `1000` close frame before tearing down resources. This is less common for application servers directly but can happen.

3.  **Proxy/Load Balancer Initiated Normal Closure:**
    *   While less frequent for `1000` (idle timeouts from proxies often result in `1006`), a properly configured load balancer or reverse proxy (like NGINX, HAProxy, or cloud load balancers such as AWS ALB) *can* gracefully close connections with a `1000` code. This would typically occur if the proxy's own timeout settings are configured to send a close frame rather than just dropping the connection. I've seen this in production when specific proxy configurations are used for long-lived connections that have an explicit maximum duration.

The underlying mechanism involves a "close frame" being sent by one end, and the other end responding with its own close frame, followed by the TCP connection being torn down. This successful handshake results in the `1000` code.

## Common Causes

Delving deeper into the 'why', here are the most common specific scenarios where you might encounter `starlette.websockets.WebSocketDisconnect: 1000`:

*   **User Interaction:** This is arguably the most frequent cause. A user simply closing their browser tab, navigating to another page, or explicitly logging out of an application will trigger the client-side JavaScript to terminate the WebSocket connection. Since it's an expected client action, the `1000` code is correct.

*   **Client-side Application Logic:** Modern web applications often manage WebSocket lifecycles. If your frontend framework (e.g., React, Vue, Angular) cleans up components, it might explicitly close WebSocket connections associated with those components upon unmounting or before re-rendering. Similarly, a dedicated "disconnect" button in the UI would also trigger this.

*   **Server-side Application Logic:** Your FastAPI endpoint might have a condition under which it decides to close the connection. For instance, if a client requests data that is only available for a short period, or if the server detects a change in client permissions requiring a reconnect, it might initiate a `websocket.close()` with the intention of the client re-establishing later.

*   **Server Shutdowns/Restarts:** During a graceful shutdown of your FastAPI application (e.g., when deploying a new version, scaling down, or performing maintenance), the ASGI server (like Uvicorn) will attempt to send close frames to all active WebSocket clients. This ensures clients are notified of the server's intention to disconnect, resulting in `1000` codes on the client and in your server logs.

*   **Short-lived WebSocket Interactions:** Sometimes, WebSockets are used for single-shot, semi-realtime data transfers rather than continuous streams. Once the data exchange is complete, either the client or server might close the connection with `1000`.

*   **Network Equipment/Cloud Provider Timeouts (Graceful):** While usually an abrupt network timeout results in a `1006` or a silent drop, certain cloud load balancers or firewalls, when configured for very specific, graceful idle timeouts, *can* send a `1000` close frame to maintain good network hygiene. I've encountered this occasionally with specific configurations of AWS API Gateway WebSockets where idle connections were gracefully terminated.

## Step-by-Step Fix

As established, `starlette.websockets.WebSocketDisconnect: 1000` is often not an "error" to be fixed but an event to be understood and possibly managed. Your "fix" primarily involves verifying if the closure is expected and handling it appropriately in your logging and application logic.

### Step 1: Determine if it's an Actual Problem
Before anything else, ask yourself: *Is this `1000` disconnect occurring under circumstances where the WebSocket should still be active?*
*   If a user closes their browser, a `1000` is expected.
*   If your server completes a task and then closes the connection, a `1000` is expected.
*   If you're seeing `1000` disconnects after only a few seconds when you expect a long-lived connection, then it *might* indicate an underlying issue in your application logic or environment setup, even though the close itself was "normal."

### Step 2: Inspect Client-Side Behavior
If you suspect premature `1000` disconnects, start with the client:
1.  **Browser Developer Tools:** Open the browser's developer console (F12), go to the "Network" tab, filter by "WS" (WebSockets). Watch the WebSocket connection's lifecycle. Does it connect and then immediately close? Is there any client-side JavaScript error immediately preceding the close?
2.  **Client-side `WebSocket.close()` Calls:** Search your client-side codebase for explicit calls to `WebSocket.close()`. Identify the conditions under which these calls are made. Are they intentional?
3.  **Client-side Framework Lifecycle:** If you're using a frontend framework, understand its component lifecycle. Is the component that initiates the WebSocket being unmounted or re-rendered in a way that causes an unintentional disconnect?

### Step 3: Inspect Server-Side Logic
Next, examine your FastAPI application:
1.  **Explicit `websocket.close()`:** Search your server code for `await websocket.close()`. Identify the conditions leading to these calls. Are they intentional and correctly placed?
2.  **Application Flow:** Trace the execution path for your WebSocket endpoint. Is there any logic that might prematurely exit the `async for` loop or the `try...except` block, leading to an implicit or explicit disconnect?
    ```python
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                # ... process data ...
                if data == "terminate": # Example: Server-side logic to close
                    await websocket.close(code=1000)
                    break # Exit the loop, allowing normal disconnect
                await websocket.send_text(f"Message text was: {data}")
        except WebSocketDisconnect as e:
            if e.code == 1000:
                print(f"WebSocket normally disconnected with code {e.code}")
            else:
                print(f"WebSocket disconnected with unexpected code {e.code}: {e.reason}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    ```

### Step 4: Review Proxy and Load Balancer Configurations
While `1000` is less common for load balancer timeouts (which usually result in `1006`), it's still worth checking if you're experiencing unexpected disconnects.
1.  **Load Balancer Idle Timeouts:** Check the idle timeout settings on your AWS ALB, GCP Load Balancer, NGINX, or other proxies. Ensure they are sufficiently long for your WebSocket connections. A very short idle timeout could, in some configurations, lead to a graceful disconnect if no application data is exchanged, even if the TCP connection is alive.
2.  **WebSocket Headers:** Ensure your proxies are correctly forwarding WebSocket upgrade headers (`Upgrade` and `Connection`). Incorrect configuration here typically leads to `400` errors or connection failures, not `1000` disconnects, but it's a good general check.
    ```nginx
    # Example NGINX configuration for WebSockets
    location /ws {
        proxy_pass http://your_upstream_fastapi_server;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s; # Adjust as needed for long-lived connections
        proxy_send_timeout 86400s;
    }
    ```

### Step 5: Implement Robust Logging for Context
Don't just log `WebSocketDisconnect`. Log the `code` and `reason`, and add contextual information. This is critical for distinguishing between expected and unexpected closures.
*   **Log Client ID:** If your application assigns a unique ID to each client, log it.
*   **Log Session State:** Log relevant information about the client's session or what they were doing when the disconnect occurred.
*   **Use appropriate log levels:** A `1000` can often be `INFO` or `DEBUG`, while a `1006` might be `WARNING` or `ERROR`.

## Code Examples

Here are some concise, copy-paste ready code examples for handling WebSockets in FastAPI and a basic client.

### FastAPI WebSocket Endpoint with Graceful Disconnect Handling

This example shows a simple WebSocket echo server that explicitly closes the connection after a specific message and handles disconnects.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging

app = FastAPI()

# Configure basic logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = id(websocket) # Simple unique ID for the client
    await websocket.accept()
    logging.info(f"Client {client_id} connected.")
    try:
        while True:
            message = await websocket.receive_text()
            if message == "bye":
                logging.info(f"Client {client_id} sent 'bye'. Closing connection normally.")
                await websocket.send_text("Goodbye!")
                await websocket.close(code=1000) # Explicit normal closure
                break # Exit the loop after closing
            logging.info(f"Client {client_id} sent: {message}")
            await websocket.send_text(f"Server received: {message}")
    except WebSocketDisconnect as e:
        if e.code == 1000:
            logging.info(f"Client {client_id} disconnected normally (code 1000). Reason: {e.reason or 'No specific reason'}")
        else:
            logging.error(f"Client {client_id} disconnected with unexpected code {e.code}. Reason: {e.reason or 'No specific reason'}")
    except Exception as e:
        logging.error(f"Client {client_id} experienced an unexpected error: {e}", exc_info=True)
    finally:
        logging.info(f"Client {client_id} handler finished.")

# To run this: uvicorn your_module_name:app --reload
```

### Client-Side JavaScript for Normal Closure

This JavaScript snippet demonstrates how a client can connect, send messages, and then explicitly close the connection normally.

```javascript
// client.js
const ws = new WebSocket("ws://localhost:8000/ws");

ws.onopen = (event) => {
    console.log("WebSocket connected!");
    ws.send("Hello from client!");
};

ws.onmessage = (event) => {
    console.log("Message from server:", event.data);
    if (event.data === "Server received: close_me") {
        console.log("Received 'close_me', client initiating normal close.");
        ws.close(1000, "Client requested normal shutdown"); // Explicit normal closure
    }
};

ws.onclose = (event) => {
    if (event.wasClean) {
        console.log(`WebSocket closed cleanly, code=${event.code}, reason=${event.reason}`);
    } else {
        // e.g. server process killed or network down
        console.error('WebSocket connection died unexpectedly');
    }
};

ws.onerror = (error) => {
    console.error("WebSocket Error:", error);
};

// Example: send a message after 3 seconds
setTimeout(() => {
    ws.send("This is another message.");
}, 3000);

// Example: client explicitly closing after 6 seconds
setTimeout(() => {
    console.log("Client explicitly sending 'bye' to server.");
    ws.send("bye"); // Server will close connection after this
}, 6000);

// Example: Client-side logic for closing without server interaction
setTimeout(() => {
    if (ws.readyState === WebSocket.OPEN) {
        console.log("Client explicitly closing the connection after 9 seconds if still open.");
        ws.close(1000, "Client timed out interaction");
    }
}, 9000);
```

## Environment-Specific Notes

The interpretation and management of `WebSocketDisconnect: 1000` can vary slightly based on your deployment environment.

*   **Local Development:**
    *   In a local environment (e.g., `uvicorn main:app --reload`), you're typically connecting directly to your FastAPI application.
    *   `1000` disconnects here are almost always due to explicit client actions (closing browser tab, JavaScript `ws.close()`) or explicit server actions (`websocket.close()`).
    *   Troubleshooting is straightforward as there are no intermediate proxies complicating matters. You can easily test client and server logic in isolation.

*   **Docker:**
    *   When running FastAPI in Docker, the primary consideration is correct port mapping and network configuration.
    *   Ensure your `docker run` command or `docker-compose.yml` file correctly exposes the port your Uvicorn server is listening on.
    *   If you're using a reverse proxy (like NGINX) *within* Docker or as a separate container, make sure its configuration handles WebSocket upgrade headers correctly as detailed in Step 4.
    *   `1000` disconnects in a Dockerized environment generally mirror local development, unless the Docker network itself is unstable (less common for `1000` codes).

*   **Cloud (AWS, GCP, Azure):**
    *   **Load Balancers (AWS ALB, GCP Load Balancer, Azure Application Gateway):** This is where things get more complex. These services are critical for routing and managing connections.
        *   Ensure your load balancer listener is configured to pass WebSocket traffic. For example, on AWS ALB, you'd typically use HTTP/HTTPS listeners and ensure proper target group configurations.
        *   **Idle Timeouts:** Load balancers *will* have idle timeouts. If a WebSocket connection remains idle for longer than the configured timeout, the load balancer will eventually close it. While often resulting in a `1006` (abnormal closure) due to an abrupt drop, some configurations *can* initiate a `1000` close if the LB sends a proper close frame. In my experience, AWS ALBs and API Gateway (for WebSocket APIs) are particularly sensitive to idle timeouts. Always ensure these are set generously for long-lived WebSocket connections.
        *   **Health Checks:** Misconfigured health checks can cause your application instances to be deemed unhealthy and taken out of rotation, leading to active connections being terminated. This is usually more abrupt than `1000`, but worth noting.
    *   **Reverse Proxies (NGINX, Envoy, Caddy on EC2/GCE/VMs):** If you're running your own NGINX or similar proxy in a cloud VM, its configuration is paramount.
        *   Verify the `proxy_http_version 1.1`, `proxy_set_header Upgrade $http_upgrade`, and `proxy_set_header Connection "upgrade"` directives are correctly set.
        *   Adjust `proxy_read_timeout` and `proxy_send_timeout` to accommodate your expected WebSocket connection duration. A `1000` from NGINX would indicate it explicitly closed the connection, perhaps due to a gracefully handled timeout or specific configuration.
    *   **Serverless (AWS Lambda with API Gateway, GCP Cloud Functions):**
        *   Direct long-lived WebSockets are not typically handled directly by serverless functions. Instead, services like AWS API Gateway's WebSocket API manage the persistent connection, and events (like `connect`, `message`, `disconnect`) trigger your Lambda/Cloud Function.
        *   In this setup, `WebSocketDisconnect: 1000` would primarily refer to the API Gateway's management of the connection being closed normally by the client. Your function might receive a `disconnect` event, but the `starlette.websockets.WebSocketDisconnect` error itself would be less relevant to your *FastAPI* function, as the FastAPI layer is generally not directly managing the raw WebSocket connection at this level.

## Frequently Asked Questions

**Q: Is `starlette.websockets.WebSocketDisconnect: 1000` always an error?**
**A:** No, almost universally, it is *not* an error. It indicates a normal, graceful closure of the WebSocket connection, either initiated by the client or the server. You should treat it as an informational event unless it occurs unexpectedly based on your application's logic or user's behavior.

**Q: How do I distinguish between an expected `1000` and one that indicates an underlying problem?**
**A:** Context is key. If a user closes their browser tab, a `1000` is expected. If your server deliberately closes a connection, it's expected. If, however, you're building a chat application and clients are frequently getting `1000` disconnects after only a few seconds without any user interaction or server-side reason, then it suggests a problem (e.g., faulty client-side logic, an intermediate proxy aggressively closing connections, or an unintended server-side close). Robust logging with contextual information (user ID, session state) is essential.

**Q: Can a load balancer or reverse proxy cause a `1000` disconnect?**
**A:** Yes, potentially. While abrupt proxy timeouts usually manifest as `1006` (abnormal closure) or silent drops, a load balancer or proxy that is *configured to gracefully manage idle connections* might send a `1000` close frame before terminating the underlying TCP connection. This means it's still a "normal" close from the WebSocket protocol's perspective, even if the application didn't explicitly request it.

**Q: Should I `raise` or `log` this specific error?**
**A:** You should almost always *log* it, typically at an `INFO` or `DEBUG` level, rather than `raise` it. Re-raising `WebSocketDisconnect: 1000` would treat an expected event as an exception, potentially cluttering your error monitoring systems and obscuring real problems. Only `raise` if you have specific, highly critical application logic that considers *any* disconnect (even a `1000`) at a specific point to be an exceptional fault.

**Q: What if I need my WebSocket connection to stay open indefinitely?**
**A:** Even "indefinite" connections are subject to timeouts. You'll need to implement a "heartbeat" or "ping-pong" mechanism both client-side and server-side. Periodically send small frames (e.g., every 30-60 seconds) to ensure the connection remains active and doesn't get terminated by idle timeouts from proxies, load balancers, or the network stack itself. This keeps the connection "alive" and prevents unexpected `1000` or `1006` disconnects due to inactivity.

## Related Errors