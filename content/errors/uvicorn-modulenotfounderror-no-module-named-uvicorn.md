# ModuleNotFoundError: No module named 'uvicorn'
> Encountering ModuleNotFoundError: No module named 'uvicorn' means Uvicorn is not installed in your current Python environment; this guide explains how to fix it.

## What This Error Means

When you see `ModuleNotFoundError: No module named 'uvicorn'`, it's Python telling you that it cannot find the `uvicorn` package in the environment where you're trying to run your application. This usually happens when you execute a command like `uvicorn main:app --reload` or `python -m uvicorn main:app --reload`, and the Python interpreter simply doesn't have the necessary module available for import.

Uvicorn is an ASGI server, essential for running modern asynchronous Python web frameworks like FastAPI and Starlette. Without it, your application's entry point, which expects Uvicorn to be present to serve the application, will fail immediately at startup. This isn't a bug in your code, but rather an environmental setup issue.

## Why It Happens

The core reason for this error is that the Python interpreter you're using to run your application does not have the `uvicorn` package installed or accessible within its `sys.path`. Python modules are typically installed into specific locations within your Python installation, and if `uvicorn` isn't in one of those spots for the active interpreter, you get this `ModuleNotFoundError`. It's a fundamental part of Python's module import system.

In my experience, this is one of the most common "gotchas" for both new developers and seasoned engineers switching between projects or environments. It's almost always a path or installation issue rather than a code problem.

## Common Causes

This error, while seemingly simple, can stem from several common scenarios:

1.  **Uvicorn is simply not installed:** The most straightforward cause. You or your deployment script forgot to run `pip install uvicorn` (or `pip install "uvicorn[standard]"`) in the target environment.
2.  **Incorrect Python environment activated:** You might have multiple Python installations on your system (e.g., system Python, Homebrew Python, `pyenv`, `conda`, different virtual environments). You might have installed Uvicorn in one environment but are attempting to run your application using another, where Uvicorn is absent. This is particularly prevalent when working with virtual environments and forgetting to `source venv/bin/activate`.
3.  **`pip` and `python` mismatch:** Sometimes, `pip` refers to the installer for one Python version, while `python` (or `python3`) refers to a different one. For instance, `pip install uvicorn` might install to Python 2.x's site-packages, while `python3 your_app.py` uses Python 3.x, which doesn't see the installed module. Or, you might use `pip` from your global Python installation, but your `python` command points to an activated virtual environment where `uvicorn` hasn't been installed.
4.  **Deployment pipeline issues:**
    *   **Docker:** The `Dockerfile` might be missing the `RUN pip install uvicorn` command, or it might be installing into a different Python version than the one used to run the application within the container.
    *   **Cloud Platforms:** Platforms like AWS Elastic Beanstalk, Heroku, Azure App Service, or Google App Engine rely on a `requirements.txt` file. If `uvicorn` (or `uvicorn[standard]`) is missing from this file, or if the platform's build process fails to install dependencies correctly, you'll encounter this error.
    *   **CI/CD:** The CI/CD pipeline might not be setting up the Python environment correctly, or it might be caching dependencies incorrectly, leading to an environment where `uvicorn` is not present when the application attempts to start.
5.  **`PATH` environment variable issues:** Less common for `uvicorn` specifically, but if `uvicorn` was installed via `pipx` or into a custom location not on your system's `PATH`, the shell might not find the `uvicorn` executable even if the module is technically installed for *a* Python interpreter. However, this particular `ModuleNotFoundError` specifically points to Python's import system, not the shell's `PATH`.

## Step-by-Step Fix

Addressing this error typically involves ensuring Uvicorn is correctly installed in the Python environment your application uses.

1.  ### Verify Your Python Environment
    First, confirm which Python interpreter and `pip` installer you are currently using. This is crucial, especially if you have multiple Python versions or virtual environments.

    ```bash
    which python
    which pip
    ```
    If you're using a virtual environment, `which python` should point to something like `/path/to/your/venv/bin/python`. If it points to a system-wide Python (e.g., `/usr/bin/python3`), ensure that's where you *intend* to install Uvicorn.

2.  ### Activate Your Virtual Environment (If Applicable)
    If you're working on a project that uses a virtual environment (which is highly recommended), make sure it's activated.

    ```bash
    # Navigate to your project directory
    cd my-fastapi-project

    # Activate the virtual environment
    source venv/bin/activate
    # or if using conda:
    # conda activate myenv
    ```
    After activation, re-run `which python` and `which pip` to confirm they now point inside your virtual environment.

3.  ### Install Uvicorn
    With the correct environment activated, install Uvicorn using `pip`. For most FastAPI or Starlette projects, you'll want the `standard` extras which includes `websockets` support.

    ```bash
    pip install "uvicorn[standard]"
    ```
    If you only need the basic HTTP server, `pip install uvicorn` is sufficient, but I generally recommend the `standard` install to avoid future `websockets` related `ModuleNotFoundError` issues down the line if your application starts using them.

4.  ### Verify Uvicorn Installation
    After installation, you can confirm `uvicorn` is now visible to your current Python environment:

    ```bash
    pip show uvicorn
    ```
    This command should output details about the installed `uvicorn` package, including its version and location. If it shows information, it's installed.

    You can also try a quick Python console test:
    ```bash
    python -c "import uvicorn; print(uvicorn.__version__)"
    ```
    If this runs without a `ModuleNotFoundError`, you're good.

5.  ### Run Your Application
    Now, attempt to run your application again using the command you were trying previously.

    ```bash
    uvicorn main:app --reload
    # Or, if uvicorn is not in PATH or you prefer explicit module execution:
    python -m uvicorn main:app --reload
    ```
    If everything is correctly set up, your application should now start without the `ModuleNotFoundError`.

6.  ### Reinstall/Upgrade (If Still Having Issues)
    Occasionally, a corrupted installation or dependency conflict can cause issues. If the problem persists, try uninstalling and reinstalling Uvicorn:

    ```bash
    pip uninstall uvicorn
    pip install "uvicorn[standard]"
    ```

## Code Examples

Here are some copy-paste ready examples for typical scenarios.

### Basic Uvicorn Installation

To get Uvicorn installed in your *current* Python environment:

```bash
pip install "uvicorn[standard]"
```

### Running a Simple FastAPI App

Assume you have a `main.py` like this:

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello from Lena's server!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

To run it, first ensure `uvicorn` and `fastapi` are installed:

```bash
pip install fastapi "uvicorn[standard]"
```

Then execute:

```bash
uvicorn main:app --reload --port 8000
```
Or, if you want to explicitly use the `python -m` method:
```bash
python -m uvicorn main:app --reload --port 8000
```

### Using `requirements.txt`

For projects, always use a `requirements.txt` file to manage dependencies.

```text
# requirements.txt
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
```

Install all dependencies from the file:

```bash
pip install -r requirements.txt
```

This ensures all required packages, including `uvicorn`, are installed consistently.

## Environment-Specific Notes

The `ModuleNotFoundError` for Uvicorn often manifests differently depending on your deployment target.

### Local Development

For local development, the key is consistency with virtual environments. I've seen this in production when developers forget to activate their virtual environment before installing or running their app. Always remember:
1.  Create a virtual environment (`python -m venv venv`).
2.  Activate it (`source venv/bin/activate`).
3.  Install dependencies (`pip install -r requirements.txt`).
4.  Run your app (`uvicorn main:app`).
This workflow isolates your project's dependencies, preventing conflicts with other projects or your system Python.

### Docker

In a Dockerized environment, the `ModuleNotFoundError` means your `Dockerfile` isn't correctly installing `uvicorn`.

A robust `Dockerfile` for a FastAPI application might look like this:

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# This specifically ensures uvicorn[standard] is installed
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Expose port 8000 for uvicorn
EXPOSE 8000

# Run uvicorn when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
I usually confirm `requirements.txt` explicitly lists `uvicorn[standard]` and that the `pip install` command is executed *after* `requirements.txt` is copied to prevent caching issues from previous builds if requirements change.

### Cloud Platforms (AWS Elastic Beanstalk, Heroku, Azure App Service, Google App Engine)

These platforms typically rely on a `requirements.txt` file in your project's root directory to determine what Python packages to install during their build process.

*   **AWS Elastic Beanstalk:** It automatically runs `pip install -r requirements.txt` when deploying Python applications. Ensure `uvicorn[standard]` is in this file. If you're using a custom `Procfile` for running your application, ensure it uses the `uvicorn` command or `python -m uvicorn`.
*   **Heroku:** Similar to Elastic Beanstalk, Heroku also uses `requirements.txt`. Your `Procfile` should define how to start your web process, e.g., `web: uvicorn main:app --host 0.0.0.0 --port $PORT`. If your `requirements.txt` is missing `uvicorn`, you'll hit this error during runtime.
*   **Azure App Service / Google App Engine:** Both platforms also look for `requirements.txt`. For App Service, you might need to specify a startup command in your application settings if you're not using the default `gunicorn` with `uvicorn` worker setup. Google App Engine's flexible environment will also use `requirements.txt`.

In all these cases, the fix is to explicitly include `uvicorn[standard]` in your `requirements.txt` file and verify that the platform's build logs show a successful installation of all dependencies. I've often seen this error in production when a developer updates an application but forgets to update the `requirements.txt` or to push the updated `requirements.txt` along with the code.

## Frequently Asked Questions

**Q: `uvicorn` is installed, `pip show uvicorn` works, but I still get `ModuleNotFoundError`!**
**A:** This almost certainly means you have multiple Python environments, and `pip show uvicorn` is checking one environment, while the `python` command you're using to run your application is invoking a *different* Python interpreter. Re-verify `which python` and `which pip`. Ensure they point to the *same* virtual environment or Python installation. For example, if `which python` returns `/usr/bin/python3`, but `which pip` returns `/path/to/my/venv/bin/pip`, they're mismatched. You need to either activate the virtual environment or install into the system-wide Python using `python3 -m pip install "uvicorn[standard]"`.

**Q: Should I install Uvicorn globally on my system?**
**A:** Generally, no. It's best practice to use Python virtual environments (`venv`, `conda`, `pyenv`) for each project. This isolates dependencies, prevents conflicts between projects, and keeps your global Python environment clean. Only install globally if you intend to use `uvicorn` as a system-wide utility for various projects *without* virtual environments (which is not recommended for development).

**Q: What's the difference between `pip install uvicorn` and `pip install "uvicorn[standard]"`?**
**A:** `pip install uvicorn` installs the base Uvicorn package. `pip install "uvicorn[standard]"` installs Uvicorn along with its "standard" extras, which currently includes the `websockets` library. If your FastAPI or Starlette application uses WebSockets, omitting `[standard]` will lead to a `ModuleNotFoundError` for `websockets`. It's good practice to include `[standard]` unless you're absolutely certain you don't need it.

**Q: My CI/CD pipeline is failing with this error. How do I fix it?**
**A:** Ensure your CI/CD script:
1.  Creates or activates a Python virtual environment.
2.  Explicitly runs `pip install -r requirements.txt` (making sure `uvicorn[standard]` is in `requirements.txt`).
3.  Uses the Python interpreter from that activated environment to run your tests or start your application.
Check the build logs for any `pip` installation failures or warnings that might indicate a problem.

**Q: What about `python -m uvicorn` versus `uvicorn` directly?**
**A:** `uvicorn` directly invokes the `uvicorn` executable script, which is usually created by `pip` in your virtual environment's `bin` directory (e.g., `venv/bin/uvicorn`). `python -m uvicorn` tells the Python interpreter to run the `uvicorn` module as a script. Both achieve the same result. I often prefer `python -m uvicorn` because it explicitly uses the Python interpreter that invoked it, helping to avoid `PATH` issues if the `uvicorn` executable isn't correctly linked or found in the shell's `PATH`. It guarantees the `uvicorn` module is loaded by *that specific* Python interpreter.

## Related Errors