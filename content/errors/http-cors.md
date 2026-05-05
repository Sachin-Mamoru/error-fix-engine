# CORS Error: Access-Control-Allow-Origin missing or blocked
> Encountering a CORS "Access-Control-Allow-Origin" error means your browser blocked a cross-origin request; this guide explains how to identify and fix the misconfiguration on your server or API.

## What This Error Means

When you encounter the "CORS Error: Access-Control-Allow-Origin missing or blocked" message, it signifies that your web browser has prevented a web page from making a request to an API or server located at a different "origin" than the page itself. This isn't a server error in the traditional sense, but rather a security enforcement by your browser.

CORS stands for Cross-Origin Resource Sharing. It's a security mechanism implemented by browsers to control how web pages in one domain can request resources from another domain. The browser's default security policy, known as the Same-Origin Policy (SOP), prevents such cross-origin requests by default. CORS provides a way for servers to explicitly tell browsers, "Hey, it's okay for this other domain to access my resources."

The specific header central to this error is `Access-Control-Allow-Origin`. When your frontend application (e.g., running on `https://myapp.com`) tries to fetch data from your backend API (e.g., running on `https://api.myapp.com`), the browser sends the request. If the backend server's response does *not* include the `Access-Control-Allow-Origin` header with a value that matches `https://myapp.com` (or `*` for any origin), the browser will block the response and throw this CORS error. You'll typically see messages like "Cross-Origin Request Blocked" or "No 'Access-Control-Allow-Origin' header is present on the requested resource" in your browser's developer console.

## Why It Happens

The fundamental reason this error occurs is the browser's Same-Origin Policy (SOP). SOP is a critical security feature that dictates a web page can only request resources from the exact same protocol, domain, and port from which it originated. For example, a script loaded from `https://example.com/page.html` cannot, by default, make a request to `https://api.example.org/data`. This prevents malicious scripts from one site from reading sensitive data from another site (e.g., your banking site) that you might be logged into in the same browser session.

CORS acts as a controlled exception to SOP. It allows servers to opt-in to cross-origin resource sharing by sending specific HTTP headers in their responses. When a server *fails* to send these correct CORS headers, the browser enforces SOP and blocks the request.

Most often, the problem lies in the server-side configuration of the API or backend service. The server either:
1.  Does not send the `Access-Control-Allow-Origin` header at all.
2.  Sends the `Access-Control-Allow-Origin` header with a value that does not match the origin of the requesting web page. For instance, if your frontend is on `http://localhost:3000` and the API sends `Access-Control-Allow-Origin: https://production.com`, the browser will still block it.
3.  Fails to handle "preflight" `OPTIONS` requests correctly. For non-simple requests (e.g., requests using methods other than `GET`, `HEAD`, `POST` with specific content types, or custom headers), the browser first sends an `OPTIONS` request to query the server about its CORS capabilities. If the server doesn't respond to this preflight request with appropriate CORS headers and a 200 OK status, the actual request will never be sent.

In my experience, this usually points to a misconfiguration in the API's web server (e.g., Nginx, Apache), application framework (e.g., Express, Flask), or API gateway. It's a common stumbling block during development and deployment transitions.

## Common Causes

Identifying the root cause is crucial for a quick fix. Here are the most common scenarios I've encountered that lead to the "Access-Control-Allow-Origin missing or blocked" error:

*   **Missing CORS Headers on the Server:** This is the most straightforward cause. The backend server simply isn't configured to send the `Access-Control-Allow-Origin` header (and related CORS headers like `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`) in its HTTP responses.
*   **Incorrect Origin Specified:** The server *does* send the `Access-Control-Allow-Origin` header, but its value doesn't match the actual origin of your frontend application. For example, the server might be configured to allow `https://www.yourdomain.com` but your frontend is running on `https://dev.yourdomain.com` or `http://localhost:3000`.
*   **Wildcard (`*`) Misuse with Credentials:** If your API requests include credentials (like cookies or HTTP authentication headers), and the server responds with `Access-Control-Allow-Origin: *` along with `Access-Control-Allow-Credentials: true`, the browser will block the request. The `*` wildcard is not permitted when credentials are involved, requiring a specific origin.
*   **Failure to Handle Preflight `OPTIONS` Requests:** Many complex HTTP requests (e.g., those using `PUT`, `DELETE`, or custom headers) trigger a "preflight" `OPTIONS` request from the browser before the actual request. If your server isn't configured to respond to these `OPTIONS` requests with the correct CORS headers and a 200 OK status, the browser will block the subsequent actual request.
*   **Proxy or Load Balancer Stripping Headers:** I've seen this in production when an API sits behind a reverse proxy (like Nginx, Apache) or a load balancer (like AWS ALB). Sometimes, these intermediate layers are misconfigured to strip or overwrite custom headers, including CORS headers, before they reach the client.
*   **CDN Caching Issues:** If your API responses are being cached by a Content Delivery Network (CDN), and the CDN's caching policy doesn't account for CORS headers, it might serve a cached response without the necessary `Access-Control-Allow-Origin` header.
*   **Authentication/Authorization Before CORS:** In some cases, if your API returns an authentication error (like a 401 Unauthorized) *before* the CORS headers are processed by the browser, it can manifest as a CORS error. The browser sees the missing `Access-Control-Allow-Origin` in the 401 response and blocks it, even if a 200 OK response with correct CORS headers *would* have been sent if authentication succeeded.

## Step-by-Step Fix

Troubleshooting CORS errors requires a systematic approach, often starting from the client side and moving towards the server.

1.  **Inspect the Browser Console and Network Tab:**
    *   Open your browser's developer tools (usually F12 or Cmd+Option+I).
    *   Go to the "Console" tab to see the exact error message. This often points directly to the missing header and the problematic origin.
    *   Navigate to the "Network" tab. Reload your page.
    *   Filter for the failing request (it will usually be red or marked with an error).
    *   Select the request and examine its "Headers" tab. Pay close attention to the "Request Headers" (specifically the `Origin` header that your browser sent) and the "Response Headers" (look for `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`). Is `Access-Control-Allow-Origin` present? Does its value match your frontend's `Origin`?
    *   If it was a preflight `OPTIONS` request that failed, ensure it's handled correctly and returns 200 OK with proper CORS headers.

2.  **Verify Server-Side CORS Configuration:**
    *   This is where you'll spend most of your time. Access your API's server code or configuration.
    *   **Check the `Origin` header:** Your server needs to know what origin your browser is sending. Make sure your server-side logic is dynamically or statically configured to allow that specific origin.
    *   **Add/Modify `Access-Control-Allow-Origin`:** This is the primary header. Set its value to the exact origin of your frontend application (e.g., `http://localhost:3000`, `https://your-frontend.com`). If your API is meant to be truly public and has no credential requirements, you *can* use `*`, but be aware of the security implications.
    *   **Handle `OPTIONS` Requests:** Ensure your server/framework explicitly handles `OPTIONS` requests by returning a 200 OK status with all necessary CORS headers. Many frameworks have middleware or decorators for this.
    *   **Allow Methods and Headers:** Make sure `Access-Control-Allow-Methods` includes all HTTP methods your frontend uses (GET, POST, PUT, DELETE, etc.) and `Access-Control-Allow-Headers` includes any custom headers your frontend sends (e.g., `Authorization`, `X-Custom-Header`).
    *   **`Access-Control-Allow-Credentials`:** If your frontend sends cookies or HTTP authentication, this header *must* be set to `true`, and `Access-Control-Allow-Origin` cannot be `*`.

3.  **Inspect Intermediate Infrastructure:**
    *   If your API is behind a reverse proxy (Nginx, Apache), API Gateway (AWS API Gateway, Azure API Management), or a Load Balancer, check their configurations. These components might be overriding or stripping CORS headers.
    *   For Nginx, ensure `add_header` directives are correctly placed within the `location` blocks and that `OPTIONS` requests are handled *before* proxying.
    *   For cloud API Gateways, many have built-in CORS configuration panels that are much easier to use.

4.  **Restart and Retest:** After making any changes to server configurations or code, restart your backend service. Clear your browser cache (or use an incognito window) and retest the request.

## Code Examples

Here are some common ways to configure CORS on various backend technologies.

### Node.js (Express) with `cors` Middleware

The `cors` package is the de-facto standard for handling CORS in Express.

```javascript
const express = require('express');
const cors = require('cors'); // Install with: npm install cors
const app = express();

// Option 1: Allow all origins (for public APIs or quick local dev)
// app.use(cors());

// Option 2: Allow specific origins (recommended for most applications)
const allowedOrigins = [
  'http://localhost:3000', // Your local frontend dev server
  'https://your-frontend-domain.com', // Your production frontend
  'https://staging.your-frontend-domain.com' // Your staging frontend
];

app.use(cors({
  origin: function (origin, callback) {
    // allow requests with no origin (like mobile apps or curl requests)
    // and requests from allowedOrigins list
    if (!origin || allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'], // Explicitly allow methods
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'], // Allow specific headers
  credentials: true // Crucial if your frontend sends cookies or auth headers
}));

// Your API routes
app.get('/data', (req, res) => {
  res.json({ message: 'Hello from your API!' });
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`API running on http://localhost:${PORT}`);
});
```

### Nginx as a Reverse Proxy

If Nginx is proxying requests to your backend, configure it to add CORS headers.

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        # Handle preflight OPTIONS requests
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' 'https://your-frontend-domain.com'; # Specify your frontend origin
            # or 'Access-Control-Allow-Origin' '$http_origin'; to dynamically allow the requesting origin (if not using credentials)
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
            add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
            add_header 'Access-Control-Max-Age' 1728000; # How long browser can cache preflight results (in seconds)
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204; # No Content, 204 status for successful OPTIONS
        }

        # Add CORS headers to all other requests
        add_header 'Access-Control-Allow-Origin' 'https://your-frontend-domain.com'; # Specify your frontend origin
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization';
        add_header 'Access-Control-Allow-Credentials' 'true'; # If your API uses credentials (cookies, auth headers)

        # Proxy to your actual backend application
        proxy_pass http://your_upstream_backend_service:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Environment-Specific Notes

CORS configuration can differ slightly depending on your deployment environment and infrastructure.

*   **Local Development:** During local development, developers often use origins like `http://localhost:3000`, `http://127.0.0.1:8080`, or other specific local IP addresses. It's common practice to temporarily allow `*` or hardcode `http://localhost:PORT` in your backend for ease of development. However, **never carry this `*` or localhost-specific configuration directly to production** unless your API is explicitly designed for public access without credentials. I typically configure my local dev server to accept both `localhost` origins and my machine's local IP, as sometimes I access it from a mobile device or a VM.

*   **Cloud Deployments (AWS, Azure, GCP):**
    *   **API Gateways:** Most cloud API Gateway services (like AWS API Gateway, Azure API Management, Google Cloud Endpoints) have robust, built-in CORS configuration options. This is often the easiest and most robust place to manage CORS. You can define allowed origins, methods, and headers directly in the gateway's settings, which then handles adding the necessary headers before forwarding requests to your backend services (e.g., Lambda functions, EC2 instances).
    *   **Serverless Functions (AWS Lambda, Azure Functions, GCP Cloud Functions):** If your API is built using serverless functions, you need to explicitly add the CORS headers to the function's response. For example, in AWS Lambda with API Gateway, this is usually managed via the API Gateway configuration. If responding directly, ensure your function code explicitly sets the headers in the response object.
    *   **Load Balancers/CDNs:** Be very careful with AWS Application Load Balancers (ALBs) or CDNs like CloudFront. An ALB generally passes headers through, but ensure it's not configured to strip anything. With CloudFront, you must explicitly whitelist the `Origin` header (and any `Access-Control-*` headers if your backend sends them and you want CloudFront to cache responses containing them) in your cache policy and response headers policy, otherwise, they might be stripped, or the CDN might serve a cached response without the required headers. This has caught me out more than once.

*   **Docker/Containerized Applications:** When deploying applications in Docker containers, the CORS configuration is typically done *inside* the application code or the web server configuration (e.g., Nginx, Apache) running within the container, just as you would for a non-containerized setup. Docker networking itself doesn't directly interfere with CORS headers, but ensure that any environment variables or configuration files governing CORS settings are correctly passed into your containers. If using a reverse proxy *outside* the container (e.g., Nginx on the host forwarding to a Docker container), configure CORS on the external proxy as well.

## Frequently Asked Questions

**Q: Why does my API work in Postman/Curl but not in my browser?**
**A:** Postman and `curl` are HTTP clients that do not enforce the Same-Origin Policy. They will happily send and receive cross-origin requests without checking for `Access-Control-Allow-Origin` headers. Browsers, however, strictly adhere to SOP for security reasons, and they will block cross-origin requests if the server's response doesn't contain the appropriate CORS headers.

**Q: Can I just use `*` for `Access-Control-Allow-Origin`?**
**A:** Using `Access-Control-Allow-Origin: *` allows *any* domain to access your API resources. This is generally acceptable for truly public APIs that do not handle sensitive user data or require authentication. However, if your API uses credentials (like cookies, HTTP authentication, or OAuth tokens in `Authorization` headers) that your browser sends, you **cannot** use `*`. In that case, you *must* specify the exact origin(s) that are allowed. For most internal or private APIs, specifying exact origins is the best security practice.

**Q: My `OPTIONS` request fails, what should I do?**
**A:** An `OPTIONS` request (a "preflight" request) is sent by the browser to check if the server understands the actual request methods and headers that will follow. If your `OPTIONS` request fails (e.g., 404 Not Found, 500 Internal Server Error, or a CORS error on the `OPTIONS` request itself), your server is not correctly configured to handle it. You need to ensure your server-side logic or web server configuration explicitly intercepts `OPTIONS` requests for your API routes, returns a 200 OK status, and includes all necessary `Access-Control-Allow-*` headers in that `OPTIONS` response.

**Q: How do I allow multiple specific origins?**
**A:** The `Access-Control-Allow-Origin` header can only contain a single origin or the `*` wildcard. If you need to allow multiple specific origins (e.g., `https://dev.example.com` and `https://prod.example.com`), your server logic must dynamically check the `Origin` header sent by the client in the request. If the client's `Origin` is in your list of allowed origins, your server should then set the `Access-Control-Allow-Origin` header in its response to that specific `Origin` value. Do not return multiple `Access-Control-Allow-Origin` headers; browsers will ignore them.

## Related Errors

- [http-401](/errors/http-401.html)
- [nginx-502](/errors/nginx-502.html)