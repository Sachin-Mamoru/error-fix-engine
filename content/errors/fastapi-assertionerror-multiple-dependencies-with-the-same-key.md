# AssertionError: Multiple dependencies with the same key
> Encountering `AssertionError: Multiple dependencies with the same key` means FastAPI found ambiguity in your dependency declarations, typically when the same callable is registered multiple times under different wrapping types; this guide explains how to fix it.

## What This Error Means

This `AssertionError` is a strong signal from FastAPI's dependency injection system that it has detected an internal inconsistency. Specifically, it means that while FastAPI was building its internal map of dependencies for a particular path operation, it found two or more entries attempting to register the *same underlying callable function* (the "key" for the dependency) as a dependency, but in a way that creates an ambiguity.

FastAPI is designed to be smart about dependencies: if `Depends(get_db)` is used in multiple places within the same request's dependency tree, `get_db` will usually only be called once, and its result cached and reused. However, this specific `AssertionError` doesn't relate to the *result* of the dependency, but to its *registration*. It indicates that the dependency resolver encountered a situation where it expected a unique registration for a given callable, but found a duplicate.

## Why It Happens

FastAPI's power comes from its robust dependency injection system. When a request comes in, FastAPI analyzes the path operation function's signature and recursively builds a graph of all required dependencies. Each `Depends(...)` or `Security(...)` declaration tells FastAPI to inject a certain value, obtained by calling the function passed to `Depends` or `Security`. Internally, FastAPI uses the *callable function itself* (e.g., `get_current_user`) as a key to manage these dependencies.

The `AssertionError: Multiple dependencies with the same key` is triggered when FastAPI tries to add a dependency to its internal mapping, but finds that a dependency with the exact same callable key has already been added in a way that is deemed conflicting or ambiguous for the *current context*. This usually happens when the same underlying callable is specified through different dependency wrappers (like `Depends` and `Security`) within the *same path operation signature*, leading to the system attempting to register the same fundamental dependency twice but via different "paths" or interpretations, which it considers an assertion failure.

In my experience, this usually points to a misconfiguration in how dependencies are declared, rather than an actual bug in FastAPI itself. It's the system's way of saying, "Hey, I can't figure out how to uniquely map this dependency because you've told me to register it multiple times using the same underlying function, but perhaps in conflicting ways."

## Common Causes

While the error message is quite specific about "multiple dependencies with the same key," the scenarios leading to it can sometimes be subtle. Here are the most common causes I've encountered:

1.  **Mixing `Depends()` and `Security()` for the Same Callable:** This is, by far, the most frequent culprit. If you define a dependency like `def get_current_user(...)` and then try to use it in a path operation's signature both with `user: User = Depends(get_current_user)` and `secure_user: User = Security(get_current_user)`, FastAPI will throw this error. Both `Depends()` and `Security()` map to the same underlying callable (`get_current_user`), but `Security()` adds extra processing (like checking security scopes). When both are present for the same callable in the same function signature, FastAPI's internal mechanism attempts to register the dependency twice with what it considers the same key, but perhaps with conflicting expectations on how it should be processed.
2.  **Redundant Global or Router-Level Dependencies:** Less common, but possible, is a scenario where you define a dependency globally (e.g., with `app.dependency_overrides` or an `APIRoute` override) and then attempt to define it again, perhaps with a slight variation or using a different wrapper, directly in a path operation. This can lead to the same callable being added to the dependency map twice for the same route.
3.  **Complex Custom Routing or Dependency Registration:** If you're building highly custom routing mechanisms, perhaps by directly manipulating `fastapi.routing.APIRoute` objects or employing meta-programming to dynamically generate path operations and their dependencies, it's possible to accidentally register the same callable as a dependency multiple times for a single endpoint. This requires a deeper understanding of FastAPI's internal routing and dependency graph construction.

## Step-by-Step Fix

Rectifying this error usually involves a careful review of your path operation's signature and any related dependency declarations.

1.  **Locate the Problematic Path Operation:**
    The traceback for the `AssertionError` will typically point to the specific path operation (e.g., `@app.get("/my-endpoint")`) where the dependency conflict was detected during startup. Isolate this endpoint.

2.  **Examine the Path Operation Signature for Duplicates:**
    Carefully inspect every parameter in the function signature of your path operation. Look for instances where the same callable function is being passed to `Depends()` or `Security()`.

    ```python
    # Example problematic signature
    @app.get("/items/")
    async def read_items(
        user_info: dict = Depends(get_current_active_user),
        # This line is the problem if get_current_active_user is the same callable
        security_user: dict = Security(get_current_active_user, scopes=["admin"])
    ):
        # ...
        pass
    ```

3.  **Identify and Refactor Conflicting `Depends()` vs. `Security()`:**
    If you've found a callable (like `get_current_active_user` in the example above) being used with both `Depends()` and `Security()` in the *same signature*, this is almost certainly the cause.

    *   **Choose one:** Decide whether you need the `Security` features (like `scopes`) or if a plain `Depends` suffices.
        *   If `Security` is required, remove the `Depends` declaration for that same callable.
        *   If only the basic dependency injection is needed, remove the `Security` declaration and stick with `Depends`.
    *   **Encapsulate if needed:** If you truly need different *aspects* or *results* derived from the same base callable, consider wrapping one of them in another dependency function.

    **Example Refactoring (choosing `Security`):**
    ```python
    # Before (causing error):
    # user_info: dict = Depends(get_current_active_user),
    # security_user: dict = Security(get_current_active_user, scopes=["admin"])

    # After (fixed):
    @app.get("/items/")
    async def read_items(
        user_info: dict = Security(get_current_active_user, scopes=["admin"]) # Use only Security
    ):
        # The 'user_info' variable now holds the result from get_current_active_user,
        # and security checks are applied.
        pass
    ```
    If you needed `user_info` for one purpose and `security_user` for another, both deriving from `get_current_active_user`, simply using `user_info: dict = Security(get_current_active_user, scopes=["admin"])` and then assigning `security_user = user_info` inside your path operation or in a subsequent dependency would be the correct approach. FastAPI calls the underlying callable (`get_current_active_user`) only once and reuses the result.

4.  **Review Global/Router Dependency Overrides (if applicable):**
    If the error persists or your code doesn't have the `Depends` vs `Security` clash, check any places where you define global `app.dependency_overrides` or router-specific dependency overrides. Ensure that a specific callable isn't being targeted for override multiple times in a conflicting manner. This is more common in advanced testing setups or plug-in architectures.

    ```python
    # Example of checking overrides (especially in test files)
    # Ensure get_db is not overridden multiple times or in conflicting ways.
    app.dependency_overrides[get_db] = override_get_db_1
    # If later, in the same scope or test context, you have:
    # app.dependency_overrides[get_db] = override_get_db_2
    # This might cause issues if not managed correctly.
    ```

5.  **Restart your application:**
    After making changes, always perform a clean restart of your FastAPI application. Since this error occurs during startup (when the dependency graph is being built), a simple code reload might not always clear the internal state if you're using a development server.

## Code Examples

Here are concise, copy-paste ready examples demonstrating the error and its fix.

### Problematic Code (Causing `AssertionError`)

This example demonstrates the classic `Depends()` vs `Security()` conflict using the same underlying callable.

```python
from fastapi import FastAPI, Depends, Security, HTTPException, status
from typing import Annotated

app = FastAPI()

# A simple mock user database
fake_users_db = {
    "john.doe": {"username": "john.doe", "full_name": "John Doe", "scopes": ["user"]},
    "jane.smith": {"username": "jane.smith", "full_name": "Jane Smith", "scopes": ["user", "admin"]},
}

# A dependency to simulate getting the current user based on an API key
async def get_current_user(api_key: Annotated[str, Depends(lambda: "some_api_key")]):
    """Mocks fetching a user from a database."""
    if api_key != "valid-api-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return fake_users_db["john.doe"]

# A dependency to check active status and scopes (reusing get_current_user)
async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Mocks checking if user is active and has basic user scopes."""
    if "user" not in current_user.get("scopes", []):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.get("/users/me/")
async def read_users_me(
    # First usage of get_current_active_user as a standard dependency
    user_info: Annotated[dict, Depends(get_current_active_user)],
    # Second usage of the *same callable* but wrapped with Security
    # This will cause: AssertionError: Multiple dependencies with the same key
    admin_user: Annotated[dict, Security(get_current_active_user, scopes=["admin"])]
):
    return {"user_info": user_info, "admin_user": admin_user}

# To run this:
# 1. Save as `main.py`
# 2. Run `uvicorn main:app --reload`
# 3. You will see the AssertionError on startup.
```

### Corrected Code (Resolves `AssertionError`)

Here, we've removed the redundant `Depends()` and used only `Security()` for the `get_current_active_user` dependency, ensuring it's registered only once.

```python
from fastapi import FastAPI, Depends, Security, HTTPException, status
from typing import Annotated

app = FastAPI()

fake_users_db = {
    "john.doe": {"username": "john.doe", "full_name": "John Doe", "scopes": ["user"]},
    "jane.smith": {"username": "jane.smith", "full_name": "Jane Smith", "scopes": ["user", "admin"]},
}

async def get_current_user(api_key: Annotated[str, Depends(lambda: "valid-api-key")]):
    if api_key != "valid-api-key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return fake_users_db["john.doe"]

async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    if "user" not in current_user.get("scopes", []):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.get("/users/me/")
async def read_users_me(
    # CORRECTED: Use only Security to define the dependency.
    # The result of get_current_active_user will be passed to 'user_info'.
    # If 'admin_user' was truly a separate concept, it would need a different dependency function.
    user_info: Annotated[dict, Security(get_current_active_user, scopes=["admin"])]
):
    # Now, 'user_info' contains the result, and 'admin' scope has been checked.
    # If you need to refer to it as 'admin_user' as well, you can just re-assign:
    admin_user = user_info
    return {"user_info": user_info, "admin_user": admin_user}

# To run this:
# 1. Save as `main_fixed.py`
# 2. Run `uvicorn main_fixed:app --reload`
# 3. The application will start successfully.
# 4. Access http://127.0.0.1:8000/users/me/
```

In the corrected example, `Security(get_current_active_user, scopes=["admin"])` ensures that `get_current_active_user` is registered as a dependency for `user_info` and that the `admin` scope is checked. FastAPI will call `get_current_active_user` once, and its result will be available through the `user_info` parameter.

## Environment-Specific Notes

This `AssertionError` is typically a code-level configuration issue, meaning its manifestation is largely consistent across different deployment environments. However, certain aspects can make it easier or harder to diagnose.

*   **Local Development:**
    During local development with `uvicorn --reload`, the application restarts on file changes. If you introduce this error, it will immediately manifest as a crash on startup. This is the ideal environment to debug it, as the feedback loop is fast. The traceback will be printed directly to your console.

*   **Docker Containers:**
    When running your FastAPI application inside a Docker container, the error will cause the container to fail to start or crash shortly after startup. The `AssertionError` will be visible in the container logs.

    ```bash
    # Example of checking logs for a Docker container
    docker logs <your-container-name-or-id>
    ```

    Ensuring your `CMD` or `ENTRYPOINT` in your `Dockerfile` uses `uvicorn` in a production-ready way (e.g., `uvicorn main:app --host 0.0.0.0 --port 80`) means the application will attempt to fully initialize, leading to the error if present. You might need to examine the logs carefully, especially if the container exits immediately.

*   **Cloud Deployments (Serverless, VMs, Kubernetes):**
    In cloud environments like AWS Lambda (via Mangum), Google Cloud Run, Azure Container Apps, or Kubernetes, the error will prevent your application instance from becoming healthy or starting up correctly.
    *   **Serverless:** For serverless functions, the initial invocation might fail, or the function instance itself might crash during initialization. You'll need to check the logs of your serverless platform (e.g., CloudWatch for AWS Lambda, Cloud Logging for Google Cloud Functions/Run) for the full traceback.
    *   **VMs/Kubernetes:** On virtual machines or Kubernetes, the application process will fail to start. In Kubernetes, this would manifest as a failing pod with crash loop back-offs (`CrashLoopBackOff` status). The logs of the failing pod or VM instance will contain the `AssertionError`. Monitoring and logging tools are crucial here.

The key takeaway is that the error is a startup-time issue. If your CI/CD pipeline includes a health check or a simple `uvicorn` startup command, this error should be caught before reaching production traffic.

## Frequently Asked Questions

**Q: Why does FastAPI throw an `AssertionError` instead of handling it gracefully?**
**A:** FastAPI's dependency injection system relies on a consistent internal state. An `AssertionError` here indicates a fundamental conflict in how dependencies are registered, which could lead to unpredictable behavior if not caught immediately. By failing loudly at startup, FastAPI forces the developer to resolve the ambiguity, preventing harder-to-debug runtime issues. It's a design choice for robustness and correctness.

**Q: Can I have two different parameters using `Depends(some_function)` in the same path operation?**
**A:** Yes, you can. For example, `param1: str = Depends(get_str), param2: str = Depends(get_str)` would typically work without this `AssertionError`. FastAPI would call `get_str` only once and use the cached result for both `param1` and `param2`. The `AssertionError` specifically targets conflicts where the *same callable* is registered as a dependency via *different wrapping types* (like `Depends` and `Security`), leading to ambiguity in how it should be processed.

**Q: What if I need `Security` features for one parameter but plain `Depends` for another, both using the same underlying logic?**
**A:** If the *underlying callable* is the same, you should typically use `Security` if you need its features (like `scopes`). The result will be available. If you need the *same data* but without the security checks for a different parameter, you can just assign the result: `user: User = Security(get_user, scopes=["read"]); user_data = user`. If the "underlying logic" truly needs to be processed differently, then it implies you should have two *distinct* callable functions for your dependencies.

**Q: Does this error occur with global dependencies or router-level dependencies?**
**A:** While less common than the `Depends` vs `Security` clash, it can occur if you're dynamically registering dependencies or using `app.dependency_overrides` in a conflicting way. For instance, attempting to override the same callable twice within the same application startup context could potentially trigger this. Always double-check your override definitions if the issue isn't in a path operation's signature directly.

## Related Errors
*(none)*