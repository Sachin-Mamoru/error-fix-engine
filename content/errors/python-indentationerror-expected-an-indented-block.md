# IndentationError: expected an indented block
> Encountering Python's IndentationError: expected an indented block means your code has incorrect spacing; this guide explains how to fix it efficiently.

## What This Error Means

Python is distinct from many other programming languages because it relies on whitespace, specifically indentation, to define code blocks. Unlike languages that use curly braces or keywords like `begin`/`end`, Python uses indentation as a fundamental part of its syntax.

The `IndentationError: expected an indented block` message indicates that the Python interpreter was expecting a block of code to follow a specific statement, but it found something else, or nothing at all, at an unexpected indentation level. This error typically occurs after statements that introduce a new scope or control structure, such as `if`, `for`, `while`, `def`, `class`, or `try`/`except` blocks. When the interpreter encounters one of these, it anticipates the subsequent line (or lines) to be indented at a deeper level, forming the body of that block. If this expectation isn't met, due to inconsistent indentation or a structural omission, Python raises this error. It's the interpreter's way of saying, "I expected a properly indented section of code here, but the structure doesn't match."

## Why It Happens

This error arises because Python's parser strictly enforces consistent indentation as part of its grammatical rules. For Python, indentation isn't merely stylistic; it's syntactical. When the parser encounters a statement that requires a new code block (e.g., `def my_function():`), it expects the very next logical line of code to be indented. If the line immediately following the colon is at the same indentation level as the preceding statement, or if its indentation is inconsistent with other lines meant to be in that block, Python cannot correctly parse the code.

The core reason is a violation of Python's structural grammar. The parser's state machine expects specific tokens and indentation levels. When this expectation is violated, it signals that the code's "shape" doesn't conform, leading to a parsing failure before execution can even begin. In my experience, this is one of the most common early-stage errors developers encounter, particularly when transitioning from languages with different block structuring conventions.

## Common Causes

I've debugged countless `IndentationError` instances throughout my career, from small scripts to large production systems. Here are the most frequent causes:

1.  **Missing Colon (`:`):** This is a very common oversight. Statements that introduce a new block—such as `if`, `for`, `while`, `def`, `class`, `try`, `except`, `finally`, `with`, and `elif`—must end with a colon. Forgetting it means the interpreter doesn't recognize that a new block is supposed to begin, leading to an `IndentationError` on the subsequent indented line.

    ```python
    # Incorrect: Missing colon
    if condition
        print("Condition is true")
    ```

2.  **Empty Blocks:** Python requires code blocks to be explicit, even if they perform no action. You cannot have an `if` statement or function definition immediately followed by nothing. If you intend a block to be empty, you must use the `pass` keyword.

    ```python
    # Incorrect: Empty function body
    def placeholder_function():
    ```

3.  **Mixed Tabs and Spaces:** This is a classic Python pitfall. Python treats tabs and spaces as distinct characters. If you use spaces for some indentation levels and tabs for others *within the same file*, or even within the *same logical block*, the interpreter will become confused and raise an `IndentationError`. This is particularly tricky because many text editors can render tabs and spaces identically, making the issue invisible to the naked eye. I've spent hours tracking this down in large files.

4.  **Incorrect Indentation Level:** Even if you consistently use spaces (or tabs), the *number* of spaces or tabs must be uniform for lines at the same logical level within a block. For example, indenting one line with 3 spaces and the next with 4 spaces (when 4 is the expected standard) within the same block will trigger this error. Python's parser expects a consistent step for each indentation level.

    ```python
    # Incorrect: Inconsistent spacing
    def my_function():
        if True:
            print("First line")
             print("Second line") # This line has 5 spaces instead of 8
    ```

5.  **Trailing Whitespace or Invisible Characters:** Less common, but sometimes extra spaces at the end of a line that should be followed by an indented block can interfere. Similarly, unexpected invisible characters might cause parsing issues.

## Step-by-Step Fix

When an `IndentationError: expected an indented block` appears, follow these steps systematically to diagnose and resolve it:

1.  **Locate the Error Line and Context:** The traceback will point to a specific line number where the interpreter *expected* an indented block. Start your investigation there. The actual cause of the error is often on the line *immediately preceding* the reported error line (e.g., the line with the `if` or `def` statement).

    ```bash
    Traceback (most recent call last):
      File "my_app.py", line 7
        print("This line has bad indentation somewhere above.")
    IndentationError: expected an indented block
    ```
    In this example, line 7 is where the `print` statement is. The actual error condition (e.g., a missing colon) likely exists on line 6 or earlier.

2.  **Check for Missing Colons (`:`):** Review the line directly before the one indicated in the traceback. Does it introduce a new block (`if`, `for`, `def`, `class`, `try`, `with`, etc.)? If so, ensure it ends with a colon (`:`). This is a very frequent oversight.

    ```python
    # Before fix
    if user_authenticated
        redirect_to_dashboard()

    # After fix
    if user_authenticated:
        redirect_to_dashboard()
    ```

3.  **Verify Indentation Consistency (Spaces vs. Tabs):** This is critical.
    *   **Use an IDE or text editor that can visualize whitespace.** Most modern editors (e.g., VS Code, PyCharm, Sublime Text) allow you to enable "show invisible characters" or "show whitespace." Look for visual cues distinguishing spaces from tabs.
    *   **Ensure you are using *either* spaces *or* tabs consistently throughout the *entire file*.** The PEP 8 style guide strongly recommends using 4 spaces per indentation level.
    *   If you find a mix, configure your editor to convert tabs to spaces automatically, or use a tool to normalize the whitespace.

    Python includes a utility to help detect mixed indentation:

    ```bash
    python -m tabnanny your_script.py
    ```
    This command will scan your Python file and report any lines where inconsistent use of tabs and spaces is detected. It's incredibly useful for quick validation.

4.  **Ensure Uniform Indentation Level:** Within any given block, all lines at the same logical level must be indented by the same number of spaces (or tabs). If one line in a block uses 4 spaces and the next line in the same block uses 3 or 5 spaces, Python will raise this error. Your editor's "reformat code" or "reindent selection" feature can often correct these inconsistencies rapidly.

5.  **Handle Empty Blocks with `pass`:** If you intend for a block to be empty—perhaps as a placeholder during development—you must explicitly use the `pass` keyword.

    ```python
    # Before fix
    def setup_database():

    # After fix
    def setup_database():
        pass
    ```

6.  **Review Copy-Pasted Code:** When copying code from external sources (webpages, chat, other editors), differing whitespace settings can easily introduce `IndentationError` issues. Always paste code into your editor and immediately apply its "format document" or "reindent" function to conform it to your project's standards.

By methodically following these steps, you can efficiently identify and resolve the root cause of an `IndentationError`.

## Code Examples

Here are concise, copy-paste ready examples demonstrating common `IndentationError` scenarios and their correct implementations.

**Scenario 1: Missing Colon After Control Flow Statement**

```python
# INCORRECT: Missing colon after 'for' statement
def process_list(items):
    for item in items
        print(f"Processing {item}")

# CORRECT: Added colon to 'for' statement
def process_list(items):
    for item in items:
        print(f"Processing {item}")
```

**Scenario 2: Empty Block Without `pass`**

```python
# INCORRECT: Function body is empty
def calculate_metrics():

# CORRECT: Use 'pass' for an intentionally empty block
def calculate_metrics():
    pass
```

**Scenario 3: Inconsistent Indentation Level**

(Note: Visualizing mixed tabs/spaces or inconsistent indentation levels precisely in plain text is hard, but this example illustrates the conceptual error of uneven spacing.)

```python
# INCORRECT: Inner 'if' block has inconsistent indentation
def authenticate_user(username, password):
    if username == "admin":
        if password == "secret":
            print("Admin access granted")
           # This line has 11 spaces, not the expected 12 for the third level
        else:
            print("Incorrect password for admin")
    else:
        print("Invalid username")

# CORRECT: Consistent 4-space indentation at each level
def authenticate_user(username, password):
    if username == "admin":
        if password == "secret":
            print("Admin access granted")
        else:
            print("Incorrect password for admin")
    else:
        print("Invalid username")
```

## Environment-Specific Notes

An `IndentationError` is fundamentally a parser error, meaning it occurs before code execution. While the error itself is consistent, where you encounter its output and how you address it can differ by environment.

*   **Local Development (CLI):** When running `python your_script.py` locally, the error traceback immediately prints to your console. This is the simplest scenario for debugging, as you have direct access to your files and editor. Interactive shells like `ipython` will also flag this immediately if you paste multi-line code with bad indentation.

*   **Build Systems / CI/CD Pipelines:** In CI/CD environments (e.g., GitHub Actions, GitLab CI, Jenkins), this error will halt any Python-dependent step. The traceback will be visible in the build logs. You'll need to locate the file and line number in the logs, then correct it in your version control system. I've seen `IndentationError` prevent Docker image builds from completing if the entrypoint or a setup script has a problem.

*   **Docker Containers:** Inside a Docker container, Python behaves as it does on a local machine. The `IndentationError` will cause your application to crash upon startup, with the traceback sent to `stdout`/`stderr`. These logs are retrieved using `docker logs <container_id>`. Ensure that no automated process within your Dockerfile or entrypoint is inadvertently corrupting indentation.

*   **Cloud Functions (AWS Lambda, Google Cloud Functions, Azure Functions):** For serverless functions, an `IndentationError` will cause function invocations to fail. The full traceback is recorded in the cloud provider's logging service (e.g., AWS CloudWatch, Google Cloud Logging, Azure Monitor). Since code is often deployed as a zip artifact, local testing *before* deployment is crucial. Fixing it requires redeploying a corrected version of your code.

*   **Web Frameworks (Django, Flask, FastAPI):** In a web application, an `IndentationError` will typically prevent the application from starting or cause a specific view/route to fail if the error is within that function. The detailed Python traceback will be found in your application server logs (e.g., Gunicorn, uWSGI) or potentially your web server's error logs (Nginx, Apache).

Regardless of the environment, the core debugging process remains the same: identify the problematic line and correct the indentation or structure. The main difference lies in accessing the error output and the workflow for applying the fix.

## Frequently Asked Questions

**Q: Can an IDE automatically fix `IndentationError`?**
**A:** Yes and no. An IDE can't fix a missing colon or an omitted `pass` statement, as these are logical syntax errors. However, an IDE *excel* at preventing and fixing issues related to inconsistent tabs/spaces or incorrect indentation *levels*. Features like "Format Document" (e.g., `Ctrl+Alt+L` in PyCharm, `Shift+Alt+F` in VS Code) will auto-apply consistent indentation (usually 4 spaces, PEP 8 compliant). Enabling "show whitespace characters" is also invaluable for spotting hidden issues.

**Q: Why is Python so strict about indentation?**
**A:** Python's strict reliance on indentation for defining code blocks promotes code readability and consistency. By making it syntactical, Python forces developers to write visually structured code, eliminating ambiguity and ensuring a uniform style across projects. This design choice contributes significantly to Python's reputation for clean, maintainable code.

**Q: What if I use tabs and my colleague uses spaces?**
**A:** This is a recipe for `IndentationError`. The best practice, outlined in PEP 8, is to standardize on 4 spaces per indentation level. To prevent issues, configure all team members' editors to "Insert spaces when Tab is pressed" and to use "4 spaces per tab." Additionally, integrating code formatters like Black or linters like Flake8 into your CI/CD pipeline can enforce this consistency automatically.

**Q: The error points to a blank line or a comment. What's wrong?**
**A:** If the traceback points to a blank line or a comment, the actual problem typically lies on the non-blank, non-comment line *immediately preceding* it. Python expects an indented code block after an initiating statement (`if`, `def`, etc.). If it finds a blank line or a comment there instead of an actual indented line of code, it still raises the `IndentationError` because its expectation for a code block wasn't met.

**Q: Does this error occur at runtime or during parsing?**
**A:** `IndentationError` is a subclass of `SyntaxError`. This means it occurs during the initial parsing phase of your Python script or module, *before* any runtime execution begins. If a script has an `IndentationError`, the interpreter will detect it immediately when it tries to read and understand the file's structure, preventing the script from running at all. It never occurs in the middle of a running program.

## Related Errors