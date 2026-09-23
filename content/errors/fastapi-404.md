# starlette.exceptions.HTTPException: 404 Not Found
> Encountering `starlette.exceptions.HTTPException: 404 Not Found` means your FastAPI application couldn't find the requested resource; this guide explains how to fix it by checking routes, methods, and deployment configurations.

## What This Error Means

As a DevOps and Cloud Specialist, I've seen countless `404 Not Found` errors across various platforms. When this specific error, `starlette.exceptions.HTTPException: 404 Not Found`, appears in your FastAPI application, it signifies a fundamental routing issue. It means that the Starlette framework, which FastAPI is built upon, received an incoming HTTP request but could not find a defined route (or "endpoint") that matches both the requested URL path *and* the HTTP method (GET, POST, PUT, DELETE, etc.).

Crucially, a 404 is not a server crash or an internal server error (like a 500). Instead, it's an explicit response from your application indicating that while the server is alive and functioning, it simply doesn't know how to handle the specific request you made to that particular path. It's like asking for a book at a library, and the librarian tells you, "We don't have that title here" – not that the library is closed, but that the resource isn't available at the location you specified.

## Why It Happens

The root cause of a `404 Not Found` in FastAPI lies in its routing mechanism. FastAPI, leveraging Starlette, maps incoming HTTP requests to specific Python functions (known as *path operation functions*) based on the request's URL path and HTTP method. If there's no exact match, Starlette raises the `HTTPException(404, detail="Not Found")`.

In my experience, this usually happens because:

1.  **The requested URL path doesn't exist** in your application's defined routes.
2.  **The HTTP method used by the client doesn't match** the method defined for the existing path. For example, a client sending a `POST` request to an endpoint only defined with `@app.get()`.
3.  **The application isn't running the expected code,** meaning new routes haven't been deployed or old routes have been removed.
4.  **External factors** like API gateways, load balancers, or reverse proxies are misconfigured, rewriting paths or not directing traffic correctly to your FastAPI service.

Understanding these underlying reasons is key to efficiently troubleshooting the problem, whether you're in local development or a complex cloud environment.

## Common Causes

Here's a breakdown of the most frequent scenarios I encounter that lead to `starlette.exceptions.HTTPException: 404 Not Found`:

*   **Typo in the Client-Side URL:** This is surprisingly common. A small misspelling in the URL path from your frontend, Postman, curl command, or another service calling your API can instantly trigger a 404. For instance, calling `/userz` instead of `/users`.
*   **Typo in the FastAPI Route Definition:** Similar to client-side typos, a typo in your `@app.get("/incorrect_path")` or `@router.post("/wrong_route")` decorator will mean that specific path simply doesn't exist as far as FastAPI is concerned.
*   **Missing Route Definition:** You might have simply forgotten to add the `@app.<method>("/path")` decorator to a function you intended to expose as an API endpoint, or you removed a route that a client still expects to exist.
*   **Incorrect HTTP Method:** One of the most common mistakes. Your FastAPI route might be defined as `@app.get("/items")`, but your client is attempting to send a `POST` request to `/items`. FastAPI will not find a `POST` handler for that path and will return a 404.
*   **`APIRouter` Prefix Issues:** When using `APIRouter` to modularize your application, you typically mount it with a prefix: `app.include_router(router, prefix="/api/v1")`. If your client then tries to access `/users` when the actual route is `/api/v1/users`, you'll get a 404. Conversely, if your client *includes* the prefix, but you forgot to specify it in `app.include_router`, you'll also hit a 404.
*   **Trailing Slashes (or Lack Thereof):** FastAPI, by default, is smart about trailing slashes, redirecting `/items/` to `/items` (or vice-versa) if a route exists. However, if your application has custom middleware, or if `redirect_slashes=False` is set on your `FastAPI` app or `APIRouter`, this behavior might change and lead to a 404 if the client's slash usage doesn't match the route definition exactly.
*   **Middleware Interference:** Custom middleware that inspects or rewrites paths *before* they reach FastAPI's router can sometimes unintentionally alter a path, leading to a 404. I've seen this in production when a custom authentication middleware incorrectly modifies the request scope.
*   **Order of Route Definitions:** While less common for direct 404s, if you have very generic routes (e.g., a catch-all route like `/path/{wildcard:path}`) defined *before* more specific routes (`/path/specific_item`), the wildcard route might "consume" the request, leading to unexpected behavior. It's generally good practice to define more specific routes first.
*   **Static Files Not Served:** If you're trying to access a static file (e.g., `favicon.ico`, `index.html`) and haven't correctly configured `app.mount()` with `StaticFiles`, FastAPI won't find a route for it and will return a 404.
*   **Deployment Errors:** The most insidious ones. Your local environment works perfectly, but after deployment, you get 404s. This often means the deployed code isn't the expected version, the application isn't running, or proxy/load balancer configurations are directing traffic to the wrong service or path.

## Step-by-Step Fix

Troubleshooting a `404 Not Found` typically involves a systematic check of your application's routing, from the client's request to your FastAPI server's definitions.

1.  **Verify the Client-Side URL and HTTP Method:**
    *   **Double-check the URL:** Is the path exactly what you expect? Pay attention to spelling, casing (paths are case-sensitive), and any prefixes.
    *   **Confirm the HTTP Method:** Are you sending a `GET` when the route expects `POST`? Use tools like Postman, curl, or your browser's developer tools (Network tab) to inspect the exact request being sent.

    ```bash
    # Example: Check with curl
    curl -v -X GET http://localhost:8000/api/v1/users
    # If it fails, try POST or other methods if you suspect a method mismatch
    curl -v -X POST -H "Content-Type: application/json" -d '{"name": "Carmen"}' http://localhost:8000/api/v1/users
    ```

2.  **Inspect FastAPI Route Definitions:**
    *   **Locate the relevant path operation function:** Find the Python function that *should* be handling the request.
    *   **Check the decorator:** Does `@app.get("/your_path")` or `@router.post("/another_path")` exactly match the client's intended path and method?
    *   **Prefixes for `APIRouter`:** If you're using `APIRouter`, ensure the `prefix` in `app.include_router(my_router, prefix="/api/v1")` combines correctly with the router's internal paths. For example, a route `@router.get("/users")` with a `prefix="/api/v1"` will result in the full path `/api/v1/users`.

    ```python
    # main.py or similar
    from fastapi import FastAPI, APIRouter

    app = FastAPI()
    router = APIRouter(prefix="/api/v1")

    @router.get("/items") # This route will be accessible at /api/v1/items
    async def read_items():
        return {"message": "Reading items"}

    @app.get("/health") # This route will be accessible at /health
    async def health_check():
        return {"status": "ok"}

    app.include_router(router) # Make sure you include the router!
    ```

    If a client requests `/items` instead of `/api/v1/items`, it will be a 404.

3.  **Review FastAPI Application Startup Logs:**
    *   When FastAPI starts (usually via Uvicorn), it often logs the registered routes. Look for these messages in your console or server logs. This is a crucial step to confirm what routes your *running* application actually has.

    ```bash
    # Example Uvicorn output
    INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
    INFO:     Started reloader process [12345] using statreload
    INFO:     Started server process [67890]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    # Look here for registered paths if your app or framework logs them explicitly
    # FastAPI usually doesn't log all routes by default, but middleware or custom
    # logging can add this.
    ```
    If you want to explicitly see your routes, you can inspect `app.routes` at startup.

4.  **Check for Middleware or Mounting Issues:**
    *   **Custom Middleware:** If you have custom ASGI middleware, temporarily disable it to see if the 404 resolves. This helps isolate whether the middleware is altering the path.
    *   **`app.mount()` for Static Files:** If you expect to serve static files (CSS, JS, images) and get a 404, verify that `app.mount("/static", StaticFiles(directory="static"), name="static")` is correctly configured and the `directory` path is accurate.
    *   **Sub-applications:** If you're mounting another ASGI application (e.g., a separate FastAPI app, a Gunicorn app), ensure the mount path and the sub-app's routes align.

5.  **Address Trailing Slash Behavior:**
    *   By default, FastAPI will redirect `/items/` to `/items` (and vice-versa) to match a single defined route. If you've explicitly disabled this (e.g., `FastAPI(redirect_slashes=False)`), you need to be precise with your client requests. Check if your client is adding or omitting a trailing slash when your route definition expects the opposite.

6.  **Simplify and Isolate:**
    *   If you're still stuck, create a *minimal* FastAPI application with just the problematic route. Run it in isolation. If it works, gradually add back components from your main application (middleware, routers) until the 404 reappears, pinpointing the conflict.

## Code Examples

Here's a concise example demonstrating common 404 scenarios and a correct setup:

```python
# main.py
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="404 Debugging App")

# Define a base router with a prefix
api_router = APIRouter(prefix="/api/v1")

# --- Correctly defined routes ---

@api_router.get("/items")
async def read_items():
    """Correctly accessed via GET /api/v1/items"""
    return {"message": "List of items"}

@api_router.post("/items")
async def create_item(item: dict):
    """Correctly accessed via POST /api/v1/items with a JSON body"""
    return {"message": f"Item '{item.get('name', 'unknown')}' created"}

@app.get("/health")
async def health_check():
    """Application-level route, accessed via GET /health"""
    return {"status": "healthy"}

# Include the API router
app.include_router(api_router)

# --- Static files setup ---
# Create a 'static' directory and put an 'index.html' inside it for testing
# e.g., static/index.html with content "<h1>Static Page</h1>"
if not os.path.exists("static"):
    os.makedirs("static")
    with open("static/index.html", "w") as f:
        f.write("<h1>Static Page from FastAPI</h1>")

app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Intentional 404 scenarios (for demonstration) ---
# If a client tries to access /api/v1/item (singular) or /api/v1/users (non-existent)
# or POST to /health, they will get a 404.

# To run this example:
# 1. Save as main.py
# 2. pip install "fastapi[all]" uvicorn
# 3. uvicorn main:app --reload

# Test with curl:
# Correct GET: curl http://localhost:8000/api/v1/items
# Correct POST: curl -X POST -H "Content-Type: application/json" -d '{"name": "test_item"}' http://localhost:8000/api/v1/items
# Correct App-level GET: curl http://localhost:8000/health
# Correct Static: curl http://localhost:8000/static/index.html

# Expected 404s:
# Typo in path: curl http://localhost:8000/api/v1/item # 'item' vs 'items'
# Non-existent path: curl http://localhost:8000/api/v1/users
# Wrong method: curl -X POST http://localhost:8000/health # /health is only GET
# Missing prefix: curl http://localhost:8000/items # Missing /api/v1
# Incorrect static path: curl http://localhost:8000/static/non_existent.html
```

## Environment-Specific Notes

The context in which you encounter a 404 can significantly influence your debugging approach.

*   **Local Development:**
    *   This is the easiest environment to debug. You have direct access to your code, console output from Uvicorn (which shows errors and potentially registered routes), and you can use a debugger.
    *   **Tip:** If you're using `uvicorn main:app --reload`, ensure your changes are saved and the reloader picks them up. Sometimes, a syntax error might prevent the app from restarting, leading to old code or an un-routable state.
    *   My first step here is always to check the exact `uvicorn` logs and `app.routes` directly in a debugger if I'm stumped.

*   **Docker Containers:**
    *   When running FastAPI in Docker, the application runs in an isolated environment.
    *   **Port Mapping:** Ensure your `docker run -p 80:8000 ...` or `docker-compose.yml` port mappings are correct. A common mistake is exposing the container's port but not mapping it to the host, or vice-versa.
    *   **Container Logs:** Use `docker logs <container_id>` to see the Uvicorn output from inside the container. This is crucial for verifying if your FastAPI app is actually starting up, what routes it *thinks* it has, and if any startup errors are preventing routing.
    *   **`docker exec`:** Sometimes, I'll `docker exec -it <container_id> bash` to get a shell inside the container and verify that the application code exists at the expected path and that dependencies are installed.

*   **Cloud Environments (AWS, Azure, GCP):**
    *   Cloud deployments add layers of complexity. In my experience, network configuration often masks the true issue.
    *   **Load Balancers (e.g., AWS ALB, Azure Application Gateway, GCP Load Balancing):**
        *   **Path-based Routing:** Many load balancers allow routing based on URL paths. A misconfigured rule can redirect a request to the wrong target group or return a 404 if no rule matches. For example, if your ALB expects `/api/*` to go to service A, but your service A only has `/items`, a request to `/api/users` might get a 404 from the load balancer itself or from a default service.
        *   **Health Checks:** A service might be returning 404s if its health check path (e.g., `/health`) is failing, causing the load balancer to remove it from the target group.
    *   **API Gateways (e.g., AWS API Gateway, Azure API Management, GCP API Gateway):**
        *   **Resource Paths:** API Gateways have their own resource path definitions. If the gateway path (`/users`) doesn't map correctly to your backend FastAPI path (`/api/v1/users`), the gateway might return a 404 *before* it even reaches your application, or your application gets an unexpected path. Pay close attention to proxy integrations (`{proxy+}`) and base path mappings.
        *   **Stage Variables:** Ensure stage variables that might influence backend URLs are correctly configured.
    *   **Serverless (e.g., AWS Lambda + API Gateway, GCP Cloud Functions/Run):**
        *   When deploying FastAPI via mangum or similar ASGI adapters, the API Gateway configuration is paramount. Ensure your Lambda proxy integration is set up correctly and the proxy path (`/{proxy+}`) matches how your FastAPI application is designed to receive paths.
    *   **Application Logs:** Always check the logs of your running application instances (e.g., CloudWatch Logs for AWS, Azure Monitor, GCP Cloud Logging). These will show the Uvicorn/FastAPI output, just like locally, revealing if the app is starting up correctly and what requests it's actually receiving.
    *   **Firewalls/Security Groups:** While rare to cause a 404 (they usually result in connection timeouts or refused), ensure your security groups and network ACLs allow traffic to reach your application instances or load balancers. A 404 implies the request *reached* the application, but it didn't know what to do with it.

## Frequently Asked Questions

**Q: Is a 404 Not Found error a sign that my FastAPI server has crashed?**
**A:** No, quite the opposite. A 404 indicates that your FastAPI server is running and successfully received the request, but it couldn't find a defined route for the specific URL path and HTTP method combination. If the server had crashed, you'd typically see a "Connection refused" or "Internal Server Error" (500) if the server failed after processing the request.

**Q: I'm sure my route is defined correctly in FastAPI, but I still get a 404. What could be wrong?**
**A:** This often points to an issue outside your direct FastAPI code. Double-check client-side typos, ensure the correct HTTP method is being used, verify any `APIRouter` prefixes, and critically, check any intermediary services like API gateways, load balancers, or reverse proxies that might be altering or misrouting the request path before it reaches your FastAPI application. Also, confirm you've deployed the *latest* code.

**Q: Can leading or trailing slashes cause a 404?**
**A:** FastAPI, by default, is quite forgiving with trailing slashes. If you have a route `/items` and a client requests `/items/`, FastAPI will typically redirect them to `/items`. However, if you've configured `FastAPI(redirect_slashes=False)` or have custom middleware, strict adherence to slash usage becomes necessary, and a mismatch could indeed result in a 404.

**Q: Why am I getting a 404 for my static files (CSS, JS, images)?**
**A:** This usually means your `app.mount()` configuration for `StaticFiles` is incorrect or missing. Ensure the `directory` argument points to the correct physical location of your static files on the server and that the `path` in `app.mount("/static", ...)` matches what your client is requesting (e.g., `/static/my_image.png`).

**Q: Could a firewall or security group cause a 404?**
**A:** Not directly. Firewalls and security groups operate at a lower network level. If they block a connection, you'd typically see a connection timeout or a connection refused error, meaning the request never reached your application. A 404 signifies that the request *did* reach your FastAPI application, which then decided it couldn't fulfill it due to a missing route.

## Related Errors