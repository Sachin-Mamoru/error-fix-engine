# django.db.utils.IntegrityError: duplicate key value violates unique constraint
> Encountering `django.db.utils.IntegrityError: duplicate key value violates unique constraint` means you've attempted to create or modify data that violates a unique database rule; this guide explains how to fix it.

## What This Error Means

This error message is a clear signal from your database, relayed through Django's ORM, that you've tried to perform an operation (usually an `INSERT` or `UPDATE`) that would result in a non-unique value being stored in a column or set of columns that are explicitly marked as unique. In essence, the database is telling you, "I cannot complete this action because it would break one of my fundamental rules for data integrity."

`IntegrityError` is a broad class of database errors in Django that indicate a problem with the integrity of your data. The "duplicate key value violates unique constraint" part specifically points to a unique constraint being triggered. This isn't just about primary keys (which are always unique by definition); it can apply to any field in your Django model where you've set `unique=True` or used `unique_together` in the `Meta` options.

## Why It Happens

At its core, this error occurs because a database schema has a rule (a "unique constraint" or "unique index") that prevents two rows from having the exact same value in a specific column (or combination of columns). When your Django application, via the ORM, sends a SQL query to the database that attempts to insert or update a row with a value that already exists for that constrained column, the database rejects the operation and raises this error.

From a Django perspective, this typically means:
*   You're calling `.save()` on a new model instance where one of its unique fields already holds a value present in the database.
*   You're calling `.save()` on an existing model instance, and you've changed a unique field's value to something that already exists in another record.
*   A database operation (like `bulk_create` or raw SQL) is attempting to insert data that violates this rule.

## Common Causes

In my experience, `IntegrityError` due to duplicate unique keys pops up in several common scenarios:

1.  **Duplicate Primary Key (PK):** While less common with Django's default auto-incrementing IDs, this can happen if you manually assign primary keys (e.g., UUIDs or custom IDs) and accidentally generate a duplicate, or if there's an issue with a sequence generator after a restore.
2.  **Duplicate Unique Field Values:** This is the most frequent cause. You have a field like `email` on a `User` model, `slug` on a `Product` model, or `SKU` on an `Item` model with `unique=True`. An attempt is made to save a record where this field's value clashes with an existing record.
3.  **Race Conditions:** This is a tricky one, especially in high-traffic applications. Two or more concurrent requests might try to create a new record with the *same* unique value (e.g., the same username) at nearly the same time. The first request succeeds, but the subsequent ones fail with this `IntegrityError` because the unique value now exists. I've seen this in production when user registration or content creation endpoints get hit simultaneously.
4.  **Faulty Application Logic for Unique Identifiers:** If your code generates unique identifiers like slugs or tracking codes without properly checking for existing values, you're bound to hit this. For example, generating a slug from a title without appending a number if a conflict exists.
5.  **Data Migration or Import Issues:** When importing data from an external source or running a custom data migration, if you don't account for existing unique values, you'll run into this. It often requires careful pre-processing of data or specific handling during the import.
6.  **`unique_together` Constraints:** If your model uses `unique_together` (e.g., `('product', 'warehouse')` to ensure a product only exists once per warehouse), attempting to create a record with an existing combination will trigger this error.

## Step-by-Step Fix

Addressing this error requires a systematic approach to understand *what* unique constraint is violated and *why* your application tried to violate it.

1.  **Identify the Exact Constraint and Value:**
    *   **Examine the Full Traceback:** Django's `IntegrityError` usually wraps the database driver's error. For PostgreSQL (which is common with Django), the error message is very helpful, often including `DETAIL: Key (field_name)=(value) already exists.` This tells you exactly which field (or fields for `unique_together`) and what value caused the problem.
    *   **Review Your Model:** Look at the model definition in `models.py` involved in the operation. Identify all fields with `unique=True` or `unique_together` in the `Meta` class.

2.  **Reproduce and Inspect:**
    *   **Can you reproduce it consistently?** If so, try to step through the code or log the exact data being saved to pinpoint the problematic value.
    *   **Query the Database:** Using the information from the traceback, directly query your database (via `dbshell`, `psql`, or Django shell) to confirm that the offending value already exists.

    ```python
    # Example: Check if an email already exists
    from myapp.models import User
    problematic_email = "conflict@example.com"
    if User.objects.filter(email=problematic_email).exists():
        print(f"User with email {problematic_email} already exists.")
    ```

3.  **Choose a Resolution Strategy:**

    *   **For New Object Creation (`.create()` or `.save()` on new instances):**
        *   **Use `get_or_create()`:** This is often the cleanest solution if your intent is to either retrieve an existing object or create a new one if it doesn't exist based on unique fields. This method is atomic and handles race conditions for many common scenarios.
        *   **Check Before Creating:** Implement explicit `.exists()` checks before calling `.create()` to decide whether to create or update.
        *   **Graceful Error Handling:** Wrap your creation logic in a `try...except IntegrityError` block to catch the error gracefully and provide user-friendly feedback or retry logic.

    *   **For Object Updates (`.save()` on existing instances):**
        *   **Verify Update Target:** Ensure you are updating the *correct* instance. Sometimes, code might fetch an object, modify a unique field, and then try to save, only to find that the *new* unique field value already belongs to a *different* object.
        *   **Use `update_or_create()`:** Similar to `get_or_create`, this can be useful if your goal is to update an object if it matches certain unique fields, or create it otherwise.

    *   **For Race Conditions:**
        *   `get_or_create()` is often sufficient. For very high-concurrency, complex scenarios, you might need database-level locking (less common with Django's ORM) or more sophisticated distributed locking mechanisms, though I rarely have to go that far for this specific error.

    *   **For Data Cleanup/Migration:**
        *   If the database already contains invalid duplicate data from a previous issue or migration, you'll need to clean it up. This is typically done with a one-off Django management command or direct SQL queries. **Always back up your database before performing data cleanup!**

4.  **Refine Application Logic:**
    *   **Validation:** Ensure your Django Forms or Django REST Framework serializers perform validation *before* attempting to save to the database. This provides a better user experience by catching the error earlier.
    *   **Slug Generation:** If you're generating slugs, use Django's `slugify` but wrap it in logic that checks for uniqueness and appends a number if necessary (e.g., `my-post`, `my-post-1`, `my-post-2`).

## Code Examples

Here are some practical code examples demonstrating common fixes:

```python
# Example 1: Using get_or_create for idempotent creation
# This is ideal when you want to create an object only if it doesn't already exist
from myapp.models import Product

product_name = "Luxury Smartphone"
product_sku = "LS-001"

try:
    product, created = Product.objects.get_or_create(
        sku=product_sku,
        defaults={'name': product_name, 'price': 999.99}
    )
    if created:
        print(f"Successfully created new product: {product.name} (SKU: {product.sku})")
    else:
        print(f"Product with SKU {product.sku} already exists, retrieved existing: {product.name}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

# Example 2: Explicitly checking existence before creating
# Useful if you need more control or specific error messages before hitting the DB
from myapp.models import User

new_email = "alice.smith@example.com"
new_username = "alice_smith"

if not User.objects.filter(email=new_email).exists():
    if not User.objects.filter(username=new_username).exists():
        User.objects.create(username=new_username, email=new_email, password="securepassword")
        print(f"User {new_username} created successfully.")
    else:
        print(f"Error: Username '{new_username}' is already taken.")
else:
    print(f"Error: Email '{new_email}' is already registered.")

# Example 3: Handling IntegrityError with try...except
# For situations where you might expect the error and want to handle it gracefully
from django.db import IntegrityError

def create_user_robust(username, email, password):
    try:
        user = User.objects.create(username=username, email=email, password=password)
        print(f"User {username} created successfully.")
        return user
    except IntegrityError as e:
        # Check if the error message contains specific constraint names if needed
        # (PostgreSQL errors are usually very detailed here)
        if "duplicate key value violates unique constraint" in str(e):
            print(f"Failed to create user {username}: A user with that username or email already exists.")
            # Depending on context, you might log this, return None, or raise a custom exception
        else:
            print(f"An unexpected database integrity error occurred: {e}")
            # Re-raise for unknown integrity errors
        return None

# Attempt to create a user that might already exist
create_user_robust("testuser", "test@example.com", "password123")
```

## Environment-Specific Notes

The impact and troubleshooting steps for this `IntegrityError` can vary slightly based on your environment.

*   **Local Development:** This is the easiest place to fix such issues. If you're prototyping and data isn't critical, you might just drop your database and run `makemigrations`/`migrate` again, then re-seed it. For more persistent issues, you'll still follow the steps above, but with direct access to your local database (e.g., via `sqlite3` CLI, `psql`, or a GUI tool). Debugging is usually straightforward as you control everything.

*   **Docker Containers:** If your database is ephemeral (i.e., not using persistent volumes), restarting your Docker containers will wipe the database, effectively clearing any conflicting data and allowing a fresh start. If your Docker setup uses persistent volumes for the database, then it behaves more like a production environment. You'll need to treat the database as persistent and apply fixes carefully, exactly as you would for a remote server. My approach here is usually to get a shell into the Django container (`docker exec -it <container_id> bash`) and then run `python manage.py dbshell` or `python manage.py shell` to inspect the data directly.

*   **Production (Cloud/Servers):** This is where these errors are most critical.
    *   **Logging is Key:** Ensure your production environment has robust logging (e.g., Sentry, AWS CloudWatch, Google Cloud Logging, ELK stack). The `IntegrityError` message, especially the full database detail, is crucial for debugging. I always ensure these details are captured.
    *   **Non-Destructive Fixes:** You cannot simply drop the database. Any data cleanup or alteration must be done with extreme caution, preferably through a Django management command that can be reviewed and run with specific permissions, and *always* after ensuring you have recent backups.
    *   **Rollback Strategy:** Understand what happens if your fix introduces new problems. Having a clear rollback plan is essential.
    *   **Monitoring:** After deploying a fix, monitor your error logs closely to ensure the `IntegrityError` count goes down and stays down.

## Frequently Asked Questions

*   **Q: Can I just disable unique constraints?**
    *   **A:** No, almost never. Unique constraints are fundamental to maintaining data integrity in your database. Disabling them would likely lead to inconsistent and unreliable data, creating far more problems than it solves down the line. If your business logic requires uniqueness, let the database enforce it.

*   **Q: Why does this happen even with auto-incrementing IDs?**
    *   **A:** While the `id` field (which is usually your primary key) auto-increments and handles its own uniqueness, this error typically refers to *other* fields in your model where you've explicitly set `unique=True` (e.g., `email`, `username`, `slug`). It can also happen with `id` if you manually try to set an ID that already exists, or if your database's sequence generator somehow gets out of sync (rare but possible after manual database operations or restores).

*   **Q: Is `get_or_create()` always the best solution?**
    *   **A:** `get_or_create()` is excellent for many scenarios where you want to ensure an object exists, creating it if it doesn't. It's often atomic and handles common race conditions well. However, for very high-concurrency situations, there can still be edge cases where two transactions attempt to create simultaneously, and both perform the `get` part before either does the `create`. Django mitigates this with retries, but it's good to be aware. For most applications, it's robust enough.

*   **Q: How do I find *which* unique constraint is being violated?**
    *   **A:** The full error message and traceback are your best friends. For PostgreSQL, the `IntegrityError` detail explicitly states the key and value, e.g., `Key (email)=(example@example.com) already exists.`. For other databases, the message might vary but typically points to the index or column involved. Reviewing your `models.py` for `unique=True` and `unique_together` on the relevant model is also critical.

*   **Q: What if I have existing duplicate data from before I added the `unique=True` constraint?**
    *   **A:** If you're trying to add a unique constraint via a migration and your database already contains duplicates, the migration will fail. You must clean up the existing duplicate data first. This usually involves:
        1.  Identifying all duplicate records (e.g., `SELECT email, COUNT(*) FROM myapp_user GROUP BY email HAVING COUNT(*) > 1;`).
        2.  Deciding which record to keep (the oldest, the one with more data, etc.) and deleting or merging the others.
        3.  Writing a one-off Django management command or direct SQL script to perform this cleanup.
        4.  Once cleaned, run your `makemigrations` and `migrate` again.

## Related Errors