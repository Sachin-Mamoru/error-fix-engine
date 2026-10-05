# werkzeug.exceptions.NotFound: 404 Not Found: The requested URL was not found on the server.
> Encountering a 404 Not Found error in Flask means the server couldn't find a route matching your request; this guide explains how to identify and fix the underlying issue.

## What This Error Means

The `werkzeug.exceptions.NotFound: 404 Not Found` error in a Flask application is Flask's standard way of signaling an HTTP 404 status. In plain terms, it means the server successfully received your request, but it couldn't find any resource or endpoint (a "route") configured to handle the specific URL you requested. It's a server-side response indicating that the path you're trying to access doesn't exist within the application's defined routing table. This is distinct from a server error (like a 500 Internal Server Error), where the server found a route but failed to process it.

## Why It Happens

At its core, this error occurs because there's a mismatch between the URL a client requested and the set of URLs (or "routes") that your Flask application has been programmed to respond to. Flask uses a routing system (powered by Werkzeug) to map incoming URLs to specific Python functions. When an incoming URL doesn't match any of the patterns defined by your `@app.route()` or `@blueprint.route()` decorators, Flask raises this `NotFound` exception. I've seen this in production when a new API endpoint was deployed without the corresponding client-side update, leading to clients hitting old or incorrect paths.

## Common Causes

Here are the most frequent culprits behind a `404 Not Found` in Flask:

1.  **Typographical Errors in the URL:** The simplest and most common cause. A typo in the client's request URL (e.g., `/userss` instead of `/users`) will lead to a 404 if no route matches the misspelled path.
2.  **Missing or Incorrect Route Definition:** The endpoint you're trying to reach might not have a corresponding `@app.route()` or `@blueprint.route()` decorator, or the path defined in the decorator is incorrect.
3.  **Wrong HTTP Method:** Flask routes can be configured to respond only to specific HTTP methods (GET, POST, PUT, DELETE, etc.). If a route is defined for `methods=['POST']` but a client sends a `GET` request to that URL, Flask will raise a 404. While sometimes a `405 Method Not Allowed` is returned for existing routes with wrong methods, a `404` can occur if the method *also* causes the route matching to fail in a subtle way, or if an OPTIONS request for a non-existent route is made.
4.  **Incorrect Blueprint Registration:** If you're using Flask Blueprints to organize your application, failing to register a blueprint with the main Flask app, or registering it with an incorrect URL prefix, will make all its routes inaccessible.
5.  **Trailing Slashes:** Flask's `strict_slashes` behavior (True by default for `app.route()`) can be a source of confusion. `/users` and `/users/` are often treated as distinct by default unless specified otherwise. Requesting `/users/` when the route is defined as `@app.route('/users')` (and `strict_slashes` is enabled) can result in a 404.
6.  **Proxy or Load Balancer Configuration:** In complex deployments, a reverse proxy (like Nginx) or a load balancer might be configured to rewrite URLs or forward requests incorrectly, preventing the correct URL from ever reaching your Flask application.
7.  **Variable Rules Mismatch:** If your route uses variable rules (e.g., `@app.route('/users/<int:user_id>')`), a request like `/users/abc` instead of `/users/123` will result in a 404 because `abc` cannot be converted to an integer.

## Step-by-Step Fix

Troubleshooting a 404 involves systematically checking the potential failure points.

1.  **Verify the Requested URL:**
    *   **Action:** Double-check the URL being requested by the client (e.g., in your browser's address bar, cURL command, Postman, or API logs).
    *   **Check For:** Typos, case sensitivity (though Flask routes are generally case-sensitive), and the presence or absence of a trailing slash.
    *   **Example (cURL):**
        ```bash
        # This might be correct
        curl -X GET http://localhost:5000/api/v1/users

        # This might have a typo
        curl -X GET http://localhost:5000/api/v1/userz
        ```

2.  **Inspect Your Flask Routes:**
    *   **Action:** Review your Flask application code (`app.py`, blueprint files) to confirm that a route exactly matching the requested URL *and* HTTP method is defined.
    *   **Tool:** You can programmatically list all registered routes in your Flask application. This is incredibly useful.
    *   **Example:**
        ```python
        from flask import Flask

        app = Flask(__name__)

        @app.route('/')
        def index():
            return "Hello, world!"

        @app.route('/api/v1/users', methods=['GET'])
        def get_users():
            return "List of users"

        if __name__ == '__main__':
            with app.test_request_context(): # Or run with app.run(debug=True)
                for rule in app.url_map.iter_rules():
                    print(f"Endpoint: {rule.endpoint}, Methods: {rule.methods}, Path: {rule.rule}")
        ```
        Look for your expected path in the output. If it's not there, you know why.

3.  **Confirm the HTTP Method:**
    *   **Action:** Ensure the client is sending the correct HTTP method (GET, POST, PUT, DELETE, etc.) for the intended route.
    *   **Check For:** A route defined as `@app.route('/data', methods=['POST'])` will 404 if accessed via `GET`.
    *   **Example (Route definition):**
        ```python
        @app.route('/submit_form', methods=['POST'])
        def handle_form_submission():
            # ... process POST data
            return "Form submitted!"
        ```
        If you try to access `/submit_form` with a GET request, you'll get a 404.

4.  **Debug with Flask's Debug Mode:**
    *   **Action:** Run your Flask application in debug mode (`app.run(debug=True)`). Flask's interactive debugger will often provide more context, including a traceback that might hint at where the routing failed.
    *   **Warning:** Never run with `debug=True` in production.

5.  **Verify Blueprint Registration:**
    *   **Action:** If using blueprints, ensure they are correctly imported and registered with the main Flask application using `app.register_blueprint()`.
    *   **Check For:** Correct `url_prefix` if applicable.
    *   **Example:**
        ```python
        # api_blueprint.py
        from flask import Blueprint

        api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

        @api_bp.route('/products')
        def get_products():
            return "List of products from API"

        # app.py
        from flask import Flask
        from api_blueprint import api_bp

        app = Flask(__name__)
        app.register_blueprint(api_bp) # Is this line missing or incorrect?

        @app.route('/')
        def index():
            return "Home page"

        # If api_bp is not registered, or registered without url_prefix,
        # accessing /api/v1/products will 404.
        ```

6.  **Consider Trailing Slashes:**
    *   **Action:** Test both `/my_path` and `/my_path/` if your route is defined simply as `@app.route('/my_path')`. Flask's default `strict_slashes=True` behavior means these are distinct unless `strict_slashes=False` is set on the route, or `url_map.strict_slashes = False` is set on the app level.
    *   **Recommendation:** Be explicit or consistent. I usually ensure all API endpoints are canonical without trailing slashes.

7.  **Check Proxy/Gateway Configuration (Advanced):**
    *   **Action:** If your Flask app is behind Nginx, Apache, an API Gateway, or a load balancer, examine its configuration. These layers can rewrite URLs before they reach your Flask application.
    *   **Check For:** `proxy_pass` directives in Nginx, `RewriteRule` in Apache, or path-based routing rules in cloud load balancers. A common issue is a proxy stripping part of the path before forwarding.

## Code Examples

**Basic Flask app with routes:**

```python
from flask import Flask, jsonify

app = Flask(__name__)

# This route exists
@app.route('/')
def home():
    return "Welcome to the API!"

# This route exists for GET requests
@app.route('/users', methods=['GET'])
def get_users():
    return jsonify({"users": ["Alice", "Bob"]})

# This route exists for POST requests
@app.route('/users', methods=['POST'])
def create_user():
    # Imagine processing request.json here
    return jsonify({"message": "User created"}), 201

# This route exists with a variable rule (integer)
@app.route('/users/<int:user_id>')
def get_user_by_id(user_id):
    return jsonify({"user_id": user_id, "name": f"User {user_id}"})

if __name__ == '__main__':
    app.run(debug=True)
```

**Testing the above (assuming `app.py`):**

```bash
# Correct: Will return "Welcome to the API!"
curl http://127.0.0.1:5000/

# Correct: Will return JSON for users
curl http://127.0.0.1:5000/users

# Correct: Will return JSON for user 123
curl http://127.0.0.1:5000/users/123

# Correct: Will create a user (POST request)
curl -X POST http://127.0.0.1:5000/users -H "Content-Type: application/json" -d '{"name": "Charlie"}'

# INCORRECT: /products does not exist -> 404
curl http://127.0.0.1:5000/products

# INCORRECT: /users only accepts GET/POST -> 404 (or 405 depending on Werkzeug version/strictness)
curl -X PUT http://127.0.0.1:5000/users

# INCORRECT: /users/<int:user_id> expects an integer -> 404
curl http://127.0.0.1:5000/users/abc
```

## Environment-Specific Notes

The context of your deployment environment significantly impacts how `404 Not Found` errors manifest and are debugged.

*   **Local Development:**
    *   Running `app.run(debug=True)` is your best friend. The interactive debugger page provides a detailed traceback, showing exactly where Flask tried to match the URL and failed. It also lists all registered URL rules, making it easy to spot a missing or mistyped route.
    *   Access directly via `http://127.0.0.1:5000/` or whatever port you're using. Network configuration is usually minimal here.

*   **Docker:**
    *   **Port Mapping:** Ensure your Docker container's internal port (e.g., 5000 for Flask) is correctly mapped to a host port (e.g., `docker run -p 80:5000 ...`). If the mapping is wrong, you might get connection refused, or the request might not reach Flask at all, possibly resulting in a `404` from an upstream proxy or even a browser-level network error.
    *   **Container Network:** If your Flask app is part of a multi-container Docker Compose setup, ensure services can reach each other via their service names (e.g., `http://my-flask-app:5000/`). A client trying to access `localhost` from within another container won't work.
    *   **Gunicorn/uWSGI:** If using a WSGI server, ensure it's correctly configured to serve your Flask app. Issues here might lead to different errors, but a misconfiguration could potentially serve a default 404 page from the WSGI server itself before Flask even gets a chance.

*   **Cloud (AWS, GCP, Azure, etc.):**
    *   **API Gateway/Load Balancer:** This is where things get tricky. Many cloud deployments involve an API Gateway (like AWS API Gateway) or a Load Balancer (ELB, GCP Load Balancer).
        *   **Path Routing:** These services often have path-based routing rules. For instance, `/api/v1/*` might be forwarded to your Flask service. If your API Gateway configuration sends `/api/v1/users` to your Flask app, but your app expects `/users` (because the API Gateway strips the prefix), you'll get a 404. I've often seen engineers struggle here, as the URL *they* requested looks correct, but what hits the Flask app is different.
        *   **Stage/Deployment:** Ensure your API Gateway stage is deployed, or your load balancer listener rules are correctly configured and applied.
        *   **Domain Mapping:** If you're using a custom domain, ensure it correctly points to your API Gateway or Load Balancer.
    *   **Reverse Proxies (Nginx, Caddy, Apache):** If you manually configure a reverse proxy in a cloud VM:
        *   **`proxy_pass`:** Verify the `proxy_pass` directive in Nginx or similar settings. Is it pointing to the correct internal IP/port of your Flask application? Is it including or stripping path prefixes as expected?
        *   **Logging:** Check the proxy's access logs *and* error logs. They will show what URL the proxy received and what URL it attempted to forward to your Flask app. This is crucial for pinpointing where the path deviation occurs.
    *   **Serverless (e.g., AWS Lambda with Zappa/Chalice):**
        *   The URL routing is often managed by the framework's integration with the API Gateway. Double-check your framework's (e.g., Zappa's `zappa_settings.json`) configuration for base paths or stage settings.

## Frequently Asked Questions

**Q: Is a 404 a server-side or client-side error?**
**A:** A 404 Not Found error is a *server-side* response indicating that the server could not find the requested resource. However, the *cause* of the 404 often originates from the *client* requesting a non-existent URL or an incorrect method. So, while it's a server response, the responsibility for fixing it might lie with either the client (wrong URL) or the server (missing route definition).

**Q: What's the difference between a 404 Not Found and a 500 Internal Server Error?**
**A:** A **404 Not Found** means the server understood the request but couldn't find a resource matching the requested URL. The problem is with the *path*. A **500 Internal Server Error** means the server encountered an unexpected condition that prevented it from fulfilling the request. This usually indicates an unhandled exception or a bug in the code for a route that *does* exist.

**Q: Can a 404 be caused by an unhandled exception in my route?**
**A:** No, not directly. An unhandled exception within a *defined* route would typically result in a 500 Internal Server Error (or a specific error page if you've configured error handling). A 404 specifically occurs *before* any route handler is invoked, because Flask couldn't find a handler for the given URL and method.

**Q: How do I implement a custom 404 error page in Flask?**
**A:** You can register an error handler for the 404 exception using `@app.errorhandler(404)`:

```python
from flask import render_template

@app.errorhandler(404)
def page_not_found(e):
    # render a custom 404.html template or return JSON
    return render_template('404.html'), 404
    # or for APIs:
    # return jsonify({"error": "Resource not found"}), 404
```

**Q: Does Flask differentiate between `/api/v1/users` and `/api/v1/users/`?**
**A:** By default, yes. Flask routes typically have `strict_slashes=True`. This means `/api/v1/users` is treated as a distinct route from `/api/v1/users/`. If you define `@app.route('/api/v1/users')`, accessing `/api/v1/users/` will result in a 404. To make them both work, you can either define two routes or set `strict_slashes=False` on the route or globally on the app. In my personal experience, for APIs, it's best to be explicit and treat the trailing slash as non-canonical or redirect.

## Related Errors
*None*