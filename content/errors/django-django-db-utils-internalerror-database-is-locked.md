# django.db.utils.InternalError: database is locked
> Encountering `django.db.utils.InternalError: database is locked` means your SQLite database is likely being accessed concurrently; this guide explains how to fix it.

## What This Error Means

This error, `django.db.utils.InternalError: database is locked`, is a strong indicator that your Django application, running on a SQLite database, is experiencing concurrency issues. Specifically, it means that one process or thread is trying to write to the SQLite database file while another process or thread already holds a write lock on it. SQLite, being a file-based database, uses file-level locking to manage concurrent access. When this lock cannot be acquired within a default timeout period (typically 5 seconds), this `InternalError` is raised.

## Why It Happens

The fundamental reason this error occurs lies in SQLite's design. Unlike client-server databases like PostgreSQL or MySQL, SQLite is an embedded database. It operates directly on a single file on the filesystem. To maintain data integrity, SQLite implements a strict locking mechanism: only one writer can operate on the database at a time. Multiple readers are generally allowed concurrently, but as soon as a write operation begins, an exclusive lock is obtained. If another process attempts to write during this period, it will fail with the "database is locked" error after its internal timeout.

In my experience, this is almost exclusively seen with SQLite, rarely with other production-grade databases because they handle concurrency at a much finer granularity (row-level or page-level locking) and are designed for multi-client access.

## Common Causes

Several common scenarios lead to the `database is locked` error in a Django application:

1.  **Concurrent Web Requests:** If your Django application receives multiple web requests simultaneously, and two or more of them attempt to write to the SQLite database, you're likely to hit this. This is especially true if requests involve complex or long-running transactions.
2.  **Long-Running Transactions:** A transaction that holds a write lock for an extended period, perhaps due to inefficient queries, large data operations, or external API calls within the transaction, will block other writers.
3.  **Background Tasks (Celery, Cron Jobs):** If you're running background tasks (e.g., with Celery, Django Q, or simple cron scripts) that interact with the database, and these tasks overlap with active web requests or other background tasks, they can contend for the SQLite lock.
4.  **Django Test Suite:** Running a large number of Django tests, especially if they use transactional test cases, can lead to lock contention as tests parallelize or run very quickly, creating many short-lived connections and write attempts.
5.  **Misconfigured ORM Operations:** Not explicitly closing connections or performing many small, unoptimized writes can exacerbate contention. While Django generally manages connections well, edge cases exist.
6.  **Multiple `runserver` instances:** Accidentally running `python manage.py runserver` multiple times in separate terminal windows, all pointing to the same SQLite database file, will almost certainly cause this.

## Step-by-Step Fix

Addressing the `database is locked` error often involves a combination of strategies, ranging from application-level optimizations to considering a different database backend.

1.  **Identify the Source of Contention:**
    *   **Check application logs:** Look for stack traces around the `InternalError` to pinpoint which specific views, tasks, or functions are involved.
    *   **Monitor database access:** While harder with SQLite, observing access patterns can help. If you're running on a server, `lsof | grep your_db.sqlite3` might show processes holding open file handles.
    *   **Replicate the issue:** Can you consistently trigger the error with specific request patterns or task combinations?

2.  **Optimize Database Transactions and Queries:**
    *   **Keep transactions short:** Ensure your `transaction.atomic()` blocks are as lean as possible. Move non-database operations (e.g., sending emails, calling external APIs) *outside* the atomic block.
        ```python
        from django.db import transaction

        def process_order(order_id):
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=order_id)
                order.status = 'processing'
                order.save()
                # Simulate some database-heavy work
                # This part should be fast!

            # Send email AFTER the transaction commits
            # This prevents holding the lock while waiting for external services
            send_order_confirmation_email(order)
        ```
    *   **Use `select_for_update()` cautiously:** This explicitly locks selected rows until the transaction commits. While powerful for preventing race conditions, overuse or long-held locks can increase contention. Only use it when you absolutely need to prevent concurrent modifications to specific rows.
    *   **Batch operations:** Instead of many individual `save()` calls within a loop, use `bulk_create()` or `bulk_update()` when appropriate.

3.  **Implement Retry Mechanisms:**
    *   For background tasks or less critical operations, a simple retry decorator can sometimes alleviate transient lock issues. If the first attempt fails, wait a short period and try again.
        ```python
        import time
        from django.db import InternalError

        def retry_on_lock(func, max_retries=3, delay=0.5):
            def wrapper(*args, **kwargs):
                for i in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except InternalError as e:
                        if "database is locked" in str(e):
                            print(f"Database locked, retrying in {delay}s... (Attempt {i+1}/{max_retries})")
                            time.sleep(delay)
                            delay *= 2 # Exponential backoff
                        else:
                            raise
                raise InternalError(f"Failed after {max_retries} retries: database is locked")
            return wrapper

        @retry_on_lock
        def update_user_profile(user_id, new_data):
            # Database write operation
            pass
        ```
        *Self-correction:* While a retry mechanism can mask the problem, it's not a root cause fix. It should be used for *transient* issues, not as a permanent solution if contention is frequent.

4.  **Review Django Settings:**
    *   **`ATOMIC_REQUESTS = True`:** If you have `ATOMIC_REQUESTS = True` in your `DATABASES` settings, every web request is wrapped in a transaction. While good for atomicity, if your request handlers perform long operations, they can hold the SQLite lock for longer. Consider if this setting is strictly necessary for *all* views, or if `transaction.atomic()` on specific views is sufficient.

5.  **Enable WAL Mode (SQLite 3.7.0+):**
    *   Write-Ahead Logging (WAL) mode allows readers and writers to operate concurrently without locking the entire database file. It dramatically improves concurrency for SQLite. To enable it, you typically add `?mode=wal` to your database name in `settings.py`.
        ```python
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3' + '?mode=wal', # Enable WAL mode
            }
        }
        ```
        *Caveat:* WAL mode doesn't eliminate the *single writer* constraint, but it significantly reduces the window for writer blocking, as readers don't block writers. It's often the first practical step for improving SQLite concurrency.

6.  **Upgrade Your Database (The Recommended Solution for Production):**
    *   **For any production environment with even moderate concurrency, SQLite is simply not the right choice.** This is the most direct and robust fix. Switch to a robust client-server database like PostgreSQL or MySQL. These databases are designed from the ground up to handle high concurrency, offering features like multi-version concurrency control (MVCC), row-level locking, and connection pooling.
    *   In my experience, almost every `database is locked` error in a production environment eventually leads to this recommendation. It's a sign that your application has outgrown SQLite's capabilities.

## Code Examples

### Using `select_for_update` for explicit locking

```python
from django.db import transaction
from myapp.models import Product

def decrease_stock(product_id, quantity):
    try:
        with transaction.atomic():
            # Locks the selected product row until the transaction commits
            product = Product.objects.select_for_update().get(id=product_id)
            if product.stock >= quantity:
                product.stock -= quantity
                product.save()
                print(f"Stock for {product.name} decreased by {quantity}.")
            else:
                print(f"Insufficient stock for {product.name}.")
    except Exception as e:
        print(f"Error processing stock update: {e}")
```

### Ensuring atomicity with `@transaction.atomic`

```python
from django.db import transaction
from django.shortcuts import render
from myapp.models import Order, OrderItem

# This view performs multiple database operations that should succeed or fail together
@transaction.atomic
def place_order(request):
    if request.method == 'POST':
        # Assume form data contains product_id and quantity
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity'))

        order = Order.objects.create(user=request.user, total_amount=0)
        product = Product.objects.get(id=product_id)
        
        # This will fail if product.stock < quantity, rolling back the Order creation
        if product.stock < quantity:
            raise ValueError("Insufficient stock!") 

        OrderItem.objects.create(order=order, product=product, quantity=quantity)
        product.stock -= quantity
        product.save()
        
        order.total_amount = product.price * quantity
        order.save()
        
        return render(request, 'order_success.html', {'order': order})
    return render(request, 'place_order.html')
```

## Environment-Specific Notes

The `database is locked` error manifests differently and has varying implications depending on your deployment environment.

*   **Local Development (e.g., `runserver`):** This is where you'll most frequently encounter the error with SQLite. It's common when running multiple `runserver` instances, or a `runserver` alongside a background worker (like Celery development server) that both access the same `db.sqlite3` file. Using `python manage.py runserver --noreload` can sometimes help rule out auto-reloader issues if you suspect them, but it's usually just basic contention. Enabling WAL mode in `settings.py` is highly recommended for local development with SQLite.
*   **Docker:** If you're running multiple Django application containers, or multiple services within Docker Compose (e.g., Django app and a Celery worker), and they *all* mount the same host directory containing your `db.sqlite3` file, you will definitely hit this error. Each container is a separate process that will contend for the file lock. The solution here is the same as for production: don't use SQLite for shared state in Docker beyond simple local dev, or switch to a proper database service (PostgreSQL, MySQL).
*   **Cloud Deployments (AWS EC2, GCP Compute Engine, etc.):** If you've deployed Django on an EC2 instance or similar cloud VM and are using SQLite, you're in a highly precarious situation. Cloud environments often imply scaling (multiple instances, load balancers), which fundamentally conflicts with SQLite's single-writer model. Even on a single instance, if you have multiple WSGI worker processes (e.g., Gunicorn workers), they are distinct processes and will contend for the lock. **Never use SQLite in production cloud deployments.** Provision a managed database service like AWS RDS (PostgreSQL/MySQL) or Google Cloud SQL.

## Frequently Asked Questions

**Q: Can I use SQLite for a production Django application?**
A: Generally, no. While SQLite is robust, it's designed for embedded use and single-writer scenarios. Any application with multiple concurrent users or background tasks will quickly run into `database is locked` errors and performance bottlenecks. Use client-server databases like PostgreSQL or MySQL for production.

**Q: How does `ATOMIC_REQUESTS` relate to this error?**
A: When `ATOMIC_REQUESTS = True` is set in your `DATABASES` configuration, every web request is wrapped in a database transaction. While this ensures data integrity for the request, if your request handlers perform long-running operations or external calls, they will hold the database lock (in SQLite's case) for the entire duration of the request, increasing the likelihood of contention.

**Q: Does Django's SQLite backend use a connection pool?**
A: No, not in the traditional sense of a connection pool like you'd find with PostgreSQL or MySQL. SQLite is file-based; each "connection" is more about opening the database file. Connection pooling primarily benefits client-server architectures by reusing network connections and authentication. SQLite's performance is bottlenecked by its file-locking mechanism, not connection overhead in the same way.

**Q: What is WAL mode, and how much does it help?**
A: WAL (Write-Ahead Logging) mode is a significant improvement for SQLite concurrency. It allows concurrent readers to continue operating while a writer is active, without blocking them. However, it still maintains the single-writer constraint. It's an excellent optimization for local development and specific low-concurrency scenarios, but it doesn't eliminate the fundamental limitations of SQLite for high-concurrency production use.

**Q: I'm seeing this error during my test suite. How do I fix it?**
A: This can happen if your test setup causes multiple test runners or processes to hit the database simultaneously. Ensure your test runner isn't accidentally configured for parallel execution in a way that conflicts with SQLite. Sometimes, disabling transaction management for specific problematic tests or using `TransactionTestCase` carefully can help. However, often it's just a side effect of SQLite's limitations being exposed by rapid, concurrent test execution. It often resolves itself when you switch to a PostgreSQL/MySQL test database.

## Related Errors
*(none)*