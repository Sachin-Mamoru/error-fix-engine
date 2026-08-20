# starlette.exceptions.HTTPException: 404 Not Found
> Encountering `starlette.exceptions.HTTPException: 404 Not Found` means your FastAPI application couldn't find the requested endpoint; this guide explains how to fix it.

## What This Error Means

When you see a `starlette.exceptions.HTTPException: 404 Not Found` error, it signifies that a client (like a web browser, a mobile app, or another API service) has made a request to your FastAPI application for a resource or URL path that the application does not recognize or have a defined route for.

In the context of web services, "404 Not Found" is a standard HTTP status code indicating that the server could not find the requested resource. Starlette, the lightweight ASGI framework that FastAPI is built upon, is responsible for handling these HTTP responses. So, while you're using FastAPI, the error often surfaces directly from Starlette's core, meaning the routing mechanism deep within your application couldn't match the incoming request to any of your defined API endpoints.

This error is purely server-side in its reporting, but its root cause can often be traced back to either a client requesting an invalid path or the server (your FastAPI app) not correctly defining or exposing the intended path.

## Why It Happens

A 404 error fundamentally happens when the requested Uniform Resource Locator (URL) does not correspond to any known handler or resource on the server. For a FastAPI application, this means the incoming HTTP request's path (e.g., `/users/123` or `/items`) and its HTTP method (e.g., `GET`, `POST`, `PUT`, `DELETE`) didn't find a match among the routes you've defined using decorators like `@app.get()`, `@app.post()`, etc.

The server isn't necessarily "down" or "broken"; it's simply stating, "I received your request for this specific path, but I don't have anything configured to respond to it."

## Common Causes

In my experience, 404s are among the most frequent errors encountered during API development and deployment. Here are the common culprits:

1.  **Typos in the URL Path:** This is the simplest and often most overlooked cause. A slight misspelling in the client's request URL (e.g., `/user` instead of `/users`, or `/items/list` instead of `/items`) will lead to a 404 if the misspelled path doesn't exist.
2.  **Missing Route Definition:** The endpoint the client is trying to reach simply hasn't been defined in your FastAPI application code. Perhaps it was forgotten, commented out, or accidentally deleted.
3.  **Incorrect HTTP Method:** FastAPI routes are specific to HTTP methods. If you define an endpoint with `@app.get("/items")` but the client sends a `POST` request to `/items`, you'll get a 404 because no `POST` handler exists for that path. The error message might sometimes indicate `Method Not Allowed` (405) if a route exists for the path but not for the specific method, but a pure 404 can also occur if no route *at all* matches the path, regardless of method.
4.  **Unincluded APIRouter:** When organizing your FastAPI application into multiple files using `APIRouter`, it's easy to forget to `include` the router in your main application instance (e.g., `app.include_router(my_router)`). If a router isn't included, none of its routes will be registered with the main application.
5.  **Base Path Mismatch:** If your FastAPI application is deployed behind a reverse proxy, API Gateway, or in a sub-directory, it might expect a base path (e.g., `/api/v1`). If the client makes a request to `/items` but the server expects `/api/v1/items`, a 404 will occur. This is particularly common in cloud deployments or microservice architectures.
6.  **Case Sensitivity:** While not all operating systems or web servers are case-sensitive for paths, it's good practice to treat API paths as such. `/Users` is different from `/users`. Ensure consistency.
7.  **Application Not Running/Routes Not Loaded:** The FastAPI application might not be fully started, or the specific module containing the routes might not have been imported, preventing the routes from being registered.
8.  **Middleware Interference:** While less common for a straightforward 404, certain middleware could theoretically rewrite paths in a way that leads to an unmatchable URL, or short-circuit the request before it reaches FastAPI's router.

## Step-by-Step Fix

Troubleshooting a 404 error in FastAPI usually involves systematically checking the client's request against your server's definitions.

1.  **Verify the Requested URL and Method:**
    *   **Client Side:** First, confirm the exact URL and HTTP method (GET, POST, PUT, DELETE, etc.) being sent by the client. Use tools like `curl`, Postman, Insomnia, your browser's developer console (Network tab), or your application's logs.
    *   *Example `curl` request:*
        ```bash
        curl -X GET http://localhost:8000/api/v1/items
        ```
    *   Pay close attention to spelling, slashes (`/`), and query parameters. A missing slash can sometimes change how a proxy or router interprets the path.

2.  **Inspect FastAPI Route Definitions:**
    *   Go through your FastAPI application code, specifically the files where you define your API endpoints.
    *   Look for the `@app.get()`, `@app.post()`, `@router.get()`, etc., decorators.
    *   **Does a decorator exist for the exact path *and* HTTP method the client is requesting?**
    *   *Correct example:*
        ```python
        from fastapi import FastAPI

        app = FastAPI()

        @app.get("/items")
        async def read_items():
            return [{"item_id": "Foo"}, {"item_id": "Bar"}]
        ```
        If the client requests `GET /items`, this will work. If they request `GET /item`, it will 404. If they request `POST /items`, it will 404.

3.  **Check APIRouter Inclusion (If Applicable):**
    *   If you're using `APIRouter` to structure your application, ensure that all your routers are correctly included in the main FastAPI application instance.
    *   **Is `app.include_router(your_router_instance)` called for every router you expect to be active?**
    *   *Example:*
        ```python
        # main.py
        from fastapi import FastAPI
        from .routers import items, users # Assuming these are modules with APIRouter instances

        app = FastAPI()

        app.include_router(items.router, prefix="/api/v1")
        app.include_router(users.router, prefix="/api/v1")

        @app.get("/")
        async def read_root():
            return {"message": "Welcome"}
        ```
        If `items.router` was not included, all paths defined within `items.router` would return 404s.

4.  **Review Base Path/Prefix Configuration:**
    *   If your application is served under a specific base path (e.g., `/my-service/api`), confirm that:
        *   Your `APIRouter` instances use the `prefix` argument correctly.
        *   The client is including this prefix in its requests.
        *   Any reverse proxies or API Gateways are configured to forward requests to the correct path *without* stripping necessary parts of the URL. I've spent hours debugging 404s only to find a load balancer was stripping `/api` from the path before it hit my container.

5.  **Check Application Startup and Logs:**
    *   **Is your FastAPI application actually running?** Verify the `uvicorn` process is active.
    *   **Are there any startup errors in your application logs?** Sometimes a critical module import failure can prevent routes from being registered.
    *   Add temporary logging within your route handlers to confirm if the code is even being reached.
        ```python
        import logging
        from fastapi import FastAPI

        logger = logging.getLogger(__name__)
        app = FastAPI()

        @app.get("/items/{item_id}")
        async def read_item(item_id: str):
            logger.info(f"Received request for item_id: {item_id}")
            return {"item_id": item_id}
        ```
        If you don't see the log message, the router is not being hit.

6.  **Restart Your Application:** A classic but often effective step. Sometimes, especially in local development, changes to route definitions might not be picked up by `uvicorn`'s reload feature, or a previous crash left the application in a bad state.

## Code Examples

Here are some concise, copy-paste ready code examples to illustrate common scenarios.

**1. A Working FastAPI Endpoint:**

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
async def say_hello():
    return {"message": "Hello, World!"}

# To run: uvicorn main:app --reload
# Access: http://localhost:8000/hello
```
*   If you request `GET /hello`, you'll get `{"message": "Hello, World!"}`.
*   If you request `GET /goodbye` or `POST /hello`, you'll get a 404.

**2. Demonstrating a 404 with a Missing Route:**

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

# No route defined for '/users' or '/items'
@app.get("/")
async def read_root():
    return {"message": "Welcome to the root!"}

# To run: uvicorn main:app --reload
# Access: http://localhost:8000/users will result in a 404
# Access: http://localhost:8000/items will result in a 404
```

**3. Correct APIRouter Usage to Avoid 404s:**

```python
# routers/items.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/items")
async def read_items():
    return [{"item_name": "Laptop"}, {"item_name": "Mouse"}]

@router.get("/items/{item_id}")
async def read_single_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}
```

```python
# main.py
from fastapi import FastAPI
from routers import items # Assuming routers/items.py is in the same directory or importable

app = FastAPI()

app.include_router(items.router, prefix="/api/v1", tags=["items"])

@app.get("/")
async def read_root():
    return {"message": "Main application root"}

# To run: uvicorn main:app --reload
# Access: http://localhost:8000/api/v1/items
# Access: http://localhost:8000/api/v1/items/123
# Access: http://localhost:8000/items will result in a 404 because of the prefix.
```

**4. Client Request Example (using `requests` library):**

```python
import requests

BASE_URL = "http://localhost:8000"

try:
    response = requests.get(f"{BASE_URL}/api/v1/items") # This should work with the previous example
    response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
    print("Success:", response.json())
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
except requests.exceptions.ConnectionError as e:
    print(f"Connection Error: {e}")

try:
    response = requests.get(f"{BASE_URL}/nonexistent_path") # This will likely 404
    response.raise_for_status()
    print("Success:", response.json())
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error for nonexistent_path: {e.response.status_code} - {e.response.text}")
```

## Environment-Specific Notes

The context in which your FastAPI application runs can influence how 404 errors manifest or are resolved.

### Cloud (AWS, GCP, Azure)

*   **API Gateway / Load Balancer Configuration:** In cloud environments, your FastAPI app often sits behind an API Gateway (like AWS API Gateway, Azure API Management) or a Load Balancer. These services have their own routing rules. I've frequently seen 404s when the API Gateway's path mapping is incorrect or when it's configured to strip a base path that your FastAPI application expects (or vice-versa). Double-check the path mapping, integration type, and stage variables.
*   **Serverless Functions (AWS Lambda, Google Cloud Functions, Azure Functions):** When deploying FastAPI as a serverless function, the proxy integration or HTTP trigger settings are crucial. Ensure that the function's event trigger is correctly configured to pass the full request path to your ASGI application and that your `main.py` is correctly exposed. Cold starts can sometimes mask issues, making it seem like a 404 before the app fully initializes, but this is less common.
*   **Container Orchestration (EKS, GKE, AKS):** If running in Kubernetes, check your Ingress controller rules, Service definitions, and Pod logs. An Ingress might not be routing traffic to the correct Service, or the Service might not be correctly targeting your FastAPI Pods, leading to a network-level 404 before FastAPI even sees the request.

### Docker

*   **Port Mapping:** Ensure that the port your FastAPI application listens on inside the container (e.g., `8000`) is correctly mapped to a port on the host machine using `-p` in `docker run` (e.g., `-p 8000:8000`). If not, the request might not reach the container.
*   **`CMD`/`ENTRYPOINT`:** Verify that your `Dockerfile`'s `CMD` or `ENTRYPOINT` properly starts `uvicorn` and points to your FastAPI application instance (e.g., `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`). If the application isn't started correctly, all routes will effectively be non-existent.
*   **Container Health:** Check `docker logs <container_id>` for any startup errors that might prevent your application from initializing properly and registering its routes.

### Local Development

*   **`uvicorn` Not Running:** The most basic check: Is `uvicorn` actually running and listening on the expected port?
*   **File Changes Not Reloaded:** If you're using `uvicorn main:app --reload`, sometimes changes aren't immediately picked up, especially with complex import structures. A manual restart of `uvicorn` can often resolve this.
*   **Environment Variables:** If your application dynamically builds routes or base paths based on environment variables, ensure these are correctly set in your local development environment. I've often forgotten to set `API_PREFIX` and gotten 404s on all my routes.
*   **Virtual Environment:** Make sure you're working within the correct virtual environment and that all FastAPI and Starlette dependencies are installed.

## Frequently Asked Questions

**Q: Is `starlette.exceptions.HTTPException: 404 Not Found` a client-side or server-side error?**
**A:** It's a server-side error *reporting* a client-side issue. The server is correctly responding with a 404 status code because the client requested a resource the server couldn't find. The error itself originates from the server (your FastAPI application).

**Q: Can middleware cause a 404 error in FastAPI?**
**A:** Yes, although it's less common for a direct 404. If a custom middleware prematurely terminates a request, rewrites the path in an unexpected way, or redirects to a non-existent URL, it could lead to a 404.

**Q: I see a 404, but I'm certain the route exists in my code. What gives?**
**A:** This is a common head-scratcher. Revisit the "Common Causes" and "Step-by-Step Fix" sections. The most frequent culprits are: a typo in the client's request or the server's route definition, an incorrect HTTP method (e.g., `POST` instead of `GET`), a missing `app.include_router()` call, or the application not having been restarted to pick up the new route.

**Q: How can I customize the 404 error response in FastAPI?**
**A:** You can define a custom exception handler for `HTTPException` (specifically for status code 404).

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"message": "Oops! The page you're looking for was not found."},
        )
    return await StarletteHTTPException(request, exc) # Fallback for other HTTP exceptions

@app.get("/items/{item_id}")
async def read_item(item_id: str):
    return {"item_id": item_id}
```

**Q: Why do I get a 404 when using path parameters like `/items/{item_id}`?**
**A:** This often happens if the client sends a request that doesn't match the path parameter's type hint (e.g., `/items/abc` when `item_id: int` is expected, which would typically be a 422 Unprocessable Entity, but depending on the exact path and definitions can result in a 404 if no *other* matching path exists). More commonly, it's a mismatch in the static part of the path, like `/item/{item_id}` instead of `/items/{item_id}`.

## Related Errors
*(none)*