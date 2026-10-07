# pydantic.error_wrappers.ValidationError: value is not a valid integer
> Encountering this Pydantic validation error means your API received non-integer input where an integer was expected; this guide explains how to identify and fix the issue.

## What This Error Means

This error, `pydantic.error_wrappers.ValidationError: value is not a valid integer`, directly indicates a type mismatch during data validation. When you're building APIs with FastAPI, Pydantic acts as the underlying data validation and settings management library. It automatically checks incoming request data (query parameters, path parameters, request body) against the type hints you've defined in your Python code.

Specifically, this error means that Pydantic expected a field to contain an integer value (e.g., `0`, `1`, `-5`, `100`), but it received something that could not be successfully parsed or converted into an integer. This could be a string like `"hello"`, a floating-point number like `3.14`, an empty string `""`, or even `None` if the field wasn't explicitly marked as optional.

FastAPI intercepts this Pydantic `ValidationError` and typically returns a `422 Unprocessable Entity` HTTP status code to the client, along with a detailed JSON response explaining which field failed validation and why.

## Why It Happens

At its core, this error happens because the data model defined in your FastAPI application enforces a strict integer type, but the actual data provided by the client deviates from this expectation. FastAPI, using Pydantic, attempts to perform an automatic type coercion and validation.

Consider a simple scenario: you define an API endpoint that expects an `item_id: int` as a path parameter. When a client makes a request to `/items/abc`, Pydantic tries to convert `"abc"` into an integer, fails, and raises this `ValidationError`. The same mechanism applies to query parameters and the request body (when using Pydantic models).

In my experience, developers often assume a degree of leniency in type handling, especially if coming from languages with looser type systems. However, FastAPI and Pydantic are designed for robust API contracts, ensuring that data integrity is maintained from the moment data enters your system. This strictness prevents many common bugs further down the line, but it does mean that client input must adhere to the defined types.

## Common Causes

This `ValidationError` typically arises from a few common scenarios:

1.  **Sending Non-Numeric Strings:**
    *   **Client Input:** The most straightforward cause. A client sends a string like `"text"`, `"abc-123"`, or even `"one"` when an integer is expected.
    *   **Example:** A `GET /users/id?user_id=abc` request where `user_id` is typed as `int`.

2.  **Sending Floating-Point Numbers:**
    *   **Client Input:** If a client sends `3.14` or `5.0` when an `int` is expected, Pydantic will *not* automatically truncate or round it to an integer. It will raise this validation error because `3.14` is not strictly an integer.
    *   **Example:** A `POST` request with `{"price": 99.99}` where `price` is typed as `int`.

3.  **Empty Strings:**
    *   **Client Input:** An empty string `""` cannot be parsed as an integer. This often happens with form submissions or query parameters where a field might be left blank.
    *   **Example:** A `GET /search?page=` request where `page` is typed as `int`.

4.  **`None` Values Without `Optional`:**
    *   **Client Input:** If a client sends a `null` (JSON `null`) value for a field that is typed as `int` but not marked as `Optional[int]` (or `Union[int, None]`), Pydantic will reject it.
    *   **Example:** A `POST` request with `{"count": null}` where `count` is typed as `int`.

5.  **JSON Type Mismatch (e.g., Booleans):**
    *   **Client Input:** While less common for integers, sending a boolean `true` or `false` where an integer is expected will also lead to this error, as booleans are not integers in Python's strict type sense (though `True` evaluates to 1 and `False` to 0 in some contexts).
    *   **Example:** A `POST` request with `{"status_code": true}` where `status_code` is typed as `int`.

## Step-by-Step Fix

Troubleshooting this error is usually a process of identifying the source of the invalid input and then correcting either the client's data or your API's expected type.

1.  **Identify the Endpoint and Parameter:**
    *   When FastAPI returns a `422 Unprocessable Entity` response, the JSON body typically provides detailed information, including the `loc` (location) of the error. This `loc` array will tell you whether the error is in a `path`, `query`, or `body` parameter, and the name of the specific field causing the issue.
    *   For example: `{"loc": ["query", "page_number"], "msg": "value is not a valid integer"}` clearly points to the `page_number` query parameter.

2.  **Examine Client Requests:**
    *   **Logs:** Check your application logs, API Gateway logs (if deployed to cloud), or `uvicorn` console output. You'll see the incoming requests and often the raw request body or query parameters that caused the error.
    *   **`curl`:** Replicate the problematic request using `curl` or a similar tool. This helps isolate whether the issue is with your client code or the API definition.
        ```bash
        # Example of a bad request that would trigger the error
        curl -X GET "http://localhost:8000/items/my_item"
        curl -X POST -H "Content-Type: application/json" -d '{"quantity": "ten"}' "http://localhost:8000/process"
        ```
    *   **Client Code Review:** If you control the client, examine the code responsible for constructing the request to the problematic endpoint. Look for places where string concatenation might inadvertently create non-integer values, or where data from forms/inputs might not be properly cast.

3.  **Check Your API Schema (Pydantic Model/Type Hints):**
    *   **Path/Query Parameters:** Review the type hints for the parameters in your FastAPI route definition.
        ```python
        @app.get("/items/{item_id}")
        async def read_item(item_id: int): # Is 'int' the correct type here?
            return {"item_id": item_id}
        ```
    *   **Request Body:** If the error is in the request body, inspect your Pydantic model.
        ```python
        from pydantic import BaseModel

        class Item(BaseModel):
            name: str
            quantity: int # Is 'int' the correct type here?
        ```
    *   **Correction:** Ask yourself: "Should this field *always* be an integer, or can it sometimes be a string, a float, or `None`?"

4.  **Correct the Input or API Definition:**

    *   **If the input *should* be an integer:**
        *   **Client-side fix:** Ensure the client sends a valid integer. Cast values before sending them, or validate input fields to ensure only digits are entered.
            ```python
            # Client-side Python example
            item_id_str = "123"
            response = requests.get(f"http://localhost:8000/items/{int(item_id_str)}")
            ```
            ```json
            // Client-side JavaScript example for a POST body
            { "quantity": 10 } // Send as a number, not a string "10"
            ```

    *   **If the input *can legitimately be something else*:**
        *   **API-side fix (Type Hint Adjustment):**
            *   **Allow strings:** If you need to accept an ID that might be numeric or alphanumeric, change the type hint to `str`.
                ```python
                @app.get("/items/{item_id}")
                async def read_item(item_id: str): # Change to str
                    return {"item_id": item_id}
                ```
            *   **Allow floats:** If a field might be a decimal, use `float`.
                ```python
                from pydantic import BaseModel

                class Product(BaseModel):
                    price: float # Change to float
                ```
            *   **Allow optional values (including `None`):** Use `Optional` from the `typing` module or a `Union`. Remember to provide a default value if it's a query parameter.
                ```python
                from typing import Optional

                @app.get("/search/")
                async def search(page: Optional[int] = 1): # Allows page=null or missing, defaults to 1
                    return {"page": page}

                # For Pydantic models:
                class UserConfig(BaseModel):
                    max_items: Optional[int] = None # Allows max_items: null or missing
                ```
            *   **Custom validation:** For complex cases (e.g., converting "ten" to 10), you might need a custom Pydantic validator or a dependency function in FastAPI.

5.  **Test Thoroughly:**
    *   After making changes, re-run your tests or manually test the endpoint with both valid and invalid inputs to confirm the fix and ensure no new regressions were introduced.

## Code Examples

Here are some concise, copy-paste ready examples demonstrating how this error occurs and how to fix it.

### Example 1: Path Parameter (Causes Error)

A FastAPI application expecting an integer `item_id`:

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    """
    Retrieves an item by its integer ID.
    """
    return {"item_id": item_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Client Request (causing error):**

```bash
curl http://localhost:8000/items/abc
```

**Expected Error Response:**

```json
{
  "detail": [
    {
      "loc": [
        "path",
        "item_id"
      ],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

### Example 1: Fix - Client Sends Correct Type

Client sends a valid integer:

```bash
curl http://localhost:8000/items/123
```

**Expected Success Response:**

```json
{"item_id": 123}
```

### Example 1: Fix - API Accepts String if Needed

If `item_id` can be alphanumeric:

```python
# main_fixed.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: str): # Changed type hint to str
    """
    Retrieves an item by its ID, which can be a string.
    """
    return {"item_id": item_id}

# ... run app as before
```

**Client Request (now works):**

```bash
curl http://localhost:8000/items/abc
```

**Expected Success Response:**

```json
{"item_id": "abc"}
```

### Example 2: Request Body with Pydantic Model (Causes Error)

An API expecting an integer `quantity` in the request body:

```python
# main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Product(BaseModel):
    name: str
    quantity: int # Expecting an integer

@app.post("/products/")
async def create_product(product: Product):
    """
    Creates a new product with a name and integer quantity.
    """
    return product

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Client Request (causing error):**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "quantity": "five"}' \
  http://localhost:8000/products/
```

**Expected Error Response:**

```json
{
  "detail": [
    {
      "loc": [
        "body",
        "quantity"
      ],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

### Example 2: Fix - Client Sends Correct Type

Client sends a valid integer for `quantity`:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "quantity": 5}' \
  http://localhost:8000/products/
```

**Expected Success Response:**

```json
{"name": "Widget", "quantity": 5}
```

### Example 2: Fix - API Allows Optional/Nullable Quantity

If `quantity` might be `null` or missing, make it optional:

```python
# main_fixed.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional # Import Optional

app = FastAPI()

class Product(BaseModel):
    name: str
    quantity: Optional[int] = None # Now quantity can be int or None

@app.post("/products/")
async def create_product(product: Product):
    """
    Creates a new product with a name and an optional integer quantity.
    """
    return product

# ... run app as before
```

**Client Request (now works with `null`):**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"name": "Gadget", "quantity": null}' \
  http://localhost:8000/products/
```

**Expected Success Response:**

```json
{"name": "Gadget", "quantity": null}
```

## Environment-Specific Notes

Debugging `ValidationError`s can vary slightly depending on your deployment environment.

### Cloud Environments (AWS Lambda/API Gateway, Google Cloud Run, Azure Functions)

In serverless or container-based cloud environments, your FastAPI application runs behind a proxy like AWS API Gateway, a Google Cloud Load Balancer, or an Azure Front Door.

*   **Logging:** The most critical tool here is structured logging. Ensure your FastAPI application logs incoming requests and the full `422` error responses. Cloud providers offer integrated logging services (CloudWatch, Cloud Logging, Application Insights) where you can search and filter for these errors. I've often seen `ValidationError`s buried in logs, and quickly locating the `loc` field in the JSON error response is key.
*   **API Gateway/Load Balancer Logs:** These upstream services also generate logs. Sometimes, an incorrect client request might not even reach your application if the API Gateway has basic validation configured, but more often, the request will pass through, and your FastAPI app will generate the `422`. Check if your proxy is modifying the request in unexpected ways (e.g., converting query parameters).
*   **Observability Tools:** Utilize tracing and monitoring tools specific to your cloud (e.g., X-Ray for AWS, Cloud Trace for GCP) to follow the request path and pinpoint where the invalid data is introduced or rejected.
*   **Cold Starts:** During cold starts, the initial request might time out or behave unexpectedly, but subsequent requests should exhibit the standard Pydantic validation behavior. This error is rarely related to cold start issues directly.

### Docker

When running your FastAPI application in Docker containers, debugging typically involves:

*   **Container Logs:** The primary source of information. Use `docker logs <container_name_or_id>` to view the `uvicorn` output. This will show the `422 Unprocessable Entity` responses and the accompanying Pydantic validation details.
*   **Port Mapping:** Ensure that your Docker container's exposed port is correctly mapped to a host port. Misconfigured port mappings can lead to requests not reaching your application, but this usually results in connection errors rather than validation errors.
*   **Environment Variables:** If your integer values are being passed via environment variables and then parsed (e.g., using Pydantic `BaseSettings`), ensure these variables are correctly set in your Dockerfile or `docker run` command and are of the expected type (even though env vars are strings, Pydantic will attempt coercion). `MY_INT_VAR=5` will work, `MY_INT_VAR=five` will not.

### Local Development

Local development offers the most immediate feedback for these types of errors.

*   **Direct `uvicorn` Output:** When running your app with `uvicorn`, the `ValidationError` details, including the `loc` field, are printed directly to your console. This is often the quickest way to see exactly what Pydantic is complaining about.
*   **IDE Debuggers:** Use your IDE's debugger (e.g., VS Code, PyCharm) to set breakpoints in your FastAPI endpoint or Pydantic models. You can inspect the values of incoming parameters and the contents of the request body right as they are being processed by FastAPI and Pydantic. This allows you to see the exact value that caused the validation failure.
*   **Interactive Tools:** Tools like Postman, Insomnia, or even `curl` are invaluable for crafting specific requests and observing the API's immediate response.

## Frequently Asked Questions

**Q: Can Pydantic automatically convert floats like `5.0` to `5` if an `int` is expected?**
**A:** No, Pydantic is strict. While Python itself can cast `float` to `int` (e.g., `int(5.0)` is `5`), Pydantic's default behavior for an `int` type hint is to reject floats that are not exactly integers (e.g., `3.14`). If you need to accept floats and convert them, you'll need to define a custom validator or use a `float` type and explicitly cast it yourself within your endpoint logic.

**Q: How do I handle optional integer parameters or fields?**
**A:** Use `Optional[int]` (imported from `typing`) in your type hints. For query parameters, you can also provide a default value. For Pydantic models, you can set a default value of `None`.
Example: `page: Optional[int] = None` (for query) or `count: Optional[int] = None` (for model field).

**Q: What if I need to accept a string that *looks* like a number (e.g., "123") but parse it as an int?**
**A:** If the field is defined as `int`, Pydantic *will* automatically parse string representations of integers (e.g., `"123"` becomes `123`). The error occurs when the string *cannot* be parsed (e.g., `"abc"`). If you need to handle more complex string-to-int conversions (like "ten" to 10), you should define the field as `str` and then manually perform the conversion with error handling in your business logic.

**Q: Is this a FastAPI error or a Pydantic error?**
**A:** It is fundamentally a Pydantic `ValidationError`. FastAPI uses Pydantic for its data validation, so it catches this error and translates it into a standard HTTP `422 Unprocessable Entity` response, which is a common way for APIs to signal validation failures.

**Q: Can I customize the error message for invalid integers?**
**A:** Yes, you can customize Pydantic's error messages using `error_msg_templates` in `Config` for a `BaseModel`, or by using FastAPI's `HTTPException` with `RequestValidationException` handling. For simple cases, the default Pydantic message is often sufficient and very informative.

## Related Errors