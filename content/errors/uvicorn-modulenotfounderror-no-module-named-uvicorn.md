# ModuleNotFoundError: No module named 'uvicorn'
> Encountering "ModuleNotFoundError: No module named 'uvicorn'" means the uvicorn package is not installed in your current Python environment; this guide explains how to fix it.

## What This Error Means

This error, `ModuleNotFoundError: No module named 'uvicorn'`, is a clear indicator that the Python interpreter cannot locate the `uvicorn` package. When you try to run a command like `uvicorn main:app --reload`, or if your application code attempts to import `uvicorn` directly, Python searches its configured paths for the module. If it's not found in any of those locations, it raises this specific `ModuleNotFoundError`. In the context of running FastAPI or Starlette applications, `uvicorn` is the ASGI server that takes your application code and makes it accessible via HTTP. Without it, your application simply won't start.

## Why It Happens

At its core, this error occurs because the `uvicorn` package has not been installed, or it has been installed in a Python environment that is not currently active or accessible to your shell. Python environments are designed to isolate dependencies, preventing conflicts between different projects. When you encounter this `ModuleNotFoundError`, it’s usually a mismatch between where you *think* `uvicorn` is installed and where Python is actually looking for it. It's a fundamental environmental issue rather than a bug in your application code itself.

## Common Causes

In my experience, encountering `ModuleNotFoundError: No module named 'uvicorn'` during CLI startup typically boils down to one of the following scenarios:

1.  **`uvicorn` is not installed at all:** This is the most straightforward cause. You've simply forgotten to install the package in your current Python environment. This happens often when setting up a new project or cloning a repository for the first time.
2.  **Incorrect Python environment is active:** You might have multiple Python installations or virtual environments on your system. `uvicorn` could be installed in one environment (e.g., a virtual environment for Project A) but you're trying to run your application using another environment (e.g., the system-wide Python or a different virtual environment for Project B). The active environment determines which packages are available.
3.  **Virtual environment not activated:** If you're using a virtual environment (which is highly recommended), you might have installed `uvicorn` into it, but forgotten to activate the environment before attempting to run your application. Without activation, your shell defaults to the system Python, which likely doesn't have `uvicorn` installed. I've seen this in production-like scenarios where a CI/CD pipeline step might miss the activation command.
4.  **`uvicorn` installed in a different Python version:** Sometimes, you might have Python 3.8 and Python 3.10 installed. If you run `pip install uvicorn` with Python 3.8's `pip`, but then try to execute your application with Python 3.10, the module won't be found.
5.  **Path issues (less common for `uvicorn` CLI startup):** While less frequent for a direct CLI call to `uvicorn`, if you were importing `uvicorn` from within a script, and your `PYTHONPATH` was misconfigured or pointing to an unexpected location, it could lead to similar issues. For CLI usage, it primarily points back to environment activation.

## Step-by-Step Fix

Here's how to systematically troubleshoot and resolve the `ModuleNotFoundError: No module named 'uvicorn'`:

1.  **Verify Your Current Python Environment:**
    First, check which Python interpreter your shell is currently using. This is crucial for understanding where `pip` will install packages and where Python will look for them.

    ```bash
    which python
    python --version
    which pip
    pip --version
    ```
    If `which python` points to `/usr/bin/python` or another system-wide path, and you intended to use a virtual environment, you need to activate it first.

2.  **Activate Your Virtual Environment (If Applicable):**
    If you have a virtual environment for your project, activate it. This ensures that any subsequent `pip` commands install packages into this isolated environment and that your application runs using its Python interpreter.

    ```bash
    # For virtualenv/venv
    source .venv/bin/activate
    # or if on Windows Command Prompt
    .venv\Scripts\activate.bat
    # or if on Windows PowerShell
    .venv\Scripts\Activate.ps1

    # For Conda environments
    conda activate your_env_name
    ```
    After activation, re-run `which python` and `pip --version`. You should see paths pointing inside your virtual environment (e.g., `~/my-project/.venv/bin/python`).

3.  **Install `uvicorn` (or Reinstall):**
    Once you are certain you are in the correct Python environment, install `uvicorn`. If you're unsure if it's already installed, `pip install` will either install it or tell you it's already satisfied. For FastAPI applications, it's often good practice to install `uvicorn` with the `standard` or `full` extras to get additional features like `python-multipart` for forms.

    ```bash
    pip install uvicorn
    # For common FastAPI setups, consider:
    # pip install "uvicorn[standard]"
    # or
    # pip install "uvicorn[full]"
    ```
    If you have a `requirements.txt` file, use that:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Verify `uvicorn` Installation:**
    You can check if `uvicorn` is now available in your active environment by listing installed packages or trying to import it.

    ```bash
    pip freeze | grep uvicorn
    # Expected output: uvicorn==x.y.z
    ```
    You can also try a quick Python import:

    ```bash
    python -c "import uvicorn; print('Uvicorn installed successfully!')"
    ```
    If this runs without an `ImportError`, you're good to go.

5.  **Run Your Application:**
    Now, attempt to start your application again using the `uvicorn` command.

    ```bash
    uvicorn main:app --reload
    ```
    This sequence typically resolves the `ModuleNotFoundError` for `uvicorn`.

## Code Examples

Here's a minimal example of a FastAPI application and how you'd run it, assuming `uvicorn` is installed.

**1. `main.py` (Your FastAPI application):**

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}
```

**2. `requirements.txt` (Recommended project dependencies):**

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
```

*(Note: Use the actual versions you need or omit for latest compatible, but specifying is generally better for reproducibility.)*

**3. Installing dependencies and running the application:**

```bash
# 1. Create a virtual environment (if you haven't already)
python -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate # On Linux/macOS
# .venv\Scripts\activate.bat # On Windows CMD
# .venv\Scripts\Activate.ps1 # On Windows PowerShell

# 3. Install the dependencies from requirements.txt
pip install -r requirements.txt

# 4. Run your FastAPI application using uvicorn
uvicorn main:app --reload --port 8000
```
This will start `uvicorn` serving your application at `http://127.0.0.1:8000`.

## Environment-Specific Notes

The cause and fix for `ModuleNotFoundError: No module named 'uvicorn'` can vary slightly depending on your deployment or development environment.

### Local Development

For local development, the primary concern is usually virtual environments. I always recommend using them (`venv` or `conda`). If you forget to activate your virtual environment, or you have multiple environments and install `uvicorn` in the wrong one, you'll hit this error.

*   **Best Practice:**
    1.  Create a dedicated virtual environment for each project: `python -m venv .venv`
    2.  Activate it: `source .venv/bin/activate` (or Windows equivalent)
    3.  Install dependencies: `pip install -r requirements.txt` (ensure `uvicorn` is in there!)
    4.  Always activate the environment before running `uvicorn` or any Python scripts for that project.
    5.  Use an IDE (like VS Code or PyCharm) that allows you to easily select and manage your project's virtual environment. This reduces manual activation errors.

### Docker Containers

When working with Docker, this error almost always means `uvicorn` wasn't installed *inside the container image*. The Python environment inside the container is completely isolated from your host machine.

*   **Common Fixes:**
    *   **Missing `pip install`:** Your `Dockerfile` needs a `RUN pip install -r requirements.txt` (or similar) command.
    *   **Incorrect `requirements.txt`:** Ensure `uvicorn` (and `fastapi`) are listed in your `requirements.txt` file and that this file is correctly `COPY`ied into the Docker image before the `pip install` command.
    *   **Incorrect Base Image:** If you're building on a very minimal base image, you might need to install `pip` itself first or ensure the image has a Python environment that works as expected.
    *   **Example `Dockerfile` Snippet:**

        ```dockerfile
        FROM python:3.10-slim-buster

        WORKDIR /app

        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt

        COPY . .

        CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
        ```
        In my experience, forgetting `COPY requirements.txt .` before `RUN pip install` is a frequent oversight that leads to this.

### Cloud Deployment (e.g., Heroku, AWS Elastic Beanstalk, Azure App Service)

Cloud platforms that deploy Python applications typically rely on a `requirements.txt` file to automatically install dependencies during the build/deployment process. This is very similar to the Docker scenario.

*   **Key Considerations:**
    *   **Missing `requirements.txt`:** The platform needs this file at the root of your project to know what to install.
    *   **`uvicorn` not in `requirements.txt`:** Double-check that `uvicorn` (and any necessary extras like `uvicorn[standard]`) is listed.
    *   **Deployment Logs:** Always check your deployment logs for the specific cloud provider. They will show you the output of the dependency installation step. If `pip install` failed for any reason (e.g., network issues during build, incompatible package versions), `uvicorn` might not be installed.
    *   **Buildpack/Runtime Configuration:** Some platforms (like Heroku) use buildpacks. Ensure you're using the correct Python buildpack and that it's configured to recognize your `requirements.txt`.
    *   **Start Command:** Ensure your platform's start command explicitly uses `uvicorn` (e.g., `uvicorn main:app --host 0.0.0.0 --port $PORT`) and that the platform's runtime environment allows `uvicorn` to execute.

## Frequently Asked Questions

**Q: What is a virtual environment and why should I use one?**
A: A virtual environment is an isolated Python environment that allows you to manage dependencies for different projects separately. This prevents conflicts where Project A needs `uvicorn==0.1.0` and Project B needs `uvicorn==0.2.0`. Using them ensures reproducibility and avoids cluttering your system-wide Python installation.

**Q: I installed `uvicorn` globally. Why am I still getting this error?**
A: If you installed `uvicorn` globally (without a virtual environment), it means it's available to your system's default Python interpreter. If you're getting the error, it's highly probable that your application is being run by a *different* Python interpreter (e.g., one inside an activated virtual environment, or a specific version like `python3.10` when `uvicorn` was installed for `python3.8`). Always verify `which python` and `which pip`.

**Q: Can I just run my FastAPI app with `python main.py` instead of `uvicorn main:app`?**
A: No, you cannot. `uvicorn` is an ASGI server. FastAPI applications are ASGI applications, and they require an ASGI server (like Uvicorn, Hypercorn, or Daphne) to run them over HTTP. `python main.py` would simply execute the Python script, but it wouldn't start a web server to listen for incoming requests.

**Q: How do I specify a particular version of `uvicorn`?**
A: You can specify the version when installing with `pip`: `pip install uvicorn==0.30.1`. It's even better practice to include this in your `requirements.txt` file for version control and reproducibility across environments.

**Q: Why does `uvicorn` seem to be missing even after `pip install` in Docker?**
A: This is usually because your `requirements.txt` file wasn't correctly copied into the Docker image before the `pip install` step, or the build context was wrong. Make sure your `COPY requirements.txt .` command is executed successfully before `RUN pip install -r requirements.txt` within your `Dockerfile`. Also, ensure `uvicorn` is indeed listed in that `requirements.txt` file.

## Related Errors