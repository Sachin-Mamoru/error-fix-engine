# Unauthenticated: 401 API key invalid
> Encountering "Unauthenticated: 401 API key invalid" means your Gemini API key is missing, invalid, or incorrectly configured; this guide explains how to fix it.

## What This Error Means

The `Unauthenticated: 401 API key invalid` error directly indicates an authentication failure when attempting to interact with the Gemini API. In the world of HTTP status codes, `401 Unauthorized` (often labelled `Unauthenticated` for clarity in API contexts) means that the request has not been applied because it lacks valid authentication credentials for the target resource.

Specifically for the Gemini platform, this error message means that the API service could not recognize or validate the API key you provided. It's a critical signal that the system doesn't know who you are, or thinks you are someone else entirely due to a malformed or incorrect key. It's distinct from a `403 Forbidden` error, which typically means the system knows who you are but you don't have the necessary permissions to access the requested resource. With a `401`, the very first step of identity verification has failed.

## Why It Happens

This error fundamentally occurs because the Gemini API endpoint you're trying to reach cannot establish your identity using the provided API key. The API key acts as a digital passport for your application. If that passport is missing, expired, revoked, or simply miswritten, the system will deny access.

From an SRE perspective, I've seen this in production when deployments go out without proper secrets configuration, or during local development when developers are moving between different projects or environments and forget to update their keys. It's a common stumbling block, but typically straightforward to resolve once you understand the underlying causes.

## Common Causes

In my experience, the `Unauthenticated: 401 API key invalid` error with Gemini API keys usually boils down to one of several recurring issues:

1.  **Missing API Key:** The most obvious cause. Your application code or environment simply isn't passing an API key at all, or it's passing an empty string. The Gemini service expects *some* key to be present.
2.  **Incorrect API Key:** This is often due to copy-paste errors, typing mistakes, or using an API key from a different project or environment. API keys are long, alphanumeric strings; even a single character mismatch will invalidate it.
3.  **Expired or Revoked Key:** API keys can have lifecycles. They might be set to expire after a certain period, or they could have been manually revoked by an administrator for security reasons. If a key is revoked, any subsequent request using it will fail.
4.  **Improper Key Formatting/Placement:** Gemini API keys are usually passed as a query parameter (`key=YOUR_API_KEY`) or in a specific HTTP header (e.g., `X-API-Key`). If the key is passed in the wrong place, or incorrectly formatted (e.g., extra spaces, wrong casing), the API won't recognize it.
5.  **Environment Variable Issues:** Often, API keys are stored in environment variables (e.g., `GEMINI_API_KEY`). If the variable isn't set correctly in the execution environment, or if your application isn't reading it properly, the key will effectively be missing or malformed when it reaches the API client.
6.  **Regional Restrictions:** While less common for the `401` specifically, sometimes API keys are tied to specific regions or projects. Attempting to use a key in an unauthorized region or for a resource it's not provisioned for *can* sometimes manifest as an authentication issue if the key itself isn't recognized in that context.

## Step-by-Step Fix

Troubleshooting this error requires a systematic approach. Here’s how I typically go about fixing it:

1.  **Verify Key Existence and Correctness:**
    *   **Source of Truth:** Go back to the Google Cloud Console (or wherever you generated your Gemini API key). Ensure the key you *think* you're using actually exists and is active.
    *   **Direct Comparison:** Carefully copy the key directly from the console and paste it into a temporary text file. Then, compare it character by character (or use a diff tool) with the key your application is actually using. Pay close attention to leading/trailing spaces, special characters, and capitalization.
    *   **Regenerate (If Unsure):** If you suspect the key might be compromised or if you're just unsure, regenerate a new API key in the Google Cloud Console. Update your application with this new key. Be aware that regenerating invalidates the old key immediately.

2.  **Check Environment Variable Configuration:**
    *   If you're using environment variables (which you should for security), verify they are set correctly in your shell or deployment environment.
    *   **Local Development:**
        ```bash
        echo $GEMINI_API_KEY
        ```
        This command should output your actual API key. If it's empty or incorrect, set it:
        ```bash
        export GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
        ```
        For persistent local development, consider using a `.env` file and a library like `python-dotenv` or `dot-env` for Node.js.
    *   **Deployment Environments:** For CI/CD pipelines, Docker containers, or cloud functions, ensure the environment variables are correctly passed and loaded.

3.  **Review API Client Initialization and Request Logic:**
    *   Examine the part of your code responsible for initializing the Gemini API client or making the raw HTTP request.
    *   Confirm the API key is being passed in the expected manner (e.g., as a `key` query parameter, or an `x-goog-api-key` header).
    *   Ensure no transformations (e.g., truncation, encoding errors) are happening to the key before it's sent.

    ```python
    import os
    import google.generativeai as genai

    # Incorrect: Key not loaded, or variable name wrong
    # api_key = os.getenv("WRONG_API_KEY_NAME")

    # Correct: Load from environment variable
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        # Handle error or exit
    else:
        genai.configure(api_key=api_key)
        # Proceed with API calls
    ```

4.  **Test with a Simple cURL Request:**
    *   A `curl` command is an excellent way to isolate if the issue is with your application code or the key itself.
    *   Replace `YOUR_ACTUAL_API_KEY` with the key you copied from the console.
    *   Replace `YOUR_GEMINI_ENDPOINT` with the specific endpoint you're trying to hit (e.g., `generativelanguage.googleapis.com/v1beta/models`).

    ```bash
    curl -X GET "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_ACTUAL_API_KEY" \
         -H "Content-Type: application/json"
    ```
    If this `curl` command still returns a `401`, you can be quite certain the issue lies with the API key itself (it's wrong, expired, revoked) or its provisioning, rather than your application's logic. If it works, the problem is in your application code or its environment.

5.  **Check Key Restrictions (If Applicable):**
    *   In the Google Cloud Console, check if your API key has any specific restrictions (e.g., IP address restrictions, HTTP referer restrictions). If your request is coming from an unauthorized IP or domain, the key might appear invalid even if it's correct. Temporarily removing these restrictions can help confirm if they are the cause. Re-apply them carefully after testing.

## Code Examples

Here are concise, copy-paste ready examples for commonly used languages.

### Python Example

This example demonstrates how to configure the `google-generativeai` client using an API key loaded from an environment variable.

```python
import os
import google.generativeai as genai

# Load API key from environment variable
# It's crucial that GEMINI_API_KEY is set in your shell or deployment environment
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

# Configure the genai library with your API key
genai.configure(api_key=api_key)

try:
    # Example API call: List available models
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"An error occurred: {e}")
    if "401 API key invalid" in str(e):
        print("Hint: Check your GEMINI_API_KEY environment variable.")

```

### cURL Example

This `curl` command directly targets a Gemini API endpoint to list models, passing the API key as a query parameter. This is invaluable for quick verification outside of your application code.

```bash
# Replace 'YOUR_ACTUAL_API_KEY' with your real Gemini API key.
# This example fetches a list of available models.
curl -X GET "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_ACTUAL_API_KEY" \
     -H "Content-Type: application/json"
```

## Environment-Specific Notes

The way you manage and provide API keys often varies significantly between development and production environments. Ignoring these differences is a classic cause of "works on my machine" bugs.

### Local Development

*   **`.env` files:** For local development, using a `.env` file (e.g., `GEMINI_API_KEY=your_dev_key`) and a library like `python-dotenv` or `dotenv` (Node.js) is common. Ensure these files are **never** committed to version control (`.gitignore` is your friend).
*   **Direct `export`:** Manually exporting the `GEMINI_API_KEY` environment variable in your terminal session before running your application. This is good for quick tests but not sustainable.
*   **IDE Configuration:** Some IDEs allow you to set environment variables for run configurations. Double-check these settings if your code runs fine via the terminal but not through your IDE's debugger.

### Cloud Environments (GCP, AWS, Azure, etc.)

*   **Secrets Managers:** In production, hardcoding or directly setting API keys as plain environment variables is a security risk. Utilize cloud-native secrets management services:
    *   **Google Cloud Secret Manager:** The recommended approach for GCP. Store your API key here and configure your applications (e.g., Cloud Functions, App Engine, GKE) to retrieve it securely at runtime.
    *   **AWS Secrets Manager / Parameter Store:** For AWS deployments.
    *   **Azure Key Vault:** For Azure deployments.
*   **IAM Roles/Service Accounts:** For services running within Google Cloud (e.g., a Cloud Function or a GKE pod), it's often more secure to use a service account with specific IAM roles that grant access to the Gemini API, rather than a raw API key. This avoids managing long-lived secrets altogether. If you are using a service account, ensure it has the `Generative Language API User` role (or equivalent).

### Docker/Containerized Environments

*   **Docker Secrets:** For sensitive information like API keys, Docker Secrets (for Docker Swarm) or Kubernetes Secrets (for Kubernetes) are the preferred methods. These encrypt and securely distribute secrets to your containers.
*   **Environment Variables (Less Secure):** While you can pass API keys as environment variables during `docker run` (e.g., `docker run -e GEMINI_API_KEY=...`), this embeds the key in the container's environment and can be inspected. It's generally less secure than Docker or Kubernetes Secrets for production.
*   **`.env` files for `docker compose`:** For local `docker compose` setups, you can use an `.env` file at the root of your project to define variables that `docker-compose.yml` can then inject into your services. Remember to `.gitignore` this file.

## Frequently Asked Questions

**Q: Can I use a service account key instead of an API key for Gemini?**
**A:** Yes, and for applications running within Google Cloud, it's generally the more secure and recommended approach. Instead of an API key, you'd assign an appropriate IAM role (like `Generative Language API User`) to the service account associated with your application (e.g., a Cloud Function, App Engine instance, GKE pod). The client libraries will automatically pick up the service account credentials.

**Q: My key works perfectly fine locally, but I get a 401 in my CI/CD pipeline or deployment environment. What's wrong?**
**A:** This is a classic symptom of an environment variable mismatch. The API key you have set locally isn't making it into your CI/CD runner or production deployment. Check how environment variables are configured in your CI/CD system (GitHub Actions secrets, GitLab CI/CD variables, Jenkins credentials, etc.) and ensure the correct variable name (`GEMINI_API_KEY` or similar) is being used. I've personally spent hours debugging this exact scenario until I realized a typo in a CI secret name.

**Q: How long do Gemini API keys last? Do they expire?**
**A:** Standard Google API keys (including those for Gemini) generally do not have an inherent expiration date by default, unlike some OAuth tokens. However, they can be manually revoked or regenerated at any time via the Google Cloud Console. Best practice is to rotate them periodically for security.

**Q: Is it safe to hardcode my API key directly into my source code?**
**A:** Absolutely not. Hardcoding API keys is a significant security vulnerability. If your code is ever committed to a public repository or falls into the wrong hands, your key can be compromised, leading to unauthorized usage and potential billing issues. Always use environment variables or, even better, a secrets management service (like Google Cloud Secret Manager) to keep your keys secure and out of your codebase.

**Q: Does the API key need specific permissions beyond just being valid?**
**A:** API keys themselves don't carry specific IAM permissions in the same way service accounts do. They grant access to the API services they are generated for. However, if your API key has "Application restrictions" or "API restrictions" configured in the Google Cloud Console, those restrictions can effectively limit what the key can do or from where it can be used. For example, restricting an API key to specific HTTP referrers means it will fail if used from an unauthorized domain.

## Related Errors