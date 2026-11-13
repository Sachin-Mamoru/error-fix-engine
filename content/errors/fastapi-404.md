# starlette.exceptions.HTTPException: 404 Not Found
> Encountering a 404 Not Found in FastAPI means the requested endpoint does not exist; this guide explains how to identify and resolve routing issues.

## What This Error Means

When you encounter `starlette.exceptions.HTTPException: 404 Not Found`, it signifies that your FastAPI application, or more precisely, its underlying Starlette framework, could not find a route definition matching the incoming HTTP request's path and method. In simple terms, the client requested a resource or an endpoint that the server doesn't know how to serve.

The `404 Not Found` is a standard HTTP status code indicating that the server could not find the requested resource. Unlike 5xx errors (server errors), a 404 typically means the client made a request for a path that simply doesn't exist on the server. From FastAPI's perspective, this means no `@app.get()`, `@app.post()`, or similar decorator matches the path and HTTP method used in the request.

## Why It Happens

At its core, a 404 happens because there's a disconnect between what the client application is asking for and what your FastAPI application is configured to provide. The FastAPI application processes incoming requests by trying to match their HTTP method (GET, POST, PUT, DELETE, etc.) and URL path against its defined routes. If no match is found after checking all registered `APIRouter` instances and direct application routes, Starlette ultimately raises this 404 error.

In my experience, this isn't usually an issue with the FastAPI framework itself, but rather a configuration or coding mistake within the application or the client making the request.

## Common Causes

Here are the most frequent reasons I've seen for a `starlette.exceptions.HTTPException: 404 Not Found`:

1.  **Typo in the URL Path:** This is by far the most common cause. A simple misspelling in the client's request URL (e.g., `/users` instead of `/user`, or `/items_list` instead of `/items`) will lead to a 404.
2.  **Incorrect HTTP Method:** While often resulting in a `405 Method Not Allowed`, if a path exists *only* for, say, a `GET` request and a `POST` request is made to it, FastAPI *might* return a 404 if there's no handler at all for that path for any other method. More commonly, if you've defined `@app.post("/users/")` but the client sends a `GET` request, and there's no `GET` handler for `/users/`, you'll get a 404.
3.  **Missing or Mismatched Path Parameters:** If your route expects path parameters (e.g., `@app.get("/items/{item_id}")`) but the client requests `/items/` without a specific ID, it won't match. Similarly, type mismatches (e.g., requesting `/items/abc` when `item_id` is typed as `int`) can also cause issues.
4.  **`APIRouter` Not Included:** If you're organizing your routes using `APIRouter` instances, but forget to include them in your main `FastAPI` application using `app.include_router()`, none of the routes defined in that router will be accessible.
5.  **Incorrect Base Path/Prefix:** When using `APIRouter` with a `prefix` (e.g., `APIRouter(prefix="/api/v1")`), clients must include that prefix in their requests. If a route `/users` is defined within such a router, the client must request `/api/v1/users`, not just `/users`.
6.  **Trailing Slashes:** Sometimes, the presence or absence of a trailing slash can cause a mismatch. While FastAPI typically normalizes `/items` and `/items/` to match the same route, in some complex setups or with specific middleware, this might occasionally cause a problem.
7.  **External Proxy/Load Balancer Configuration:** In production environments, an API Gateway, load balancer (e.g., Nginx, AWS ALB), or reverse proxy might be misconfigured to forward requests to the wrong path on your FastAPI application, resulting in a 404 even if the client's initial request was correct.
8.  **Application Not Running or Not Accessible:** Although less likely to produce a `404` (more often a "connection refused" or timeout), if your FastAPI app isn't actually running or isn't listening on the port the client is trying to reach, the client might eventually receive a `404` from an intermediate proxy.

## Step-by-Step Fix

Troubleshooting a 404 error requires a systematic approach. I always follow these steps:

1.  **Verify the Requested URL and HTTP Method:**
    *   **Client Side Check:** The absolute first step is to confirm exactly what URL and HTTP method the client is using. Use browser developer tools (Network tab), `curl`, Postman, Insomnia, or your client library's logging to see the outgoing request.
        ```bash
        # Example: Requesting a known non-existent path with curl
        curl -v http://localhost:8000/non_existent_path
        ```
    *   **Confirm against expectations:** Does this match what you *intend* the client to request?

2.  **Inspect FastAPI Route Definitions:**
    *   **Code Review:** Open your FastAPI application code (`main.py` and any files containing `APIRouter` instances).
    *   Look for the specific route decorator (`@app.get`, `@router.post`, etc.) that should handle the request.
    *   **Check for typos:** Are there any subtle misspellings in the path strings (e.g., `/user` vs. `/users`, `/items` vs. `/item`)?
    *   **Check HTTP Method:** Does the decorator's method (e.g., `.get`, `.post`) match the client's request method?
    *   **Verify Path Parameters:** If your route uses path parameters (e.g., `/items/{item_id}`), ensure the client is providing a value for `item_id` and that its type matches (e.g., an integer if `item_id: int`).

3.  **Check for Mounted Routers:**
    *   If you're using `APIRouter` for modularity, ensure every router containing the target route is explicitly included in your main `FastAPI` application instance.
    *   Search for `app.include_router(your_router_instance)`. A common oversight is defining a router but forgetting to add this line.

4.  **Examine Base Paths and Prefixes:**
    *   If an `APIRouter` uses a `prefix` (e.g., `APIRouter(prefix="/v1/users")`), confirm that the client's request includes this entire prefix (e.g., `GET /v1/users/profile`). The `/docs` endpoint can be a real lifesaver here.

5.  **Consult FastAPI's Interactive Documentation (`/docs` or `/redoc`):**
    *   FastAPI automatically generates OpenAPI documentation, usually accessible at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc) by default.
    *   This is the canonical source of truth for what endpoints your application exposes. Browse these pages and verify that the endpoint you're trying to reach is listed exactly as you expect, including its path, method, and any parameters. If it's not listed, it means FastAPI hasn't registered it.

6.  **Add Logging or Debugging Middleware:**
    *   Sometimes, seeing the request as FastAPI receives it can be illuminating. You can add simple middleware to log the incoming request path and method before FastAPI processes it.
    *   This helps differentiate between a client sending the wrong request and FastAPI not finding a matching route even for a correct request.

    ```python
    # main.py
    from fastapi import FastAPI, Request
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import PlainTextResponse

    app = FastAPI()

    # Simple middleware to log incoming requests
    class RequestLoggerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            print(f"Incoming request: {request.method} {request.url.path}")
            response = await call_next(request)
            return response

    app.add_middleware(RequestLoggerMiddleware)

    @app.get("/")
    async def read_root():
        return {"message": "Hello FastAPI"}

    # Run with: uvicorn main:app --reload
    ```
    If you see your request path logged correctly by the middleware, but still get a 404, the issue is almost certainly within your route definitions or router inclusion.

7.  **Check External Factors (Proxies, Load Balancers, API Gateways):**
    *   In deployed environments, always check the configuration of any component sitting between the client and your FastAPI application.
    *   **Nginx/Apache:** Verify `location` blocks and `proxy_pass` directives.
    *   **AWS API Gateway/ALB:** Confirm integration requests, path mappings, and listener rules. Is the API Gateway stripping a base path that your FastAPI app expects? I've seen this many times where `/prod` or `/dev` prefixes are handled by the gateway, but the backend expects the raw path.

## Code Examples

Here are some common FastAPI routing scenarios and how to correctly implement them, along with examples of mistakes that lead to 404s.

**Correct FastAPI Setup with Router and Path Parameters:**

```python
# main.py
from fastapi import FastAPI, APIRouter

app = FastAPI()

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to the API!"}

# Direct app endpoint with a path parameter
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "detail": f"This is item {item_id}"}

# Define an APIRouter for users
user_router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@user_router.get("/")
async def read_users():
    return [{"username": "Alice"}, {"username": "Bob"}]

@user_router.get("/{user_id}")
async def read_user(user_id: str):
    return {"user_id": user_id, "detail": f"User {user_id} found"}

# --- IMPORTANT: Include the router in the main app ---
app.include_router(user_router)

# To run this: uvicorn main:app --reload
# Test with:
# curl http://localhost:8000/
# curl http://localhost:8000/items/123
# curl http://localhost:8000/users/
# curl http://localhost:8000/users/charlie
```

**Common Mistake: Missing `app.include_router()`**

If the line `app.include_router(user_router)` is commented out or missing from the `main.py` above, all `/users` endpoints would return a 404, even if correctly defined in `user_router`.

```python
# main.py (excerpt showing the mistake)
# ... user_router definition ...

# app.include_router(user_router) # THIS LINE IS MISSING!
# If this line is not present, all /users routes will 404.
```

**Common Mistake: Incorrect Path Parameter Usage**

If you define a route expecting a path parameter:

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    return {"product_id": product_id}

# If a client requests:
# curl http://localhost:8000/products/  <-- This will 404 because "product_id" is missing.
#
# Correct request:
# curl http://localhost:8000/products/XYZ123
```

## Environment-Specific Notes

The context of your deployment can influence how you troubleshoot 404s.

### Local Development

*   **Debugging Ease:** This is the easiest environment to debug. You have direct access to your code, console logs, and often an interactive debugger.
*   **`uvicorn --reload`:** Running your app with `uvicorn main:app --reload` (or similar for your entry point) allows immediate feedback on code changes.
*   **Direct Access:** You're typically hitting the FastAPI application directly, so there are fewer external factors (like proxies) to consider. Focus on your code and client requests.

### Docker Containers

*   **Port Mapping:** Ensure that your Docker container's exposed port is correctly mapped to a host port that the client is trying to reach (e.g., `-p 8000:80`).
*   **Container Logs:** Always check `docker logs <container_id>` for any errors during application startup or runtime that might prevent routes from being registered.
*   **`CMD` / `ENTRYPOINT`:** Verify that your `Dockerfile`'s `CMD` or `ENTRYPOINT` is correctly starting your FastAPI application (e.g., `uvicorn main:app --host 0.0.0.0 --port 80`). If the app isn't truly running inside the container, you won't get any valid responses.

### Cloud Deployments (e.g., AWS, GCP, Azure)

*   **Load Balancers / API Gateways:** These are frequent sources of 404s in the cloud.
    *   **AWS API Gateway:** Check integration requests, mapping templates, and resource paths. It's very common for API Gateway to handle base paths (e.g., `/dev`, `/prod`) that your backend FastAPI app isn't expecting.
    *   **AWS Application Load Balancer (ALB):** Verify listener rules and target group health checks. Is the ALB forwarding traffic to the correct path on your FastAPI service?
    *   **GCP Cloud Run / Azure Container Apps:** While generally simpler, ensure that any base path or routing rules defined at the platform level align with your FastAPI app's expected routes.
*   **Deployment Artifact:** Confirm that the correct, latest version of your code has actually been deployed. Sometimes, an old version might be running that doesn't include newly added routes.
*   **Networking:** While less likely to cause a 404 (more likely connection timeouts), always ensure your security groups, network ACLs, and firewalls allow traffic to reach your FastAPI service on the correct port.

## Frequently Asked Questions

**Q: Why do I get a 404 even though my code explicitly defines the route?**
**A:** This almost always boils down to a mismatch. Either the client is sending a request that doesn't exactly match your route definition (path or HTTP method), or a router containing your route hasn't been `app.include_router()`ed. Check your `/docs` page to see what FastAPI *actually* thinks is available.

**Q: Does the order of routes matter in FastAPI?**
**A:** Yes, it can, especially for routes with path parameters or wildcard paths. FastAPI processes routes in the order they are defined. A more specific route (e.g., `/items/all`) should generally be defined *before* a more general route that could "catch" it (e.g., `/items/{item_id}`). If `/items/{item_id}` comes first, it might incorrectly match `/items/all` as a parameter.

**Q: I'm using an API Gateway (like AWS API Gateway); could that be causing the 404?**
**A:** Absolutely. Misconfigured API Gateway rules, path mapping, or integration requests are a very common cause of 404s. The gateway might be stripping part of the path, or forwarding to the wrong internal path on your FastAPI service. Always check the API Gateway logs and configuration thoroughly.

**Q: What's the difference between a 404 and a 405 (Method Not Allowed)?**
**A:** A `404 Not Found` means the *path itself* doesn't exist on the server for *any* HTTP method. A `405 Method Not Allowed` means the path *does* exist, but the specific HTTP method used in the request (e.g., `POST`) is not allowed for that resource (e.g., it only accepts `GET` requests). If you receive a 405, you're closer to a valid endpoint; you just need to adjust your method.

## Related Errors