# RuntimeError: dictionary changed size during iteration
> Encountering "RuntimeError: dictionary changed size during iteration" means you're attempting to modify a dictionary (add or remove items) while actively iterating over it; this guide explains why this happens and provides practical, reliable methods to fix it.

## What This Error Means

When you see `RuntimeError: dictionary changed size during iteration`, it signifies that your Python code is trying to alter the structure of a dictionary (either by adding new key-value pairs or deleting existing ones) at the same time it's looping through that very dictionary. Python's dictionary implementation includes safety mechanisms to prevent unpredictable behavior that could arise from such modifications during iteration. It's essentially Python telling you, "Hold on, you're changing the map while I'm trying to follow it!"

This isn't a bug in Python; rather, it's a deliberate design choice to help developers write more robust and predictable code. Modifying a collection while iterating over it can lead to skipped items, infinite loops, or other subtle bugs that are much harder to diagnose than a direct `RuntimeError`.

## Why It Happens

Python dictionaries, like many hash-based data structures, are not designed for concurrent modification and iteration. When you iterate over a dictionary, Python creates an internal iterator that keeps track of its current position. If the dictionary's size changes (meaning keys are added or removed), this internal iterator can become invalid because the underlying structure of the dictionary might have been reorganized (e.g., due to hash collisions or resizing operations).

To prevent accessing non-existent memory, skipping elements unexpectedly, or encountering an infinite loop, Python throws this `RuntimeError`. It's a fail-fast mechanism. Instead of allowing your program to continue with potentially corrupted state or unpredictable logic, it explicitly stops execution at the point of conflict, forcing you to address the root cause directly. This is crucial for maintaining data integrity, especially in applications where dictionary state is critical.

## Common Causes

In my experience, this error typically stems from a few common patterns:

1.  **Conditional Deletion:** The most frequent cause is iterating through a dictionary and trying to delete items that meet a certain condition. For example, removing entries where a value is `None` or an item has expired.
    ```python
    my_dict = {'a': 1, 'b': 2, 'c': 3}
    # This will cause the RuntimeError
    for key, value in my_dict.items():
        if value == 2:
            del my_dict[key]
    ```

2.  **Adding New Items:** Similarly, attempting to add new key-value pairs to the dictionary while looping through it will trigger the error. This often happens when processing existing items and deciding to cache or generate new related data within the same dictionary.
    ```python
    my_dict = {'item1': 'data', 'item2': 'more_data'}
    # This will also cause the RuntimeError
    for key, value in my_dict.items():
        new_key = key + '_processed'
        my_dict[new_key] = value.upper()
    ```

3.  **Nested Loops or Function Calls:** Sometimes, the modification isn't directly in the loop body. It might occur within a function that is called from inside the loop, and that function then modifies the dictionary that the outer loop is iterating over. This can be harder to spot because the modification isn't immediately obvious. I've seen this in production when a helper function, unaware of the ongoing iteration, clears a shared dictionary or adds new entries.

4.  **Global or Shared Dictionary Access:** If multiple parts of your application, or even different threads (though multi-threading introduces its own set of synchronization challenges beyond this specific error), access and modify the same dictionary, one part iterating while another modifies can lead to this runtime error.

## Step-by-Step Fix

The core principle to fix `RuntimeError: dictionary changed size during iteration` is to separate the iteration process from the modification process. Here’s how you can approach it:

1.  **Iterate Over a Copy of Keys or Items:**
    The simplest and most common fix is to iterate over a *copy* of the dictionary's keys or items. This way, your loop operates on a snapshot of the dictionary's state at the start of the iteration, allowing you to safely modify the original dictionary.

    *   **For modifying (deleting/adding) based on keys:**
        ```python
        my_dict = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        keys_to_delete = []
        for key in list(my_dict.keys()): # Iterate over a copy of keys
            if my_dict[key] % 2 == 0:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del my_dict[key]
        print(my_dict) # Output: {'a': 1, 'c': 3}
        ```
        Alternatively, you can delete directly if the number of operations is small:
        ```python
        my_dict = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        for key in list(my_dict.keys()): # Iterate over a copy of keys
            if my_dict[key] % 2 == 0:
                del my_dict[key] # Modify the original dict
        print(my_dict) # Output: {'a': 1, 'c': 3}
        ```

    *   **For modifying (deleting/adding) based on items (key-value pairs):**
        ```python
        my_dict = {'apple': 'red', 'banana': 'yellow', 'grape': 'purple'}
        items_to_process = list(my_dict.items()) # Iterate over a copy of items

        for key, value in items_to_process:
            if 'a' in key:
                # Example: adding new entries, or modifying existing ones
                my_dict[key.upper()] = value.upper()
                del my_dict[key] # Example: deleting original entry
        print(my_dict) # Output: {'APPLE': 'RED', 'GRAPE': 'PURPLE'} (banana was not processed)
        ```
        Notice that `list(my_dict.keys())` or `list(my_dict.items())` creates a new list containing the keys or items. The loop then iterates over this new list, which remains constant, while any modifications are applied to the original `my_dict`.

2.  **Use Dictionary Comprehension for Filtering/Transformation:**
    If your goal is to filter a dictionary or create a new one based on the existing one, dictionary comprehensions are often the most Pythonic and efficient solution. This creates an entirely new dictionary based on conditions or transformations without modifying the original in place.

    ```python
    my_dict = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    # Create a new dictionary containing only odd values
    new_dict = {key: value for key, value in my_dict.items() if value % 2 != 0}
    print(new_dict) # Output: {'a': 1, 'c': 3}
    print(my_dict)  # Output: {'a': 1, 'b': 2, 'c': 3, 'd': 4} (original remains unchanged)
    ```

3.  **Collect Keys/Items to Modify, Then Modify:**
    This is similar to iterating over a copy but explicitly separates the "identification" phase from the "modification" phase. This is particularly useful when you have complex logic for deciding what to modify.

    ```python
    my_dict = {'user1': {'active': True, 'last_login': '2023-01-01'},
               'user2': {'active': False, 'last_login': '2022-11-15'},
               'user3': {'active': True, 'last_login': '2023-03-20'}}

    users_to_deactivate = []
    for user_id, data in my_dict.items():
        if not data['active'] and data['last_login'] < '2023-01-01':
            users_to_deactivate.append(user_id)

    for user_id in users_to_deactivate:
        del my_dict[user_id] # Or update: my_dict[user_id]['active'] = False

    print(my_dict)
    # Output: {'user1': {'active': True, 'last_login': '2023-01-01'},
    #          'user3': {'active': True, 'last_login': '2023-03-20'}}
    ```

## Code Examples

Here are concise, copy-paste ready examples demonstrating the error and its common fixes.

### Example 1: Demonstrating the Error (Bad Practice)

```python
# bad_code.py
data_store = {
    "item_A": {"status": "pending", "value": 10},
    "item_B": {"status": "completed", "value": 20},
    "item_C": {"status": "pending", "value": 30},
    "item_D": {"status": "failed", "value": 40}
}

print("Original data:", data_store)

try:
    # Attempting to delete an item while iterating over data_store directly
    for key, details in data_store.items():
        if details["status"] in ["completed", "failed"]:
            print(f"Deleting {key}...")
            del data_store[key]
except RuntimeError as e:
    print(f"\nCaught expected error: {e}")

print("Data after attempted modification:", data_store)
```
**Output:**
```
Original data: {'item_A': {'status': 'pending', 'value': 10}, 'item_B': {'status': 'completed', 'value': 20}, 'item_C': {'status': 'pending', 'value': 30}, 'item_D': {'status': 'failed', 'value': 40}}
Deleting item_B...

Caught expected error: dictionary changed size during iteration
Data after attempted modification: {'item_A': {'status': 'pending', 'value': 10}, 'item_D': {'status': 'failed', 'value': 40}}
```
Notice `item_C` was skipped and `item_D` was not deleted because the iteration stopped prematurely.

### Example 2: Fixing with `list(my_dict.keys())`

```python
# fix_with_copy.py
data_store = {
    "item_A": {"status": "pending", "value": 10},
    "item_B": {"status": "completed", "value": 20},
    "item_C": {"status": "pending", "value": 30},
    "item_D": {"status": "failed", "value": 40}
}

print("Original data:", data_store)

# Iterate over a copy of keys, then modify the original dictionary
for key in list(data_store.keys()):
    if data_store[key]["status"] in ["completed", "failed"]:
        print(f"Deleting {key}...")
        del data_store[key] # Modifying the original data_store

print("Data after safe modification:", data_store)
```
**Output:**
```
Original data: {'item_A': {'status': 'pending', 'value': 10}, 'item_B': {'status': 'completed', 'value': 20}, 'item_C': {'status': 'pending', 'value': 30}, 'item_D': {'status': 'failed', 'value': 40}}
Deleting item_B...
Deleting item_D...
Data after safe modification: {'item_A': {'status': 'pending', 'value': 10}, 'item_C': {'status': 'pending', 'value': 30}}
```

### Example 3: Fixing with Dictionary Comprehension

```python
# fix_with_comprehension.py
data_store = {
    "item_A": {"status": "pending", "value": 10},
    "item_B": {"status": "completed", "value": 20},
    "item_C": {"status": "pending", "value": 30},
    "item_D": {"status": "failed", "value": 40}
}

print("Original data:", data_store)

# Create a new dictionary containing only items with "pending" status
processed_data_store = {
    key: details
    for key, details in data_store.items()
    if details["status"] == "pending"
}

print("Data after filtering (new dictionary):", processed_data_store)
print("Original data (unchanged):", data_store)
```
**Output:**
```
Original data: {'item_A': {'status': 'pending', 'value': 10}, 'item_B': {'status': 'completed', 'value': 20}, 'item_C': {'status': 'pending', 'value': 30}, 'item_D': {'status': 'failed', 'value': 40}}
Data after filtering (new dictionary): {'item_A': {'status': 'pending', 'value': 10}, 'item_C': {'status': 'pending', 'value': 30}}
Original data (unchanged): {'item_A': {'status': 'pending', 'value': 10}, 'item_B': {'status': 'completed', 'value': 20}, 'item_C': {'status': 'pending', 'value': 30}, 'item_D': {'status': 'failed', 'value': 40}}
```

## Environment-Specific Notes

The `RuntimeError: dictionary changed size during iteration` is fundamentally a Python language runtime error, meaning its root cause and primary fix remain consistent regardless of the execution environment. However, the *impact* and *detection* might vary:

*   **Cloud Functions (e.g., AWS Lambda, Google Cloud Functions):** In serverless environments, each invocation is typically isolated. If this error occurs, it will likely cause that specific function invocation to fail immediately. The function might retry automatically (depending on configuration), but it will continue to fail until the code is patched. Detection often involves reviewing function logs for the `RuntimeError` stack trace. Because functions are short-lived and often stateless, persistent dictionary modification issues across invocations are less common, but within a single invocation, the rules still apply.
*   **Containerized Applications (e.g., Docker, Kubernetes):** Within a Docker container running a Python application, this error will crash the Python process. If your application is managed by Kubernetes, the pod might enter a `CrashLoopBackOff` state, where Kubernetes repeatedly tries to restart the container. This is a clear indicator that the application is failing to start or run reliably. Logs from the failing container will contain the `RuntimeError`. The key difference here is the orchestration layer (Kubernetes) attempting restarts, potentially masking the immediate crash if not monitored closely.
*   **Local Development:** During local development, the error will simply stop your script or application. This is often the easiest environment to debug, as you have direct access to the console and can step through the code with a debugger. It's an excellent opportunity to catch and fix this error before it reaches more complex deployment environments.

In all these environments, the solution remains the same: identify where the dictionary is being modified during iteration and apply one of the safe modification strategies outlined in the "Step-by-Step Fix" section. The challenge sometimes is tracing *which* part of a complex application, possibly involving multiple modules or even threads, is responsible for the concurrent modification.

## Frequently Asked Questions

**Q: Why does Python raise an error instead of just letting me modify it?**
A: Python's behavior is a "fail-fast" strategy. Modifying a dictionary while iterating over it can lead to unpredictable outcomes like skipped elements, infinite loops, or even data corruption. By raising a `RuntimeError`, Python forces you to address this ambiguous state, making your code more predictable and robust.

**Q: Can I just wrap the problematic loop in a `try-except RuntimeError` block?**
A: While technically possible, this is generally a bad practice. Catching the `RuntimeError` doesn't fix the underlying logical flaw. You'd still be dealing with an incompletely processed or unpredictably modified dictionary, potentially leading to subtler bugs later. It's always better to fix the root cause by iterating over a copy or using comprehensions.

**Q: Does this error apply to lists or other collections as well?**
A: `RuntimeError: dictionary changed size during iteration` is specific to dictionaries. However, the *concept* of modifying any collection (like a list) while iterating over it can lead to similar issues (skipped elements, index out of bounds errors) if not handled carefully. For lists, it's generally safe to iterate backward when deleting items, or to build a new list with list comprehensions.

**Q: What about multi-threading? Does this error mean Python dictionaries are not thread-safe?**
A: This `RuntimeError` is primarily for single-threaded execution. When multiple threads access and modify the same dictionary, you can encounter much more complex issues like race conditions or inconsistent state, even without this specific `RuntimeError`. For multi-threaded scenarios, you need to use proper synchronization primitives (like `threading.Lock`) or thread-safe data structures. This runtime error is a distinct safety measure for sequential iteration.

**Q: Is it always bad to modify a dictionary?**
A: No, modifying a dictionary is a fundamental operation. The problem only arises when you modify it *while actively iterating over it* using a standard `for` loop. If you modify a dictionary outside of an ongoing iteration, or using one of the safe methods described (like iterating over a copy), it's perfectly fine.

## Related Errors