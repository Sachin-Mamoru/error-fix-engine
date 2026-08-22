# starlette.websockets.WebSocketDisconnect: 1000
> Encountering `starlette.websockets.WebSocketDisconnect: 1000` means a WebSocket connection was closed normally; this guide explains its nuances and how to handle it gracefully.

## What This Error Means

When you encounter `starlette.websockets.WebSocketDisconnect: 1000`, it's crucial to understand that, despite the `Disconnect` in the name, this is typically *not* an error in the sense of something breaking unexpectedly. Instead, `1000` is the WebSocket protocol status code for "Normal Closure." It signifies that the connection has been closed cleanly, either because the client initiated the closure, or the server gracefully terminated it, and both parties understood and agreed to the closure.

Think of it less as a problem and more as an event notification. In the context of FastAPI, which uses Starlette under the hood for WebSocket capabilities, this exception is raised to signal the end of a WebSocket connection's lifecycle. Other disconnect codes (like `1001` for going away, `1006` for abnormal closure, `1008` for policy violation, etc.) would indicate issues, but `1000` is usually a sign that things are working as intended for a graceful shutdown.

## Why It Happens

This "disconnect" occurs when the WebSocket connection, which is persistent, needs to be terminated. The underlying Starlette/FastAPI framework raises this specific exception to allow your application code to react to the closure event.

Common scenarios where `starlette.websockets.WebSocketDisconnect: 1000` will be observed include:

*   **Client-Initiated Closure:** The most frequent cause. A user closes their browser tab, navigates away from a page using WebSockets, or the client-side JavaScript explicitly calls `websocket.close()`.
*   **Server-Initiated Graceful Shutdown:** Your FastAPI application might explicitly close a WebSocket connection, perhaps due to a server-side timeout, a user session expiring, or as part of a controlled server shutdown sequence.
*   **Network Events Handled Gracefully:** While less common for code 1000, some network proxies or load balancers might gently terminate idle connections after a timeout period, which the client or server interprets as a normal closure.
*   **Application Logic:** Your own application code might decide to close a connection based on certain conditions being met or unmet.

In my experience, 90% of the `WebSocketDisconnect: 1000` messages I see in logs are due to clients simply closing their browsers or switching pages. It's a natural part of a web application's lifecycle.

## Common Causes

Let's break down the typical origins of a `WebSocketDisconnect: 1000` in more detail:

1.  **User Action:**
    *   Closing the browser window or tab.
    *   Navigating to a different URL.
    *   Refreshing the page (which implicitly closes the old connection before establishing a new one).
    *   Explicit client-side JavaScript call to `WebSocket.close()`.

2.  **Client-Side Application Logic:**
    *   A client-side framework or library deciding to close the connection after a specific event, such as a user logging out or an inactive period.

3.  **Server-Side Application Logic:**
    *   Your FastAPI endpoint explicitly calling `await websocket.close(code=1000)`. This is a clear signal from the server that it wishes to end the connection gracefully.
    *   If your server has a mechanism to disconnect idle clients after a certain period to conserve resources.
    *   During a controlled server restart or shutdown, where connections are gracefully terminated before the process exits.

4.  **Network Infrastructure (indirectly):**
    *   While proxies and load balancers usually cause more abrupt closures (e.g., `1006`), a well-configured proxy might initiate a graceful shutdown after a very long idle period, which could manifest as a `1000` code if the negotiation is clean. This is rarer, but I've seen this in production when long-lived, rarely used connections hit an extremely generous proxy timeout.

Understanding these common causes helps in determining if the `1000` code is benign or if it points to an underlying issue (e.g., too many rapid disconnections suggesting a problem with client-side reconnection logic).

## Step-by-Step Fix

Since `WebSocketDisconnect: 1000` indicates a normal closure, the "fix" isn't about preventing it, but rather about *handling* it gracefully within your application. This involves ensuring your server-side code cleans up resources and doesn't crash when a client disconnects.

1.  **Implement `try...except WebSocketDisconnect`:**
    The most critical step is to wrap your WebSocket message receiving loop in a `try...except` block. This allows your application to catch the `WebSocketDisconnect` exception and perform necessary cleanup without crashing.

    ```python
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect

    app = FastAPI()

    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: int):
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                # Process received data
                await websocket.send_text(f"Message text was: {data}")
        except WebSocketDisconnect:
            print(f"Client #{client_id} disconnected normally.")
            # Perform any necessary cleanup for this client
            # e.g., remove from active connections list, close database session
        except Exception as e:
            print(f"An unexpected error occurred with client #{client_id}: {e}")
            # Handle other types of exceptions
    ```

2.  **Perform Resource Cleanup:**
    Inside the `except WebSocketDisconnect` block, this is your opportunity to clean up any resources associated with that specific client. This might include:
    *   Removing the client from a list of active WebSocket connections.
    *   Closing a database connection or releasing a lock held for that client.
    *   Notifying other connected clients that this client has left.

    This ensures your application doesn't leak memory or connections.

3.  **Client-Side Graceful Closure (if applicable):**
    Ensure your client-side code explicitly closes the WebSocket connection when it's no longer needed, rather than just letting the tab close. This is good practice for managing resources on both ends.

    ```javascript
    // Example client-side JavaScript
    const ws = new WebSocket("ws://localhost:8000/ws/123");

    ws.onopen = (event) => {
        console.log("WebSocket connection opened.");
    };

    ws.onmessage = (event) => {
        console.log("Received:", event.data);
    };

    ws.onclose = (event) => {
        if (event.wasClean) {
            console.log(`Connection closed cleanly, code=${event.code}, reason=${event.reason}`);
        } else {
            // e.g. server process killed or network down
            console.error('Connection died unexpectedly.');
        }
    };

    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
    };

    // To close explicitly (e.g., when user logs out or navigates away)
    function closeConnection() {
        if (ws.readyState === WebSocket.OPEN) {
            ws.close(1000, "User logged out"); // 1000 is normal closure
        }
    }

    // Call closeConnection() on appropriate events (e.g., beforeunload, logout)
    window.addEventListener('beforeunload', closeConnection);
    ```

4.  **Logging and Monitoring:**
    While `1000` is normal, logging these events can be helpful. Log them at an `INFO` or `DEBUG` level, not `ERROR`. If you see an unusually high rate of `1000` disconnections, it might warrant investigation. For instance, if your application expects long-lived connections but they're constantly dropping and reconnecting, that suggests a problem with client-side stability or network infrastructure.

## Code Examples

Here are concise, copy-paste ready examples demonstrating the key patterns for handling `WebSocketDisconnect: 1000`.

**FastAPI Server-Side Handling:**

This example shows a basic FastAPI WebSocket endpoint that manages multiple connected clients, handling disconnections gracefully.

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import asyncio

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"Client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"Client disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self0, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    await manager.broadcast(f"Client #{client_id} joined the chat.")
    try:
        while True:
            # You would typically receive messages here
            data = await websocket.receive_text()
            print(f"Received from #{client_id}: {data}")
            await manager.broadcast(f"From #{client_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat.")
    except Exception as e:
        print(f"Error for client #{client_id}: {e}")
        manager.disconnect(websocket) # Ensure disconnect on unexpected errors too
        await manager.broadcast(f"Client #{client_id} experienced an error and left.")

# Example route to send a message to all clients from an HTTP endpoint
@app.get("/send-to-all/{message}")
async def send_to_all(message: str):
    await manager.broadcast(f"Server says: {message}")
    return {"message": "Broadcast sent"}
```

**JavaScript Client-Side Example (Basic):**

This minimal HTML and JavaScript shows how a client connects and handles closure, including explicit closure.

```html
<!DOCTYPE html>
<html>
<head>
    <title>FastAPI WebSocket Client</title>
</head>
<body>
    <h1>WebSocket Test</h1>
    <input type="text" id="messageInput" placeholder="Enter message">
    <button onclick="sendMessage()">Send</button>
    <button onclick="closeWebSocket()">Close WebSocket</button>
    <div id="messages"></div>

    <script>
        const clientId = Math.floor(Math.random() * 1000);
        const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`);
        const messagesDiv = document.getElementById("messages");
        const messageInput = document.getElementById("messageInput");

        ws.onopen = (event) => {
            logMessage("CONNECTED");
        };

        ws.onmessage = (event) => {
            logMessage(`Received: ${event.data}`);
        };

        ws.onclose = (event) => {
            if (event.wasClean) {
                logMessage(`DISCONNECTED cleanly, code=${event.code}, reason=${event.reason}`);
            } else {
                logMessage('DISCONNECTED unexpectedly (e.g., server process killed or network down)');
            }
        };

        ws.onerror = (error) => {
            logMessage("ERROR: " + error.message);
        };

        function sendMessage() {
            const message = messageInput.value;
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(message);
                messageInput.value = '';
            } else {
                logMessage("WebSocket is not open. Cannot send message.");
            }
        }

        function closeWebSocket() {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close(1000, "User requested closure"); // Explicitly close with normal code
            }
        }

        function logMessage(message) {
            const p = document.createElement("p");
            p.textContent = message;
            messagesDiv.appendChild(p);
        }

        // Optional: Close WebSocket when leaving the page
        window.addEventListener('beforeunload', () => {
            closeWebSocket();
        });
    </script>
</body>
</html>
```

## Environment-Specific Notes

The behavior and handling of WebSocket disconnections, even normal ones, can vary slightly depending on your deployment environment.

*   **Cloud Deployments (AWS, GCP, Azure, etc.):**
    *   **Load Balancers:** Services like AWS ALB, GCP Load Balancer, or Azure Application Gateway often have idle timeouts. If a WebSocket connection remains truly idle (no data sent in either direction) for longer than this timeout, the load balancer might terminate the connection. Depending on the load balancer's configuration and how gracefully it handles this, it might result in a `1000` or a more abrupt code like `1006`. It's crucial to configure these timeouts appropriately for your application's needs. For long-lived, potentially idle WebSockets, you might need to implement client-side *ping/pong* mechanisms to keep the connection alive. I've personally dealt with ALB timeouts silently dropping connections that were expected to last hours, and implementing simple `setInterval` pings on the client fixed it.
    *   **Auto-Scaling:** When your instances scale down or restart, active WebSocket connections on those instances will be terminated. Your application should be designed to handle these disconnections gracefully, and clients should be configured to attempt reconnection (with backoff) to new instances.
    *   **Monitoring:** Pay attention to connection metrics. Sudden drops in total connections without corresponding user activity could indicate issues with your infrastructure or application restarts.

*   **Docker/Containerized Environments:**
    *   **Container Restarts:** If a Docker container running your FastAPI app crashes, restarts, or is terminated by an orchestrator like Kubernetes, all active WebSocket connections to that container will be abruptly terminated. While the client might see a `1006` (abnormal closure), the server's `try...except` block will still catch `WebSocketDisconnect` if it manages to process the termination signal before exiting.
    *   **Network Overlays:** Docker's networking or Kubernetes services might introduce additional layers that could have their own timeouts or failure modes. Ensure your network configurations allow for long-lived WebSocket connections.

*   **Local Development:**
    *   In a local development setup, `1000` is most commonly seen when you manually close the browser tab or hit `Ctrl+C` to stop your FastAPI server. This is exactly where your `try...except` blocks prove their worth, allowing a clean shutdown of the client-server interaction without ugly stack traces in your console. It's an excellent way to test your graceful shutdown logic.

Regardless of the environment, a robust WebSocket application must assume that connections can and will drop for various reasons, both normal and abnormal, and build resilient handling and reconnection strategies into both the server and client.

## Frequently Asked Questions

**Q: Is `WebSocketDisconnect: 1000` always a good thing?**
A: Generally, yes. It indicates a normal, graceful closure initiated by either the client or the server. It's the expected way for a WebSocket connection to end without errors.

**Q: How can I differentiate `1000` from actual errors like network drops?**
A: `starlette.websockets.WebSocketDisconnect` is an exception. The code `1000` is part of the exception's details. Other codes like `1006` (abnormal closure) would signify a real problem. Your `try...except WebSocketDisconnect` block handles *all* such disconnects. You can inspect the exception object if you need to differentiate the code, e.g., `except WebSocketDisconnect as e: if e.code == 1000: ... else: ...`. Other exceptions (e.g., `ConnectionClosedOK` or `ConnectionClosedError` from `websockets` library, or generic `OSError` for network issues) would indicate different problems.

**Q: Should I log every `WebSocketDisconnect: 1000`?**
A: It depends on your logging strategy. For high-traffic applications, logging every `1000` at an `INFO` or `WARN` level can generate a lot of noise. Consider logging them at a `DEBUG` level by default. Only elevate to `INFO` if you need to specifically track connection lifecycles or if you're debugging an issue related to frequent disconnects.

**Q: Does frequent `WebSocketDisconnect: 1000` impact performance?**
A: While `1000` itself is normal, a high frequency of *any* type of connection/disconnection event can impact performance if your server has significant overhead in establishing or tearing down connections (e.g., resource allocation, authentication, cleanup). If clients are constantly connecting, disconnecting, and reconnecting, it might indicate an underlying issue with client-side stability or an aggressive server-side timeout configuration that leads to repeated churn.

**Q: What if I see `1000` constantly even when the user isn't actively closing the tab?**
A: This could indicate a subtle problem. Common culprits include:
*   **Aggressive Client-Side Logic:** Your client-side code might be inadvertently closing connections.
*   **Short Server-Side Timeouts:** Your server might be explicitly closing idle connections after a short period.
*   **Proxy/Load Balancer Idle Timeouts:** As mentioned in `Environment-Specific Notes`, an intermediary might be terminating idle connections.
*   **Network Instability:** Brief network hiccups could cause a connection to drop and be re-established, but often these manifest with other error codes. If it's *always* `1000`, look at deliberate closures.

## Related Errors
*(none)*