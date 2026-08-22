# starlette.exceptions.HTTPException: 404 Not Found
> Encountering a 404 Not Found error in FastAPI means the requested resource doesn't exist; this guide explains how to diagnose and resolve it.

## What This Error Means

When you encounter `starlette.exceptions.HTTPException: 404 Not Found` in a FastAPI application, it signifies that your application is running, actively received an HTTP request, but could not find a route or resource matching the Uniform Resource Locator (URL) provided in that request. This isn't a server crash, but rather an explicit response from your FastAPI application (or its underlying Starlette framework) indicating that, while the server is operational, the specific path the client requested simply doesn't exist within the defined API.

In HTTP parlance, a "404 Not Found" status code is a client error, meaning the issue lies with the request itself rather than the server experiencing an unexpected failure. From my perspective, this is often a relief because it tells me the application is alive and responding, even if it's with an error. The challenge is then to pinpoint *why* the path wasn't found.

## Why It Happens

The core reason for this error is that FastAPI's routing mechanism, powered by Starlette, failed to match the incoming request's URL path and HTTP method (GET, POST, PUT, DELETE, etc.) against any of the API endpoints you've defined using decorators like `@app.get()`, `@app.post()`, or via `APIRouter`.

Think of FastAPI as having a directory of all available paths and the corresponding function to execute for each. When a request comes in, it consults this directory. If the requested path isn't listed, or if it's listed but the HTTP method doesn't match, then a 404 Not Found is the logical response. It's akin to asking for a specific file in a folder, and the folder reports, "Sorry, that file isn't here."

I've seen this frequently occur during development or when new features are deployed, especially when API contracts change or new endpoints are introduced without proper testing.

## Common Causes

Based on my experience troubleshooting `404 Not Found` errors in FastAPI, these are the most common culprits:

1.  **Typographical Errors in the URL:** This is, by far, the most frequent cause. A simple misspelling in the client-side request URL (e.g., `/user` instead of `/users`, or `/items` instead of `/item`) will lead to a 404 if the backend doesn't have a route for the misspelled path.
2.  **Missing Route Definition:** You might have intended to create an endpoint, but forgot to add the `@app.get("/my-path")` or `@router.post("/new-resource")` decorator, or the associated function.
3.  **Incorrect HTTP Method:** FastAPI routes are specific to HTTP methods. If you define `@app.get("/items")` but the client sends a `POST` request to `/items`, FastAPI won't find a `POST` route for that path and will return a 404. It effectively sees `/items` as available only via `GET`.
4.  **Path Parameter Mismatch:** If your route expects path parameters, such as `@app.get("/items/{item_id}")`, requesting `/items/` (without an `item_id`) or `/items/all` (if `all` is not an expected specific ID or sub-path) might result in a 404 if there isn't a more general route like `@app.get("/items/")` defined.
5.  **Trailing Slashes (or Lack Thereof):** While FastAPI generally normalizes trailing slashes, discrepancies can sometimes arise, particularly with older clients or specific proxy configurations. A route defined as `/users` might not perfectly match `/users/` in all scenarios without explicit handling, though FastAPI is usually robust here.
6.  **Static Files Not Configured or Incorrectly Accessed:** If you're trying to serve static assets (images, CSS, JavaScript files) through FastAPI but haven't correctly configured `app.mount(StaticFiles(directory="static"), name="static")` or you're accessing them via the wrong URL prefix (e.g., `/images/logo.png` instead of `/static/logo.png`), you'll get a 404.
7.  **`APIRouter` or Sub-Application Mounting Issues:** When organizing your API with `APIRouter` or mounting sub-applications, a common mistake is getting the base path wrong. If you define routes in `user_router` with paths like `/`, `/me`, and then mount it as `app.include_router(user_router, prefix="/api/v1/users")`, the actual full paths become `/api/v1/users/`, `/api/v1/users/me`. Forgetting the prefix in the client request or having a mismatch will cause a 404.
8.  **Reverse Proxy/Load Balancer Path Rewrites:** In production environments, reverse proxies (like Nginx, Apache, or cloud load balancers) often sit in front of FastAPI. These proxies can sometimes rewrite URL paths before forwarding them to your application. If a proxy strips a `/api` prefix that your FastAPI app expects, or adds one that your app doesn't, it will lead to a 404 within FastAPI.

## Step-by-Step Fix

Here's how I typically approach diagnosing and fixing `starlette.exceptions.HTTPException: 404 Not Found`:

1.  **Identify the Exact Requested URL and Method:**
    *   Check your application logs. FastAPI often logs 404s, sometimes with the requested path.
    *   If you have a front-end client, inspect its network requests (e.g., in browser developer tools) to get the precise URL and HTTP method (GET, POST, etc.) that triggered the 404.
    *   Use `curl -v` or Postman/Insomnia to make the exact request, paying attention to the full URL, method, and any headers. This helps isolate if the client is sending something unexpected.

2.  **Inspect Your FastAPI Route Definitions:**
    *   **Scan for the Path:** Look through all your `app.py` or `router.py` files for decorators that define the requested path. For example, if the error is for `GET /api/v1/items`, search for `@app.get("/api/v1/items")` or `@router.get("/items")` if using a router with a `/api/v1` prefix.
    *   **Check for Typos:** Are there any subtle spelling mistakes in your route path compared to the requested URL?
    *   **Verify HTTP Method:** Does the decorator's method (e.g., `@app.get`) match the HTTP method of the incoming request? If you're sending a `POST` to `/items` but only have a `GET` route, that's your problem.
    *   **Path Parameters:** If the route involves path parameters (e.g., `/users/{user_id}`), ensure the client is providing a value for `user_id` and that the format matches any type hints you've used (e.g., `int`).

3.  **Confirm Router and Sub-Application Mounting:**
    *   If you're using `APIRouter`, verify that you've correctly included all your routers using `app.include_router()`.
    *   Crucially, check the `prefix` argument in `app.include_router()`. A mismatch here means your API routes will effectively be at a different base URL than what your client expects. For instance, if you define `@router.get("/health")` but `include_router` with `prefix="/api"`, the endpoint is `/api/health`.

4.  **Validate Static File Configuration:**
    *   If the 404 is for an asset like `/static/image.png`, ensure you have:
        ```python
        from fastapi.staticfiles import StaticFiles
        # ...
        app.mount("/static", StaticFiles(directory="static"), name="static")
        ```
    *   Double-check that the `directory` argument points to the correct location of your static files relative to your application's root. Also, verify that the `"/static"` prefix matches what the client is requesting.

5.  **Examine Your Deployment Environment (if applicable):**
    *   **Reverse Proxies:** If your application sits behind Nginx, Caddy, an AWS Application Load Balancer (ALB), or similar, check its configuration. Is it rewriting paths in a way that your FastAPI app doesn't expect? Is it correctly forwarding requests to your FastAPI service?
    *   **Containerization (Docker):** Ensure your Dockerfile's `CMD` or `ENTRYPOINT` is correctly starting your FastAPI application. I've sometimes seen issues where the container starts but Uvicorn isn't listening on the correct host (`0.0.0.0`) or port, leading to external 404s (though often these manifest as connection refused or 5xx from the proxy).
    *   **Serverless (e.g., AWS Lambda + API Gateway):** API Gateway path mapping can be complex. Ensure your Lambda proxy integration is configured correctly, especially if you're using `/{proxy+}` catch-all routes.

6.  **Add Logging:**
    *   Temporarily add logging middleware or print statements within your FastAPI application's startup or routing logic (if possible) to see the exact paths FastAPI is aware of, and the exact path of incoming requests. This can be invaluable for debugging.

```python
# Basic logging middleware example (for debugging purposes)
from starlette.middleware.base import BaseHTTPMiddleware
import logging

class LogRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logging.info(f"Incoming Request: {request.method} {request.url}")
        response = await call_next(request)
        return response

app.add_middleware(LogRequestsMiddleware)
logging.basicConfig(level=logging.INFO)
```

By methodically going through these steps, you can typically narrow down the cause of the 404 error quite effectively.

## Code Examples

Here are some concise, copy-paste ready examples illustrating common 404 scenarios and their fixes.

**Scenario 1: Simple Path Mismatch**

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
async def read_hello():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# To run: uvicorn main:app --reload
```

*   **Works:** `GET http://localhost:8000/hello` -> `{"message": "Hello, World!"}`
*   **404:** `GET http://localhost:8000/hallo` (typo in path)
*   **404:** `POST http://localhost:8000/hello` (wrong HTTP method)
*   **Works:** `GET http://localhost:8000/items/123` -> `{"item_id": 123}`
*   **404:** `GET http://localhost:8000/items` (missing `item_id` for this specific path, though you could add a route for `/items` without a parameter)

**Scenario 2: Using `APIRouter` with a Prefix**

```python
# routers/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_all_users():
    return {"users": ["Alice", "Bob"]}

@router.get("/{user_id}")
async def get_user(user_id: str):
    return {"user": user_id}

# main.py
from fastapi import FastAPI
from routers import users # Assuming routers/users.py is in the same directory or importable

app = FastAPI()

# Include the router with a prefix
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])

# To run: uvicorn main:app --reload
```

*   **Works:** `GET http://localhost:8000/api/v1/users/` -> `{"users": ["Alice", "Bob"]}`
*   **Works:** `GET http://localhost:8000/api/v1/users/john.doe` -> `{"user": "john.doe"}`
*   **404:** `GET http://localhost:8000/users/` (missing `/api/v1` prefix)
*   **404:** `GET http://localhost:8000/api/users/` (incorrect `/v1` prefix)
*   **404:** `GET http://localhost:8000/api/v1/user/` (typo: `/user` instead of `/users`)

**Scenario 3: Static Files**

```python
# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Create a 'static' directory and put an 'index.html' inside it
# e.g., static/index.html
# <html><body><h1>Hello Static!</h1></body></html>

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the API"}

# To run: uvicorn main:app --reload
```

*   **Works:** `GET http://localhost:8000/static/index.html` -> Serves `static/index.html`
*   **Works:** `GET http://localhost:8000/` -> `{"message": "Welcome to the API"}`
*   **404:** `GET http://localhost:8000/index.html` (missing `/static` prefix)
*   **404:** `GET http://localhost:8000/assets/index.html` (incorrect prefix, should be `/static`)
*   **404:** `GET http://localhost:8000/static/nonexistent.js` (file `nonexistent.js` doesn't exist in `static` directory)

## Environment-Specific Notes

The troubleshooting steps remain similar across environments, but certain factors become more prominent:

*   **Local Development:**
    *   Generally the easiest to debug. You have direct access to the code, server logs, and can restart quickly.
    *   Focus on code typos, `APIRouter` prefixes, and correct static file paths relative to your project root.
    *   Ensure Uvicorn is running and accessible on `localhost` or `127.0.0.1` and the correct port.

*   **Docker Containers:**
    *   **Port Exposure:** Ensure the Docker container exposes the port your FastAPI app listens on (e.g., `EXPOSE 8000` in Dockerfile) and that the host machine maps a port to it (`docker run -p 8000:8000`).
    *   **Host Binding:** FastAPI (via Uvicorn) should listen on `0.0.0.0` within the container, not `127.0.0.1`, so it's accessible from outside the container. Your `CMD` or `ENTRYPOINT` should be something like `uvicorn main:app --host 0.0.0.0 --port 8000`.
    *   **File Paths in Container:** Verify that static file directories or configuration files are correctly copied into the container at the paths FastAPI expects (e.g., `COPY ./static /app/static`).
    *   **Container Logs:** `docker logs <container_id>` is your best friend for seeing what FastAPI is doing inside the container.

*   **Cloud Deployment (AWS ECS, Kubernetes, Serverless, etc.):**
    *   **Load Balancers/API Gateways:** This is where `404 Not Found` errors can become tricky. A common scenario is that a load balancer (like AWS ALB or Nginx Ingress in Kubernetes) has a base path (`/api/v1`) that it *strips* before forwarding the request to your FastAPI service. Your FastAPI app might then receive `/users` when it expects `/api/v1/users`, resulting in a 404. Conversely, if your load balancer doesn't add a prefix your app expects, you'll also get a mismatch.
        *   **Solution:** Configure your load balancer to correctly rewrite or forward paths, *or* adjust your FastAPI `APIRouter` prefixes to match what your application receives after the proxy.
    *   **Kubernetes Ingress Controllers:** Examine your Ingress resource's rules and annotations (`nginx.ingress.kubernetes.io/rewrite-target`, `pathType`). A misconfigured `path` or `rewrite-target` can lead to the proxy-stripping issue described above.
    *   **Serverless (e.g., AWS Lambda + API Gateway):**
        *   API Gateway routes (`Path` or `ANY /{proxy+}`) must match what your FastAPI-wrapped Lambda function expects.
        *   If using a non-proxy integration, you'll need explicit method and path mappings which can be prone to `404 Not Found` if not aligned. I usually recommend `Lambda Proxy Integration` for FastAPI apps on Lambda as it passes the full request context.
    *   **Environment Variables:** Check if base paths, static file locations, or router prefixes are determined by environment variables that might be set differently in your production cloud environment compared to local development. This is a subtle but common source of differences.

## Frequently Asked Questions

*   **Q: Why do I get a 404 for my static files but my API endpoints work?**
    *   **A:** This almost always means your `app.mount(StaticFiles(...))` configuration is incorrect. Double-check the `directory` path (relative to where your app starts) and the URL `prefix` (e.g., `/static`). The client must request the files using that exact prefix.

*   **Q: I have `@app.get("/users")` and `@app.get("/users/{user_id}")`. Why does `/users` sometimes return 404?**
    *   **A:** While FastAPI is generally smart about route ordering (more specific before more general), a 404 for the general path (`/users`) when a more specific one exists (`/users/{user_id}`) usually indicates a subtle typo in the `/users` route's definition, or a situation where a catch-all route defined *after* `users` somehow captures it, or middleware interfering. Ensure the `/users` route is correctly defined and, if necessary, place it before more general path parameter routes if both are defined.

*   **Q: My frontend makes a request to `/api/data`, but my FastAPI app only has `@app.get("/data")`. What's wrong?**
    *   **A:** Your frontend is sending a request to a path that your backend isn't expecting. You have two main options:
        1.  **Adjust the Backend:** Add `/api` to your FastAPI routes (e.g., `@app.get("/api/data")` or use `app.include_router(my_router, prefix="/api")`).
        2.  **Adjust the Frontend/Proxy:** Configure your frontend application or any reverse proxy in front of FastAPI to remove the `/api` prefix before forwarding the request to your backend.

*   **Q: Can a 404 mean my server is down?**
    *   **A:** No, quite the opposite! A 404 error explicitly means your FastAPI application is running, received the request, and successfully processed it enough to determine that the requested URL path does not correspond to any defined route. If your server were truly down, you would typically receive a "Connection Refused" error, a "Host Unreachable," or potentially a 5xx error from an upstream proxy if it can't reach your server.

*   **Q: I'm seeing 404s in production but not locally. What gives?**
    *   **A:** This is a classic indicator of environment-specific configuration differences. Focus your investigation on:
        *   **Reverse Proxy/Load Balancer Configuration:** Path rewrites, base path additions/removals.
        *   **Containerization (`CMD`/`ENTRYPOINT`):** How Uvicorn is started, host binding.
        *   **Environment Variables:** Any differences that might alter route prefixes or static file locations.
        *   **Deployment Pipeline:** Ensure the correct code version is deployed. I've had situations where an older, non-compliant version was accidentally deployed.

## Related Errors
*()