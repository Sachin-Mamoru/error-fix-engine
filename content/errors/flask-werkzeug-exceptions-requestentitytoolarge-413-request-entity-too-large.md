# werkzeug.exceptions.RequestEntityTooLarge: 413 Request Entity Too Large
> Encountering a 413 Request Entity Too Large error in Flask means your client sent too much data; this guide explains how to fix it.

## What This Error Means

The `werkzeug.exceptions.RequestEntityTooLarge: 413 Request Entity Too Large` error indicates that the server, in this case, your Flask application or a component in front of it, refused to process a request because its payload body is larger than the configured limit.

In practical terms, when a client (like a web browser or another API service) sends an HTTP request, it often includes data in the request body – perhaps a file upload, a large JSON object, or form data. The `413 Request Entity Too Large` HTTP status code is the server's way of saying, "I'm not processing this because the data you sent is too big for me to handle based on my current settings." `werkzeug` is Flask's underlying WSGI utility library, and it's responsible for generating this specific exception when the size limit is hit within the Flask application itself.

## Why It Happens

This error doesn't just pop up randomly; it's a direct consequence of a mismatch between the size of the data a client is sending and the size limit configured on the server-side. Servers, web frameworks, and proxies often impose these limits for several good reasons:

1.  **Resource Management:** Processing very large requests consumes significant memory, CPU, and network bandwidth. Limits prevent a single large request from monopolizing server resources and impacting other users or services.
2.  **Security:** Large payload limits can be exploited in denial-of-service (DoS) attacks. An attacker could send deliberately oversized requests to exhaust server resources. Restricting size helps mitigate this.
3.  **Preventing Misuse:** It ensures clients only send data sizes that the application is designed to handle. If your application expects small JSON payloads, allowing gigabyte uploads could expose vulnerabilities or lead to unexpected behavior.

The core issue is always a configuration setting, whether it's within your Flask application, the web server (like Nginx or Apache) sitting in front of Flask, or even a load balancer or API Gateway further upstream.

## Common Causes

In my experience, this error typically surfaces in a few common scenarios:

*   **Large File Uploads:** This is the most frequent culprit. Users attempting to upload images, videos, documents, or other large files through a Flask endpoint that isn't configured to accept them.
*   **Extensive JSON/XML Payloads:** APIs dealing with complex data structures, especially those involving bulk operations or data synchronization, might send or receive JSON or XML bodies that exceed default limits. I've seen this in production when an integration partner started sending significantly more data than anticipated in a single API call.
*   **Base64 Encoded Data:** Sometimes, binary data (like images) is embedded directly into JSON or form data as a Base64 string. Base64 encoding increases the data size by about 33%, which can quickly push seemingly moderate-sized files over the limit.
*   **Development vs. Production Differences:** An application might work perfectly during local development because the local server (e.g., `flask run`) often doesn't have strict size limits, or you're not using a reverse proxy. When deployed to production, Nginx, Apache, or a cloud load balancer with default limits can suddenly introduce this error.

## Step-by-Step Fix

Troubleshooting a `413 Request Entity Too Large` error involves working your way up the stack, from your Flask application to any reverse proxies or load balancers.

### 1. Adjust Flask's `MAX_CONTENT_LENGTH`

Flask itself has a built-in mechanism to limit the size of incoming requests. This is often the first place to check.

1.  **Understand the Limit:** By default, Flask (via Werkzeug) does not impose a `MAX_CONTENT_LENGTH` limit. However, if it's set, it will raise `RequestEntityTooLarge` when exceeded. This limit is specified in bytes.
2.  **Set the Limit:** You can set `MAX_CONTENT_LENGTH` in your Flask application configuration. A value of `16 * 1024 * 1024` would allow payloads up to 16 MB.

    ```python
    from flask import Flask, request, jsonify

    app = Flask(__name__)
    # Set maximum content length to 16 MB
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 Megabytes

    @app.route('/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Simulate file processing
        # file.save(os.path.join('/tmp', file.filename))
        return jsonify({"message": f"File {file.filename} uploaded successfully!"}), 200

    if __name__ == '__main__':
        app.run(debug=True)
    ```

    Remember that this limit is *only* for the Flask application itself. If a web server or load balancer upstream has a lower limit, it will hit that first.

### 2. Configure Your Web Server (Nginx, Apache)

Most production Flask applications run behind a reverse proxy like Nginx or Apache. These servers have their own client body size limits.

#### For Nginx:

1.  **Locate Nginx Configuration:** This is usually in `/etc/nginx/nginx.conf`, `/etc/nginx/sites-available/your_app`, or a similar location.
2.  **Add/Modify `client_max_body_size`:** You can set `client_max_body_size` in the `http`, `server`, or `location` block.

    ```nginx
    # In /etc/nginx/nginx.conf or your site's config file
    http {
        # ... other http settings ...
        client_max_body_size 20M; # Set a global limit of 20 Megabytes

        server {
            # ... other server settings ...
            client_max_body_size 30M; # Override for this specific server to 30MB

            location /upload {
                client_max_body_size 50M; # Override for this specific upload path to 50MB
                # ... proxy_pass settings for your Flask app ...
            }
        }
    }
    ```

    Choose the appropriate scope. I typically set it in the `server` block for the application it applies to.
3.  **Test and Reload Nginx:** After making changes, always test your configuration and reload Nginx.

    ```bash
    sudo nginx -t
    sudo systemctl reload nginx
    ```

#### For Apache:

1.  **Locate Apache Configuration:** This is typically in `httpd.conf` or a virtual host configuration file (`.conf` in `sites-available`).
2.  **Add/Modify `LimitRequestBody`:** Use the `LimitRequestBody` directive. It's specified in bytes.

    ```apache
    # In your VirtualHost or .htaccess file
    <VirtualHost *:80>
        ServerName your_domain.com
        # ... other settings ...

        # Set limit to 20 MB (20 * 1024 * 1024 bytes)
        LimitRequestBody 20971520

        <Directory /var/www/your_app>
            # You can also set it within a Directory block
            # LimitRequestBody 20971520
        </Directory>
    </VirtualHost>
    ```
3.  **Restart Apache:**

    ```bash
    sudo systemctl restart apache2 # Or httpd depending on your OS
    ```

### 3. Check Load Balancers / API Gateways (e.g., AWS ALB, API Gateway)

If your application is deployed in a cloud environment, there might be another layer of limits.

*   **AWS Application Load Balancer (ALB):** ALBs have a default request size limit of 1MB (1048576 bytes) for POST requests. This is a common pitfall. You need to ensure your client sends data in smaller chunks or use S3 pre-signed URLs for larger uploads. ALBs do not have a configurable setting to increase this limit directly for the request body itself; for large uploads, the pattern changes to direct client-to-S3 uploads. For other request types where the payload is part of the request, 1MB is the hard limit.
*   **AWS API Gateway:** API Gateway has a default payload size limit of 10 MB for request and response bodies. This *is* configurable. Go to your API Gateway console, navigate to your API, then `Settings`. You can adjust the "Payload size limit" there.
*   **Azure Application Gateway / Front Door:** These services also have their own request size limits that might need adjustment. For Application Gateway, look for "Maximum request body size (KB)" in WAF policies if enabled, or generally, its configuration for backend pools.

### 4. Client-Side Considerations

While the fix is server-side, it's worth checking if the client is attempting to send an unreasonably large request. Can the client-side logic be improved to:
*   **Split large files:** Break a huge file into smaller chunks and upload them sequentially.
*   **Optimize data:** Ensure that no unnecessary data is being sent.
*   **Provide feedback:** Inform the user if their file/data size exceeds the allowed limit *before* sending, rather than waiting for a server error.

## Code Examples

### Flask Application Configuration

To allow payloads up to 50 MB in your Flask app:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 Megabytes

@app.route('/data-ingest', methods=['POST'])
def handle_large_data():
    if request.is_json:
        data = request.get_json()
        # Process the large JSON data
        print(f"Received JSON data size: {len(request.data) / (1024*1024):.2f} MB")
        return jsonify({"status": "success", "message": "Data processed"}), 200
    return jsonify({"error": "Request must be JSON"}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### Nginx Configuration Snippet

To increase the client body size limit for a specific location in Nginx:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location /api/upload-files {
        # Allow requests up to 100 Megabytes for this path
        client_max_body_size 100M;
        proxy_pass http://127.0.0.1:5000; # Your Flask app
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        # Default limit for other paths (e.g., 20 MB)
        client_max_body_size 20M;
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Environment-Specific Notes

The `413 Request Entity Too Large` error can behave differently depending on your deployment environment.

*   **Local Development:** When you run `flask run` directly, Flask uses Werkzeug's development server. This server typically doesn't have strict upstream size limits, so `MAX_CONTENT_LENGTH` in your Flask app is usually the only relevant setting. You might not encounter a `413` locally unless you explicitly set `MAX_CONTENT_LENGTH` to a very low value. This disparity often leads engineers to believe their code is fine until it hits production.
*   **Docker/Containerized Environments:** If your Flask app is containerized, pay close attention to the web server configuration *within* the container. Often, Nginx or Gunicorn is bundled. If you're running Nginx in a separate container acting as a reverse proxy to your Flask app container, its `client_max_body_size` setting is critical. Ensure your Dockerfile or Docker Compose mounts the correct Nginx configuration if you're modifying it. I've often seen teams forget to update the Nginx config volume when increasing limits, leading to frustrating `413` errors.
*   **Cloud Deployments (AWS, Azure, GCP):**
    *   **AWS:** As mentioned, AWS ALBs have a hard 1MB limit for request bodies. If you need larger uploads, the common pattern is to bypass your Flask API for the actual file transfer. Instead, your Flask app generates a pre-signed S3 URL, which the client then uses to directly upload the file to S3. This offloads the heavy lifting from your application and load balancer. For non-file large JSON payloads, consider breaking them down or using API Gateway with an increased payload limit.
    *   **Azure App Services/Function Apps:** These platforms might have their own ingress limits. For App Services, there's typically a 100MB default request body size, which is quite generous, but it's worth verifying if you're hitting limits with truly massive files. If you're using Azure API Management, it also has configurable request size limits.
    *   **Google Cloud Platform (GCP) Load Balancers / Cloud Run:** GCP's external HTTP(S) Load Balancers have a maximum request size of 32MB by default for the *entire* request, including headers and body. For Cloud Run, the request body limit is 32MB. Be mindful of these.

In any cloud environment, it's crucial to consult the specific documentation for the load balancers, API gateways, and compute platforms you are using, as they often impose limits beyond your direct application configuration.

## Frequently Asked Questions

**Q: Can I set `MAX_CONTENT_LENGTH` to an extremely high value (e.g., 1GB)?**
**A:** While technically possible, it's generally not recommended. Extremely high limits can expose your application to denial-of-service attacks or simply consume excessive server resources, impacting performance for other users. Always set a limit that is reasonable for your application's expected use case.

**Q: Why do I get a `413` in production but not locally?**
**A:** This is a classic symptom. It almost always means an upstream component in your production environment (like Nginx, Apache, or a cloud load balancer) has a lower request body limit than your local development server or Flask's `MAX_CONTENT_LENGTH`. You need to adjust the configuration of that upstream component.

**Q: Does `MAX_CONTENT_LENGTH` apply to all HTTP methods?**
**A:** Yes, `MAX_CONTENT_LENGTH` in Flask applies to the content length of any incoming request with a body, regardless of the HTTP method (POST, PUT, etc.).

**Q: How can I handle very large file uploads (e.g., >100MB) with Flask?**
**A:** For very large files, it's often more efficient and robust to avoid sending them directly through your Flask application. Instead, implement a pattern where your Flask API generates a pre-signed URL (e.g., for AWS S3, Azure Blob Storage, or GCP Cloud Storage). The client then uploads the file directly to the cloud storage, bypassing your application's direct ingress. Your Flask app can then be notified (e.g., via a webhook or message queue) once the upload is complete.

## Related Errors