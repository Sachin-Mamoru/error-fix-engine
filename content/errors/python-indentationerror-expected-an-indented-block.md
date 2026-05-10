# IndentationError: expected an indented block
> Encountering `IndentationError: expected an indented block` means Python found a line that should be indented but isn't, or vice-versa; this guide explains how to fix it with practical steps.

## What This Error Means

The `IndentationError: expected an indented block` is a fundamental syntax error in Python, signaling that the Python interpreter found an inconsistency in the way your code blocks are structured. Unlike many other programming languages that use curly braces (`{}`) or keywords like `begin`/`end` to delineate code blocks, Python relies entirely on whitespace – specifically, consistent indentation. When Python expects a block of code (e.g., after an `if` statement, `for` loop, `def` function definition, or `class` definition) and finds a line that isn't indented or is inconsistently indented, it raises this specific error. This error is always caught during the parsing phase, meaning your program won't even start executing if this syntax issue is present.

## Why It Happens

This error occurs because Python's grammar mandates that certain statements introduce a new, indented block of code. When you use keywords like `if`, `else`, `elif`, `for`, `while`, `try`, `except`, `finally`, `with`, `def`, or `class`, and you terminate the line with a colon (`:`), Python expects the very next line (and subsequent lines belonging to that block) to be indented at a new, consistent level. If Python encounters a line that it believes should be part of this new block but finds it at the same indentation level as the preceding statement, or at a different, inconsistent indentation, it throws an `IndentationError`.

In my experience, this is one of the most common early errors new Python developers encounter, but it also trips up seasoned engineers when they're rushing, refactoring, or copying code snippets.

## Common Causes

Identifying the root cause of an `IndentationError` often comes down to a few typical culprits:

1.  **Missing Indentation:** The most straightforward cause is simply forgetting to indent a line that should be part of a code block.
    ```python
    def calculate_sum(a, b):
    result = a + b # ERROR: This line should be indented
        return result
    ```
    Python expects `result = a + b` to be indented under `def calculate_sum(a, b):`.

2.  **Over-indentation:** Indenting a line when it should logically be at a higher (less indented) level. This often happens with `else`, `elif`, `except`, or `finally` clauses that aren't aligned with their corresponding `if` or `try` blocks.
    ```python
    if condition:
        do_something()
        else: # ERROR: 'else' should be at the same level as 'if'
            do_another_thing()
    ```

3.  **Inconsistent Indentation (Mixed Tabs and Spaces):** This is, by far, the most insidious and frustrating cause. Some editors insert tab characters (`\t`), while others insert a specified number of space characters (e.g., 4 spaces) when you press the Tab key. Python treats tabs and spaces as distinct characters. If you mix them within the same file or even within the same block, Python can get confused because what looks correctly aligned to your eye might be a different character sequence to the interpreter. For instance, one line might be indented with 4 spaces, while the next (which *looks* aligned in your editor) might be indented with a single tab character, which Python might interpret as 8 spaces, leading to an inconsistency. I've seen this in production when developers copy-paste code from different sources, or when multiple developers with different editor configurations work on the same file.

4.  **Empty Blocks:** Python requires *something* to be in an indented block. If you define a function or a conditional and leave the block completely empty, it will raise this error.
    ```python
    def incomplete_function():
    # ERROR: expected an indented block
    ```
    The fix here is to explicitly state that the block is intentionally empty using the `pass` statement.

5.  **Copy-Pasting Errors:** When you copy code snippets from web pages, documentation, or other files, the source might have different indentation conventions (e.g., tabs, 2 spaces, 8 spaces). Pasting this directly into a file that uses 4 spaces can introduce inconsistencies that are hard to spot visually.

## Step-by-Step Fix

Addressing an `IndentationError` is usually a process of careful inspection and correction.

1.  **Locate the Error Line:** Python's traceback is your best friend here. It will tell you the file name and the exact line number where the `IndentationError` was detected.
    ```
    File "my_script.py", line 5
        print("Hello")
    IndentationError: expected an indented block
    ```
    In this example, the error is on `line 5`.

2.  **Examine the Preceding Line(s):** Look at the line indicated by the traceback, and critically, the line *immediately preceding* it. The preceding line will almost always contain a colon (`:`) at the end, indicating the start of a new block. For example, if the error is on line 5, check line 4 for `def`, `if`, `for`, etc., followed by a colon.

3.  **Check for Mixed Tabs and Spaces:** This is crucial. Many modern text editors and IDEs have features to visualize whitespace characters (e.g., dots for spaces, arrows for tabs) or to convert all tabs to spaces (or vice-versa).
    *   **In VS Code:** Use `View > Render Whitespace` or look at the status bar for "Spaces: 4" (or "Tabs: 4"). You can change this by clicking on it.
    *   **In Sublime Text:** `View > Indentation > Show White Space` or `View > Indentation > Convert Indentation to Spaces`.
    *   **In Vim/Neovim:** `:set list` will show `$` at EOL and `^I` for tabs. `:set expandtab` and `:retab` can convert tabs to spaces.
    The goal is to ensure *all* indentation in your file uses the same character (preferably 4 spaces, as per PEP 8).

4.  **Correct the Indentation Level:**
    *   If a line is not indented enough, add spaces until it aligns correctly with the expected block level.
    *   If a line is over-indented, remove spaces until it aligns correctly.
    *   If a keyword like `else` or `except` is misaligned, ensure it matches the indentation level of its corresponding `if` or `try` statement.

5.  **Use `pass` for Intentionally Empty Blocks:** If you're prototyping or you genuinely need an empty block, insert the `pass` statement.
    ```python
    def my_future_function():
        pass # This tells Python the block is intentionally empty
    ```

6.  **Utilize Linters and Formatters:** Tools like `flake8` or `pylint` will catch indentation issues early. Auto-formatters like `black` or `autopep8` can automatically fix many indentation and formatting issues, enforcing a consistent style across your codebase. Integrating these into your development workflow or CI/CD pipeline is a powerful preventative measure.

    ```bash
    # Install a linter/formatter
    pip install flake8 black

    # Run flake8 to check for errors, including indentation (E111, E112, E113)
    flake8 my_script.py

    # Use black to automatically format and fix indentation (careful, it's opinionated!)
    black my_script.py
    ```

## Code Examples

Here are some concise, copy-paste ready examples demonstrating the error and its fix.

**Example 1: Missing Indentation**

```python
# CODE WITH ERROR
def greet(name):
print(f"Hello, {name}!") # This line should be indented

# FIX
def greet(name):
    print(f"Hello, {name}!")
```

**Example 2: Incorrect De-indentation (e.g., with `else`)**

```python
# CODE WITH ERROR
is_logged_in = True
if is_logged_in:
    print("Welcome back!")
    else: # 'else' is over-indented here
        print("Please log in.")

# FIX
is_logged_in = True
if is_logged_in:
    print("Welcome back!")
else:
    print("Please log in.")
```

**Example 3: Empty Block**

```python
# CODE WITH ERROR
def placeholder_action():
# This will raise IndentationError: expected an indented block

# FIX
def placeholder_action():
    pass # Use 'pass' for empty blocks
```

**Example 4: Hypothetical Mixed Tabs and Spaces (Difficult to represent purely in text, but conceptually important)**

Imagine this scenario. In your editor, it *looks* correct:

```python
def example_func():
....print("Line 1") # 4 spaces
->..print("Line 2") # 1 tab, then 2 spaces
```
Python would see the second line as incorrectly indented relative to the first, even if they appear aligned. The fix involves converting all tabs to spaces (or vice-versa, but spaces are preferred) throughout the file.

## Environment-Specific Notes

The `IndentationError` itself is a core Python syntax issue, so it manifests identically across different environments. However, the debugging and prevention strategies can differ slightly.

*   **Local Development:**
    Your Integrated Development Environment (IDE) or text editor is your primary tool here. Modern IDEs like VS Code, PyCharm, Sublime Text, and Atom are excellent at auto-indenting, displaying whitespace characters, and even automatically converting tabs to spaces. Configuring your editor to follow PEP 8 standards (4 spaces per indentation level, no tabs) is the best preventative measure. Local `git diff` commands can also highlight whitespace changes, which I find incredibly useful when reviewing merge requests that suddenly introduce these errors.

*   **CLI / Build Systems:**
    When you run a Python script directly from the command line (`python my_script.py`) or as part of a build process (e.g., a CI/CD pipeline executing `pytest`), this error will halt execution immediately. The stack trace will point to the exact file and line number. This is where linting tools like `flake8` become invaluable. Running `flake8 my_script.py` as part of a pre-commit hook or a build step can catch these errors *before* the code even attempts to run, saving valuable debugging time.

*   **Docker Containers:**
    Inside a Docker container, Python behaves identically. If your Python application inside a Docker container throws an `IndentationError`, it means the source code that was built into the image or mounted into the container has the indentation issue. The fix isn't specific to Docker; it's about correcting the source code on your host machine. If you're debugging inside a running container using `docker exec -it <container_id> bash` and then editing files with `vi` or `nano`, be mindful of those editors' default tab/space settings to avoid introducing new errors. I've often seen this issue arise when building Docker images where the copy-paste operation during the `Dockerfile` build inadvertently propagates bad indentation from a developer's local machine.

*   **Cloud Platforms (AWS Lambda, Google Cloud Functions, Azure Functions):**
    When deploying Python code to serverless platforms or other cloud services, the code is typically packaged (e.g., as a `.zip` file) and uploaded. If an `IndentationError` occurs, it indicates a problem with the code *before* deployment. The cloud environment simply executes the Python interpreter on your provided code. Debugging involves checking your local source, ensuring it passes linting/formatting, and then re-packaging and re-deploying. I've seen this in production when deploying Python functions to Lambda where a developer copy-pasted a snippet from an online source that used tabs into an existing 4-space codebase, leading to deployment failures only caught at runtime.

## Frequently Asked Questions

**Q: Can I use tabs instead of spaces for indentation?**
**A:** Python 3 allows the use of tabs for indentation, but PEP 8 (Python's style guide) strongly recommends using 4 spaces per indentation level. More importantly, you *must not mix* tabs and spaces in the same file for indentation. Mixing them is a primary cause of `IndentationError`. Consistency is paramount.

**Q: My code *looks* perfectly indented, but I still get the error. Why?**
**A:** This almost certainly points to mixed tabs and spaces. What looks aligned to your eyes in your editor might be interpreted differently by Python because a tab character and a sequence of space characters (e.g., four spaces) are distinct. Use your editor's "show whitespace characters" feature to reveal hidden tabs.

**Q: How can I prevent `IndentationError` in the future?**
**A:** Configure your editor or IDE to automatically convert tabs to spaces (typically 4 spaces per indent). Use code formatters like `Black` or `autopep8` which automatically standardize your code's indentation. Integrate linters like `flake8` into your development workflow and CI/CD pipelines to catch these issues early.

**Q: Is this error unique to Python?**
**A:** While the concept of incorrect indentation can exist in other languages (e.g., poorly formatted XML or YAML), the `IndentationError: expected an indented block` is specific to Python because of its unique syntax where indentation defines code blocks, unlike languages that use explicit delimiters like curly braces.

**Q: What if I want an empty code block?**
**A:** If you need a placeholder or an intentionally empty block (e.g., for a function you'll implement later, or a conditional branch that does nothing), use the `pass` statement. This tells Python to do nothing and satisfies the interpreter's expectation for an indented block.

## Related Errors
(none)