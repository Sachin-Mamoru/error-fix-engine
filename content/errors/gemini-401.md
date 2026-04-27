# Unauthenticated: 401 API key invalid
> Encountering "Unauthenticated: 401 API key invalid" means your Gemini API key is either missing, incorrect, or not authorized; this guide explains how to fix it.

## What This Error Means

The `Unauthenticated: 401 API key invalid` error, specifically when interacting with the Gemini API, is a clear signal that the service cannot authenticate your request using the provided API key. An HTTP 401 status code signifies "Unauthorized," meaning the client's request has not been authenticated. In simpler terms, the server doesn't recognize you. When the message further specifies "API key invalid," it pinpoints the issue: the secret string you're presenting as your identity (your API key) is either malformed, incorrect, revoked, or doesn't match any valid keys associated with your project.

This isn't typically a permissions problem (which would often result in a 403 Forbidden error, meaning the server recognized you but you lack the necessary authorization for the requested action). Instead, it's a fundamental authentication failure. The Gemini service received *something* it believed to be an API key, but it failed its internal validation checks. From an SRE perspective, this error is often an early indicator of misconfiguration rather than a service outage, directing our attention straight to how the client application is handling its credentials.

## Why It Happens

This error occurs because the Gemini API endpoint you're calling needs a valid API key to confirm your identity and link your request to a specific Google Cloud Project. When the key presented with your request doesn't pass the server's validation checks, it responds with the 401 status and the specific "API key invalid" message.

In my experience, this usually stems from a disconnect between where the API key is expected, where it's stored, and what key is actually being used. It's a common stumbling block, especially when integrating a new service or deploying an application to a different environment. The server has a list of active, valid keys for your project, and if the one you provide doesn't match any on that list – or if it's structured incorrectly – authentication fails. It's like trying to unlock a door with the wrong key; the lock mechanism engages, but it doesn't open.

## Common Causes

Identifying the root cause of an `Unauthenticated: 401 API key invalid` error usually boils down to one of several common scenarios. I've debugged this issue countless times, and these are the usual suspects:

*   **Incorrect API Key:** This is by far the most frequent culprit.
    *   **Typos or Copy-Paste Errors:** A single missing character, an extra space, or incorrect casing in the API key string will render it invalid. These keys are long, alphanumeric strings, making manual entry or sloppy copy-pasting prone to error.
    *   **Using the Wrong Key:** You might have multiple API keys for different projects, environments (e.g., dev, staging, production), or even different Google Cloud services. Accidentally using a key from Project A for an application belonging to Project B, or using a Firebase API key for the Gemini API, will lead to this error.
*   **Missing API Key:** The application might not be supplying *any* API key at all.
    *   **Environment Variable Not Set:** Many client libraries and applications rely on environment variables (e.g., `GOOGLE_API_KEY`) to retrieve the key. If this variable is undefined, misspelled, or not loaded correctly in the execution environment, the API call goes out without the necessary credential.
    *   **Configuration File Issue:** If the key is loaded from a configuration file, that file might be missing, unreadable, or incorrectly formatted.
*   **API Key Not Enabled/Generated:** The key might not have been properly generated or enabled in the Google Cloud Console, or it might have been accidentally deleted or revoked.
*   **Key Restrictions Mismatch:** API keys can be restricted to specific IP addresses, HTTP referrers, or application bundles.
    *   **IP Address Restriction:** If your API key is restricted to a specific server's IP address and your request originates from a different IP (e.g., your local machine, a new deployment server), the key will be deemed invalid for that source.
    *   **HTTP Referrer Restriction:** For web applications, if the key is restricted to a specific domain (`example.com`) and your request comes from another domain or a non-browser client (like `curl`), it will fail.
*   **Client Library Configuration Errors:** While client libraries are designed to simplify API interaction, incorrect initialization can lead to the key not being passed correctly. For instance, configuring `genai.configure(api_key="your_key")` but then making a call that bypasses this configuration or uses an older, unconfigured client instance.
*   **Project Inactivity or Suspension:** In rare cases, if the Google Cloud project associated with the API key becomes inactive, suspended, or has billing issues that prevent service usage, API keys within that project might cease to function, resulting in an "invalid" status. While typically these lead to different error messages (e.g., 403 Forbidden with a specific message about project state), it's a possibility to keep in mind for complex scenarios.

## Step-by-Step Fix

Troubleshooting an `Unauthenticated: 401 API key invalid` error requires a systematic approach. From my SRE perspective, I always start by verifying the source of truth for the API key and then trace its path through the application.

1.  **Verify Your API Key in Google Cloud Console**
    *   **Navigate to Credentials:** Open the [Google Cloud Console](https://console.cloud.google.com/). Ensure you've selected the *correct project* from the dropdown menu at the top. Go to "APIs & Services" > "Credentials."
    *   **Locate the Key:** Find the API key you expect your application to be using. If you have multiple keys, confirm which one is intended for your Gemini integration.
    *   **Inspect the Key:** Click on the key name. Carefully examine the "API key string."
        *   **Action:** Copy the *entire* key string to your clipboard. This eliminates copy-paste errors from your original source. Do NOT regenerate the key yet, as this could break other services using it.

2.  **Inspect Your Code and Environment Variable Setup**
    *   **Check Key Usage:** How is your application or script accessing the API key?
        *   **Environment Variable:** This is the recommended and most common method. The Gemini client libraries typically look for `GOOGLE_API_KEY` (or sometimes `GEMINI_API_KEY`).
            *   **Action (Bash/Linux/macOS):** In your terminal, run `echo $GOOGLE_API_KEY`. If it's blank or shows the wrong key, set it correctly: `export GOOGLE_API_KEY="YOUR_ACTUAL_API_KEY"`. For persistence, add it to your `.bashrc`, `.zshrc`, or equivalent.
            *   **Action (Windows Command Prompt):** `echo %GOOGLE_API_KEY%` then `set GOOGLE_API_KEY="YOUR_ACTUAL_API_KEY"`.
            *   **Action (Windows PowerShell):** `Get-Item Env:GOOGLE_API_KEY` then `$env:GOOGLE_API_KEY="YOUR_ACTUAL_API_KEY"`.
        *   **Directly in Code:** If you've hardcoded the key (not recommended for production!), double-check that the string in your code exactly matches the key from the Google Cloud Console. *I've seen this in production when engineers cut corners; it inevitably leads to issues.*
        *   **Configuration File:** If loading from a `.env` file, YAML, or JSON, verify the file path, permissions, and the key's value within it.

3.  **Review API Key Restrictions**
    *   **Access Restrictions:** Back in the Google Cloud Console, under "APIs & Services" > "Credentials," click on your API key.
    *   **Check "Application restrictions":**
        *   If "IP addresses" is selected, ensure the IP address of the machine making the API call is listed. If testing locally, your local public IP needs to be added (you can find it by searching "what is my ip" on Google).
        *   If "HTTP referrers (websites)" is selected, ensure the referrer URL from which your application is making calls is correctly listed.
        *   **Action:** For debugging, you can temporarily set "Application restrictions" to "None" (ensure you do this *only* for a test key or in a controlled environment and re-apply restrictions immediately after testing for security).
    *   **Check "API restrictions":** Ensure the Gemini API (Generative Language API) is enabled for this key. If "Restrict key" is selected, verify that "Generative Language API" is explicitly allowed.
        *   **Action:** If not, add "Generative Language API" to the list of restricted APIs.

4.  **Test the API Key with a Simple `curl` Command**
    *   This is a critical step for isolating the issue from your application logic. A `curl` command directly against the Gemini API endpoint will quickly confirm if the key itself is the problem or if it's how your application is using it.
    *   **Action:** Replace `YOUR_API_KEY` with the actual key copied from the console. Replace `YOUR_MODEL_ID` (e.g., `gemini-pro`).
        ```bash
        API_KEY="YOUR_ACTUAL_API_KEY"
        MODEL_ID="gemini-pro"
        ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:generateContent?key=${API_KEY}"

        curl -X POST -H "Content-Type: application/json" \
             -d '{ "contents": [{"parts":[{"text":"Hello Gemini API"}]}] }' \
             "${ENDPOINT}"
        ```
    *   **Expected Outcome:** A successful response will be JSON containing the model's generated content. If you still get a `401 Unauthenticated: API key invalid` error, the problem is definitively with the key itself or its restrictions, not your application's logic.

5.  **Regenerate the API Key (Last Resort)**
    *   If you've exhausted all other options and confirmed the key from the console is indeed what you're using, and the `curl` test still fails, it's possible the key is somehow corrupted or marked invalid internally.
    *   **Action:** In the Google Cloud Console, under "APIs & Services" > "Credentials," click on your key and then click "Regenerate key." This will generate a completely new key string. **WARNING:** This will immediately invalidate the old key. Update *all* places where this key is used simultaneously. This is why I consider this a last resort; I've caused outages by regenerating a key without updating all consumers first.

## Code Examples

Here are concise, copy-paste-ready examples demonstrating how to correctly set and use your Gemini API key, focusing on robustness against the `401 API key invalid` error.

### Python Example

This Python example uses the `google-generativeai` library, which is the recommended way to interact with Gemini. It prioritizes loading the API key from an environment variable, which is a best practice.

```python
import google.generativeai as genai
import os

# --- Step 1: Ensure API Key is loaded correctly ---
# Best practice: Load GOOGLE_API_KEY from environment variables.
# This prevents hardcoding and allows for easy environment-specific configuration.
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY environment variable is not set.")
    print("Please set it, e.g., export GOOGLE_API_KEY='YOUR_ACTUAL_API_KEY'")
    exit(1) # Exit if the key is missing

# --- Step 2: Configure the Gemini SDK with the API key ---
try:
    genai.configure(api_key=api_key)
    print("Gemini API configured successfully.")
except ValueError as e:
    # This might catch issues with the key format before the actual API call
    print(f"Configuration error: {e}. Check your API key format.")
    exit(1)

# --- Step 3: Make an API call ---
try:
    model = genai.GenerativeModel('gemini-pro')
    # Example content generation
    prompt = "Tell me a short, inspiring fact about SRE."
    response = model.generate_content(prompt)

    print("\n--- Gemini Response ---")
    print(response.text)

except genai.types.BlockedPromptException as e:
    print(f"Prompt was blocked due to safety reasons: {e}")
except Exception as e:
    # Catch any other exceptions, including 401 Unauthenticated
    # The SDK usually wraps HTTP errors as specific exceptions or raises a generic one.
    print(f"\nAn API call error occurred: {e}")
    if "401 Unauthenticated" in str(e):
        print("This often indicates an 'API key invalid' issue.")
        print("Please double-check your GOOGLE_API_KEY in the Google Cloud Console.")
    exit(1)

print("\nAPI call completed.")
```

### Bash Example (using `curl`)

This `curl` command is excellent for quickly testing your API key directly, bypassing any application logic. It's my go-to for initial API key validation.

```bash
#!/bin/bash

# --- Instructions ---
# 1. Replace "YOUR_ACTUAL_API_KEY" with your Gemini API key from Google Cloud Console.
# 2. Ensure the MODEL_ID is correct (e.g., gemini-pro, gemini-pro-vision).
# 3. If you have region-specific endpoints, adjust the ENDPOINT URL accordingly.

API_KEY="YOUR_ACTUAL_API_KEY" # <<<<<<< UPDATE THIS WITH YOUR KEY <<<<<<<
MODEL_ID="gemini-pro"
ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:generateContent?key=${API_KEY}"

# --- Check if API_KEY is set ---
if [ "$API_KEY" == "YOUR_ACTUAL_API_KEY" ] || [ -z "$API_KEY" ]; then
  echo "Error: Please replace 'YOUR_ACTUAL_API_KEY' with your actual API key."
  exit 1
fi

echo "Attempting to call Gemini API with model: ${MODEL_ID}"
echo "Endpoint: ${ENDPOINT}"

# --- Make the cURL request ---
curl -X POST -H "Content-Type: application/json" \
     -d '{ "contents": [{"parts":[{"text":"Hello Gemini API, what is the capital of France?"}]}] }' \
     "${ENDPOINT}"

echo "" # Add a newline for cleaner output
echo "--- End cURL Response ---"

# Note: For security, avoid putting actual API keys directly in scripts that are committed to source control.
# Instead, load them from environment variables: API_KEY="${GOOGLE_API_KEY}"
```

A successful `curl` response will show JSON data, including the model's generated text. If you get a 401 error message in the `curl` output, it confirms the problem lies with the API key or its associated restrictions.

## Environment-Specific Notes

The context in which your application runs significantly impacts how you manage and deploy API keys. Misconfiguration in different environments is a common source of the `401 API key invalid` error.

### Local Development

*   **`.env` Files:** For local development, I always recommend using `.env` files with tools like `python-dotenv` (Python), `dotenv` (Node.js), or similar for other languages. You create a file named `.env` in your project root with `GOOGLE_API_KEY=YOUR_ACTUAL_API_KEY`. These tools load these variables into your environment when your application starts. **Crucially:** Add `.env` to your `.gitignore` to prevent committing sensitive keys to version control.
*   **Direct Export:** Alternatively, you can `export GOOGLE_API_KEY="YOUR_ACTUAL_API_KEY"` directly in your terminal session before running your application. This is temporary and only lasts for that session.
*   **IDE Configuration:** Integrated Development Environments (IDEs) often have settings to define environment variables for run/debug configurations. Ensure `GOOGLE_API_KEY` is correctly specified there.

### Cloud Environments (Google Cloud Run, Cloud Functions, GKE)

When deploying to cloud platforms, security and proper credential management become paramount.

*   **Google Cloud Run / Cloud Functions:** These serverless platforms allow you to set environment variables directly in their configuration. This is the preferred method for passing API keys. Navigate to your service/function settings and add `GOOGLE_API_KEY` with its value. **Do not hardcode keys in your source code or Dockerfiles.** While API keys work, for services running *within* Google Cloud, using Service Accounts with appropriate IAM roles is generally a more secure and robust authentication method (e.g., granting the `Generative Language User` role to the service account, then relying on default credentials), but this error specifically points to API key issues.
*   **Google Kubernetes Engine (GKE):** In a Kubernetes environment, API keys should be stored as Kubernetes Secrets.
    *   **Action:** Create a secret: `kubectl create secret generic google-api-key --from-literal=GOOGLE_API_KEY='YOUR_ACTUAL_API_KEY'`.
    *   Then, reference this secret in your pod's deployment manifest (`deployment.yaml`) to inject it as an environment variable:
        ```yaml
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: my-gemini-app
        spec:
          # ...
          template:
            spec:
              containers:
              - name: app-container
                image: your-app-image
                env:
                - name: GOOGLE_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: google-api-key
                      key: GOOGLE_API_KEY
        ```
    *   This ensures the key is not exposed in your image or repository.

### Docker Containers

*   **Build-time vs. Run-time:** Never bake API keys into your Docker image during the build process (`Dockerfile`). This creates insecure images that contain sensitive data.
*   **Run-time Injection:** Pass the API key as an environment variable when you run the container:
    `docker run -e GOOGLE_API_KEY="YOUR_ACTUAL_API_KEY" your-app-image`
*   **Docker Compose:** For multi-container applications, use Docker Compose's `.env` file integration or define environment variables directly in your `docker-compose.yml`:
    ```yaml
    version: '3.8'
    services:
      web:
        image: your-app-image
        environment:
          GOOGLE_API_KEY: ${GOOGLE_API_KEY} # Loaded from .env or host env
    ```
    Ensure `GOOGLE_API_KEY` is set in the host environment or a `.env` file that Docker Compose will pick up.

## Frequently Asked Questions

**Q: My API key works locally but not in production. Why?**
**A:** This is a very common scenario. It almost always points to differences in how the `GOOGLE_API_KEY` environment variable is set or accessed between your local machine and the production environment. Check production environment variables, deployment scripts, and any cloud platform configurations (e.g., Cloud Run environment variables, Kubernetes Secrets). Another possibility is that your API key has IP address or HTTP referrer restrictions that match your local environment but not your production servers.

**Q: Should I regenerate my API key if I keep getting this error?**
**A:** Regenerating the key should be a last resort. First, meticulously follow the "Step-by-Step Fix" guide: verify the key in the Google Cloud Console, inspect its journey through your application (environment variables, code), and test it with `curl`. Regenerating is useful if you suspect the key has been compromised, or if you've exhausted all other troubleshooting steps and believe the existing key might be internally corrupted or revoked without your knowledge. Remember, regenerating invalidates the old key immediately, so be prepared to update all consumers quickly.

**Q: Is "API key invalid" the same as "API key expired"?**
**A:** Not exactly. Most Google API keys do not have a hard expiration date in the way OAuth access tokens do. "API key invalid" generally means the key string provided does not match a valid, active key registered for your project, or it's improperly formatted. While a key could become 'invalid' if its associated project is suspended or if the key is revoked, it's not a timed expiration. If a key had a specific expiration mechanism and expired, it would likely present as an "invalid" key or a specific "expired" message depending on the service.

**Q: Can billing issues cause this "API key invalid" error?**
**A:** Generally, no. Billing issues typically manifest as a `403 Forbidden` error with a message explicitly stating "Billing Not Enabled," "Quota Exceeded," or "Project Shut Down." A `401 Unauthenticated: API key invalid` error specifically indicates a problem with the key's authenticity, not with usage limits or billing status. However, if a project is completely shut down due to severe billing problems, its API keys might effectively become invalid as the project no longer exists to validate them against.

**Q: What is the most secure way to handle API keys in a cloud environment?**
**A:** For most cloud environments (especially Google Cloud), using a Service Account with appropriate IAM roles (e.g., `Generative Language User`) and relying on the platform's default credential mechanisms is more secure than using raw API keys. The platform handles rotating and managing the service account's credentials. If API keys *must* be used, store them in secret management systems (like Kubernetes Secrets, AWS Secrets Manager, Google Secret Manager) and inject them as environment variables at runtime, never hardcoding them or baking them into container images.

## Related Errors
*(none)*