# django.middleware.csrf.CsrfViewMiddleware: CSRF token missing or incorrect
> Encountering django.middleware.csrf.CsrfViewMiddleware: CSRF token missing or incorrect means the CSRF token was absent or invalid in a request; this guide explains how to identify and resolve this critical security error in your Django application.

## What This Error Means

This error message, `django.middleware.csrf.CsrfViewMiddleware: CSRF token missing or incorrect`, indicates a failure in Django's built-in Cross-Site Request Forgery (CSRF) protection mechanism. CSRF is a type of malicious exploit where unauthorized commands are transmitted from a user that the web application trusts. Django's `CsrfViewMiddleware` is responsible for verifying that POST requests, and other potentially state-changing requests (PUT, DELETE), originate from your own forms or scripts within your application, not from an external, malicious source.

When you see this error, it means one of two things happened:
1.  **The CSRF token was completely missing** from the incoming request. Django expected to find it, but it wasn't there.
2.  **The CSRF token was present, but it did not match** the token that Django had generated and expected for the current user's session.

In essence, Django could not confirm the request's authenticity, and for security reasons, it rejected the request. While this is a security feature, it often points to a misconfiguration or oversight in how your forms or AJAX requests are handled.

## Why It Happens

At a high level, the error occurs because there's a mismatch between what Django's CSRF middleware expects and what it receives. Django generates a unique, session-bound CSRF token and embeds it into your rendered HTML forms or sets it as a cookie. When a form is submitted or an AJAX request is made, Django expects this token to be sent back with the request.

If the token is either not sent or the sent token doesn't match the one stored on the server (usually in the user's session), the `CsrfViewMiddleware` raises this error. This can happen for various reasons, from simple template oversights to complex caching issues or misconfigurations in proxy setups.

## Common Causes

In my experience as a platform engineer, this error typically stems from a few recurring scenarios:

1.  **Missing `{% csrf_token %}` in Django Templates:** This is by far the most common cause. Every `<form>` tag in a Django template that uses the `POST` method (or `PUT`/`DELETE` via method override) must include the `{% csrf_token % %}` template tag inside it. If omitted, the token won't be rendered into the form, and thus won't be sent with the submission.
2.  **AJAX Requests Not Sending the CSRF Token:** When making asynchronous JavaScript requests (e.g., using `fetch` or jQuery's `$.ajax`) to Django views, the CSRF token isn't automatically included. You must manually retrieve it (either from a cookie or a hidden input field) and send it as an `X-CSRFToken` header with your request. I've debugged many a frontend application where this crucial step was forgotten.
3.  **Caching Issues:** Aggressive caching, whether at the browser level, an intermediate proxy (like Nginx), a CDN, or even Django's own caching, can sometimes serve stale pages. If a cached page contains an outdated CSRF token (or no token at all, if the page was cached before the session started), subsequent form submissions will fail.
4.  **Session-Related Problems:** The CSRF token is typically tied to the user's session. If the session isn't properly initialized, saved, or is lost (e.g., due to `SESSION_COOKIE_DOMAIN` issues, `SESSION_COOKIE_SECURE` mismatches in production, or sessions not being persisted across server restarts in multi-instance deployments without a shared session backend), Django won't be able to retrieve the expected token for validation.
5.  **Cross-Origin Request Issues (`CSRF_TRUSTED_ORIGINS`, `CSRF_COOKIE_DOMAIN`):** If your frontend is served from a different domain or subdomain than your Django backend (e.g., `app.example.com` and `api.example.com`), you might need to configure `CSRF_TRUSTED_ORIGINS` or `CSRF_COOKIE_DOMAIN` in your Django settings to allow the CSRF cookie to be sent and validated across origins.
6.  **Redirects After a POST Request:** Although less common directly, I've seen scenarios where a POST request triggers a redirect that somehow interferes with session or cookie handling, leading to subsequent CSRF issues if the user attempts another POST immediately.
7.  **Middleware Order:** While rare for standard Django setups, if you've heavily customized your `MIDDLEWARE` list, ensure `django.middleware.csrf.CsrfViewMiddleware` is correctly positioned. It should generally come after `SessionMiddleware` and `AuthenticationMiddleware`.
8.  **Third-party Integrations or Embeds:** If you're embedding Django forms or components within another application or platform, the context might strip or prevent the correct handling of CSRF tokens.

## Step-by-Step Fix

Troubleshooting this error systematically is key. Here's how I typically approach it:

1.  **Inspect the Browser's Network Tab:**
    *   Open your browser's developer tools (usually F12).
    *   Go to the "Network" tab.
    *   Clear the network log.
    *   Perform the action that triggers the CSRF error (e.g., submit the form).
    *   Look for the failed request (often a `POST` request with a 403 Forbidden status).
    *   Examine the "Headers" tab for that request.
        *   **For traditional forms:** Check the "Form Data" or "Request Payload" section. Is there an input field named `csrfmiddlewaretoken` with a value?
        *   **For AJAX requests:** Look at the "Request Headers". Is there an `X-CSRFToken` header, and does it have a value?
    *   Also, check "Response Headers" for `Set-Cookie` headers, specifically for the `csrftoken` and `sessionid` cookies.

2.  **Verify `{% csrf_token %}` in Django Templates:**
    *   If the request was from a traditional form and the `csrfmiddlewaretoken` was missing from the form data, open the Django template rendering that form.
    *   Ensure that `{% csrf_token %}` is placed directly inside the `<form>` tag:
        ```html
        <form method="post">
            {% csrf_token %}
            <!-- your form fields -->
            <button type="submit">Submit</button>
        </form>
        ```
    *   If you're rendering forms via `{{ form.as_p }}`, `{{ form.as_table }}`, or `{{ form.as_ul }}`, the token is usually included automatically, but it's worth double-checking the rendered HTML source in the browser.

3.  **Correctly Handle CSRF in AJAX Requests:**
    *   If you're making AJAX requests and the `X-CSRFToken` header was missing or empty, you need to manually include it.
    *   The most robust way is to fetch the token from the `csrftoken` cookie or a hidden input field. See the "Code Examples" section below for common patterns.
    *   Ensure your JavaScript code retrieves the correct token and sets the `X-CSRFToken` header for *non-GET* requests.

4.  **Check Django Settings:**
    *   **`MIDDLEWARE`:** Confirm that `django.middleware.csrf.CsrfViewMiddleware` is in your `MIDDLEWARE` setting and positioned correctly (e.g., after `SessionMiddleware`).
    *   **`INSTALLED_APPS`:** Ensure `django.contrib.sessions` is present, as CSRF relies on sessions.
    *   **`CSRF_COOKIE_DOMAIN`:** If your frontend and backend are on different subdomains, ensure this setting is correctly configured (e.g., `CSRF_COOKIE_DOMAIN = ".example.com"`). If misconfigured, the browser might not send the cookie.
    *   **`CSRF_TRUSTED_ORIGINS`:** For cross-origin POST requests, list your trusted origins here (e.g., `CSRF_TRUSTED_ORIGINS = ['https://*.myfrontend.com']`).
    *   **`SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE`:** In production, if using HTTPS, these should be `True`. If they are `True` but you're testing on HTTP, the cookies won't be sent. This has caught me out more than once during local testing on dev environments.

5.  **Clear Caches:**
    *   **Browser Cache:** Hard refresh (Ctrl+F5 or Cmd+Shift+R) or clear browser data.
    *   **Server/CDN Cache:** If you're using Nginx, Varnish, or a CDN, ensure any caching layers are properly configured *not* to cache dynamic pages containing CSRF tokens, or to vary on the `Cookie` header. A stale cached page could serve an old token.

6.  **Verify Session Backend:**
    *   Ensure your session backend (e.g., `django.contrib.sessions.backends.db`) is correctly configured and working. If sessions aren't being written or read, the CSRF token cannot be validated. Check your database for `django_session` entries.

7.  **Isolate with `curl` or Postman:**
    *   To rule out browser or JavaScript issues, try sending a `POST` request manually using `curl` or a tool like Postman. You'll need to first perform a `GET` request to your page to obtain the `csrftoken` cookie, then include that cookie and an `X-CSRFToken` header in your `POST` request. This helps confirm if the issue is server-side or client-side.

## Code Examples

Here are some concise, copy-paste ready code examples for common CSRF scenarios:

### 1. Traditional Django Form

Ensure the `{% csrf_token %}` template tag is always present inside your `<form>` element:

```html
<!-- my_template.html -->
<form method="post" action="{% url 'my_view_name' %}">
    {% csrf_token %}
    <label for="name">Name:</label>
    <input type="text" id="name" name="name" required>
    <br>
    <label for="email">Email:</label>
    <input type="email" id="email" name="email" required>
    <br>
    <button type="submit">Submit Data</button>
</form>
```

### 2. AJAX POST Request with jQuery

This approach includes a utility function to get the CSRF token from cookies and sets up jQuery's `ajaxSetup` to include the `X-CSRFToken` header automatically for non-GET requests.

```javascript
// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

// Set up jQuery AJAX requests to include the CSRF token
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// Example AJAX POST request
$('#submit-button').on('click', function() {
    $.ajax({
        url: '/api/submit_data/',
        type: 'POST',
        data: {
            item_name: $('#item-name').val(),
            item_value: $('#item-value').val()
        },
        success: function(response) {
            console.log('Success:', response);
            // Handle success, e.g., update UI
        },
        error: function(xhr, status, error) {
            console.error('Error:', error);
            // Handle error, e.g., show error message
        }
    });
});
```

### 3. AJAX POST Request with Fetch API

Similar to jQuery, you need to manually add the `X-CSRFToken` header.

```javascript
// Re-use the getCookie function from the jQuery example, or get token from a meta tag
const csrftoken = getCookie('csrftoken'); // Or: document.querySelector('meta[name="csrf-token"]').getAttribute('content');

document.getElementById('fetch-submit-button').addEventListener('click', async () => {
    const data = {
        item_name: document.getElementById('fetch-item-name').value,
        item_value: document.getElementById('fetch-item-value').value
    };

    try {
        const response = await fetch('/api/submit_data/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken // Crucial for non-GET requests
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Success:', result);
    } catch (error) {
        console.error('Error:', error);
    }
});
```

## Environment-Specific Notes

The "CSRF token missing or incorrect" error can manifest differently or require specific considerations based on your deployment environment.

*   **Local Development:**
    *   Often, developers don't use HTTPS locally. Ensure `CSRF_COOKIE_SECURE = False` and `SESSION_COOKIE_SECURE = False` in your `settings.py` for local `DEBUG = True` environments, otherwise, the browser won't send the cookies over insecure HTTP. I've wasted hours debugging this simple setting change when deploying to production and then testing locally again.
    *   Browser extensions (e.g., ad blockers, privacy tools) can sometimes interfere with cookies or form submissions. Test in an incognito window or with extensions disabled.

*   **Docker/Containerized Environments:**
    *   **Network Configuration:** Ensure your Docker containers can communicate correctly, especially if your Django application and a frontend (e.g., a React app in another container) are separate. Incorrect network settings can prevent cookie transmission.
    *   **Proxy Setup:** If using Nginx or Caddy as a reverse proxy in front of your Django container, verify that headers related to cookies and original host are correctly passed through (e.g., `proxy_set_header Host $host;`, `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`). This impacts how Django sees the request and sets cookies.
    *   **Shared Session Storage:** If running multiple Django instances (e.g., via Docker Compose with scaling, or Kubernetes deployments), ensure you're using a shared session backend (like Redis or a database) and not the default file-based session. Otherwise, requests could hit different containers with different session states, leading to token mismatches.

*   **Cloud Deployments (AWS, GCP, Azure, etc.):**
    *   **Load Balancers & CDNs:** Load balancers (e.g., AWS ALB/ELB, Azure Load Balancer) and Content Delivery Networks (CDNs like CloudFront, Cloudflare) are common culprits.
        *   **Sticky Sessions:** If your session backend isn't shared (e.g., using Django's default database sessions), enable sticky sessions (session affinity) on your load balancer. This ensures a user's requests always go to the same application instance, maintaining session state and CSRF tokens.
        *   **Caching:** Be extremely cautious about caching dynamic pages containing forms. Configure your CDN or load balancer to *not* cache POST requests or pages with forms, or at minimum, to vary caching on the `Cookie` header.
        *   **SSL/TLS Termination:** If your load balancer handles SSL termination, ensure it forwards the correct `X-Forwarded-Proto` header so Django knows the original request was HTTPS. This affects `CSRF_COOKIE_SECURE` and `SESSION_COOKIE_SECURE`.
    *   **Web Application Firewalls (WAFs):** WAFs (like AWS WAF, Cloudflare WAF) can sometimes inspect or even block requests if they don't conform to certain patterns or if they misinterpret valid CSRF tokens as malicious payloads. Check WAF logs if all else fails.
    *   **`CSRF_COOKIE_DOMAIN` and `CSRF_TRUSTED_ORIGINS`:** These settings become paramount in cloud environments, especially with distinct domain names for frontend and backend services. Incorrect configuration here is a frequent cause of CSRF failures when deploying to the cloud.

## Frequently Asked Questions

**Q: Can I just disable CSRF protection altogether?**
**A:** While it's technically possible using `@csrf_exempt` or by removing the middleware, it's **strongly discouraged** for any production application, especially for views that handle state-changing operations. Disabling CSRF protection leaves your application vulnerable to serious security exploits.

**Q: I need an API endpoint that can be called by external services without CSRF protection. What's the best practice?**
**A:** For specific API endpoints that are explicitly designed for machine-to-machine communication or external public consumption, and where other authentication methods (like API keys or OAuth tokens) are in place, you can use the `@csrf_exempt` decorator on the view function. Exercise extreme caution and ensure you understand the security implications. It's not a substitute for proper API authentication.

**Q: Why is my `csrftoken` cookie missing from the browser, even after a GET request to a Django page?**
**A:** This usually indicates a problem with session management. Check if `django.contrib.sessions` is in your `INSTALLED_APPS`, and that your session backend is properly configured and accessible (e.g., database sessions are writing to the database). Also, review `SESSION_COOKIE_DOMAIN`, `SESSION_COOKIE_PATH`, and `SESSION_COOKIE_SECURE` settings, especially in production environments or if using HTTPS.

**Q: Does caching interfere with CSRF tokens?**
**A:** Yes, absolutely. If a page containing a CSRF token is cached by a browser, proxy, or CDN, and then that token becomes stale (e.g., the user's session expires or the server restarts), subsequent form submissions using the cached token will fail. Be very careful about caching pages that generate forms or dynamically insert CSRF tokens.

## Related Errors