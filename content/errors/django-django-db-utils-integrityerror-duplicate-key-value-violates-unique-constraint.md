# django.db.utils.IntegrityError: duplicate key value violates unique constraint
> Encountering django.db.utils.IntegrityError: duplicate key value violates unique constraint means your database rejected an insert or update due to a pre-existing record; this guide explains how to fix it.

As a Staff Engineer, I've seen this `IntegrityError` pop up in various Django projects, from small internal tools to large-scale production applications. It's a clear signal from your database that you're trying to do something that violates its rules, specifically a uniqueness constraint. This isn't just a Django error; it's a database error that Django's ORM translates for you. Understanding and resolving it requires looking at both your application code and your database schema.

## What This Error Means

At its core, `django.db.utils.IntegrityError: duplicate key value violates unique constraint` means that your Django application attempted to insert or update a record in the database, but the values provided for one or more fields conflicted with an existing record, violating a uniqueness rule defined on your database table.

Databases enforce integrity constraints to ensure data quality and consistency. A "unique constraint" is one such rule, declaring that a specific column or combination of columns must contain unique values across all rows in a table. When you try to save data that breaks this rule, the database rejects the operation, and Django catches this database error, raising an `IntegrityError`.

Common databases will return slightly different messages, but the meaning is the same:
*   **PostgreSQL:** `duplicate key value violates unique constraint "table_field_key"`
*   **MySQL:** `Duplicate entry 'value' for key 'field'`
*   **SQLite:** `UNIQUE constraint failed: table.field`

## Why It Happens

This error occurs because your Django model, either explicitly or implicitly, has a unique constraint defined, and your code is attempting to save data that already exists according to that constraint. Django's ORM is just the messenger here; the problem originates from the database itself.

In Django, unique constraints are typically defined in one of two ways:

1.  **`unique=True` on a model field:** This is the most common way. For example, `email = models.EmailField(unique=True)`. This ensures no two users can have the same email address.
2.  **`UniqueConstraint` in a model's `Meta` options:** This allows you to define uniqueness across a combination of fields. For instance, `UniqueConstraint(fields=['product', 'user'], name='unique_product_for_user')` would ensure a user can only have one review for a specific product.

When your code tries to `save()` a new instance or `update()` an existing one with values that clash with these definitions, the database throws the error, and Django converts it into the `IntegrityError` you see. I've often seen this occur due to race conditions or inadequate validation logic.

## Common Causes

Based on my experience, these are the most common scenarios leading to a `duplicate key value violates unique constraint` error:

*   **Attempting to create a record with an existing unique value:** This is the primary cause. For example, registering a new user with an email address that's already in use, or creating a product slug that already exists.
    ```python
    # models.py
    class Article(models.Model):
        slug = models.SlugField(unique=True)

    # In your code
    Article.objects.create(slug='my-first-article')
    Article.objects.create(slug='my-first-article') # <-- This will cause the error
    ```
*   **Race Conditions:** This is a trickier one to diagnose. Two concurrent requests try to create the *same* unique record almost simultaneously. The first request succeeds and commits the data. The second request, after checking for uniqueness (and finding nothing *before* the first committed), proceeds to create the record, but now finds a conflict and fails. I've seen this in production when multiple users or background tasks hit the same creation endpoint at once.
*   **Data Migration / Seeding Issues:** When importing data from an external source or seeding your database with initial data, you might accidentally include duplicate values for fields that are meant to be unique.
*   **Manual Primary Key Assignment:** While less common with Django's auto-incrementing `AutoField` (which is the default for `id`), if you're manually assigning primary keys (e.g., using a `UUIDField` or `SlugField` as a primary key), you might try to assign a key that already exists.
*   **Incorrect `get_or_create()` usage:** While `get_or_create()` is designed to *prevent* this error, if its `defaults` or `create_kwargs` contain values that violate other unique constraints, it can still fail.
*   **Third-Party Integrations:** Sometimes, external systems send duplicate data, and your application code attempts to persist it directly without proper checks, leading to the integrity error.

## Step-by-Step Fix

Resolving this error involves a systematic approach, from identifying the source to implementing a robust solution.

### Step 1: Identify the Specific Constraint and Field

The error message usually gives you a strong hint. Look for something like `(field_name)` or `(table_name_field_name_key)`.
For example, `duplicate key value violates unique constraint "myapp_user_email_key"` tells you the `email` field on the `myapp_user` table is the culprit.

### Step 2: Check Your Django Model Definition

Open `models.py` for the model mentioned in the error. Look for:
*   `unique=True` on any `Field` definition.
*   `UniqueConstraint` in the `Meta` class.

This confirms *what* constraint the database is enforcing.

```python
# myapp/models.py
class UserProfile(models.Model):
    username = models.CharField(max_length=150, unique=True) # Likely culprit
    email = models.EmailField(unique=True) # Another common one
    # ... other fields

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['first_name', 'last_name'], name='unique_fullname') # Or this one
        ]
```

### Step 3: Inspect Existing Database Data

Use the Django shell or a direct SQL client to query your database for existing data that might be causing the conflict.

```bash
python manage.py shell
```
```python
# In Django shell
from myapp.models import UserProfile

# If the error was 'duplicate key value violates unique constraint "myapp_userprofile_username_key"'
# And you tried to create a user with username 'johndoe'
UserProfile.objects.filter(username='johndoe').exists()
# This should return True if the record already exists.

# If it was a UniqueConstraint on multiple fields (e.g., first_name, last_name)
UserProfile.objects.filter(first_name='John', last_name='Doe').exists()
```

If the query returns `True`, you've confirmed an existing record is the source of the conflict.

### Step 4: Understand the Source of the Duplicate

*   **Is it legitimate?** Is the data you're trying to save *supposed* to be unique? (e.g., a user's email). If so, your application logic needs to prevent duplicates.
*   **Is it a data error?** Was a duplicate inserted incorrectly at some point?
*   **Is it a race condition?** If it's intermittent and happens under heavy load, it's likely a race condition.

### Step 5: Implement the Solution

Depending on the cause, here are the common fixes:

#### a. Prevent Duplicates (Most Common & Recommended)

*   **`get_or_create()`:** If your intention is to retrieve an object if it exists, or create it if it doesn't, `get_or_create()` is your friend. It's atomic and handles race conditions for creation fairly well.

    ```python
    # Instead of:
    # try:
    #     obj = MyModel.objects.get(unique_field=value)
    # except MyModel.DoesNotExist:
    #     obj = MyModel.objects.create(unique_field=value, other_field='data')

    # Use:
    obj, created = MyModel.objects.get_or_create(
        unique_field=value,
        defaults={'other_field': 'data'} # These are used ONLY if a new object is created
    )
    if created:
        print("Object was created.")
    else:
        print("Object already existed.")
    ```

*   **Form/Serializer Validation:** For user input, validate *before* attempting to save to the database. Django Forms and Django REST Framework serializers have built-in unique validation that can catch this early.

    ```python
    # forms.py
    from django import forms
    from .models import UserProfile

    class UserProfileForm(forms.ModelForm):
        class Meta:
            model = UserProfile
            fields = ['username', 'email']

        def clean_username(self):
            username = self.cleaned_data['username']
            if UserProfile.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken.")
            return username

    # Or even better, let ModelForm handle unique validation by default for unique=True fields
    ```

*   **Transactional Locks (`select_for_update`):** For complex logic or when dealing with race conditions, `select_for_update()` can lock rows, preventing other transactions from modifying them until your transaction completes. This is particularly useful when checking for existence and then creating/updating.

    ```python
    from django.db import transaction

    with transaction.atomic():
        try:
            # Lock potentially conflicting rows (e.g., if you were to update instead of create)
            # or simply rely on atomic block for creation
            existing_obj = MyModel.objects.select_for_update().get(unique_field=value)
            # If it exists, process existing_obj
            print("Object already existed:", existing_obj)
        except MyModel.DoesNotExist:
            # If it doesn't exist, create it within the same atomic block
            new_obj = MyModel.objects.create(unique_field=value, other_field='data')
            print("Object created:", new_obj)
    ```

#### b. Handle Gracefully with `try...except` (Use with Caution)

You can wrap the `save()` or `create()` call in a `try...except IntegrityError` block. While possible, I generally advise *against* this as a primary solution for unique constraints unless you have a very specific reason (e.g., logging and ignoring expected, but non-critical, duplicates from an external system). It's usually better to prevent the error than to catch it.

```python
from django.db.utils import IntegrityError

try:
    MyModel.objects.create(unique_field='value', other_field='data')
except IntegrityError:
    print("Warning: Attempted to create a duplicate record.")
    # Log the error, maybe retrieve the existing object, or skip the operation
    pass
```

#### c. Clean Up Existing Data (If Data is Corrupt)

If your database contains truly duplicate data that shouldn't be there, you might need to clean it up. **Always back up your database before performing manual data deletions or modifications, especially in production.**

```bash
python manage.py shell
```
```python
# In Django shell
from myapp.models import MyModel
from django.db.models import Count

# Find duplicates for a specific field (e.g., 'slug')
duplicates = MyModel.objects.values('slug').annotate(count=Count('id')).filter(count__gt=1)

for duplicate in duplicates:
    print(f"Duplicate slug '{duplicate['slug']}' found {duplicate['count']} times.")
    # Fetch all instances with that slug
    items_to_delete = MyModel.objects.filter(slug=duplicate['slug']).order_by('id')[1:]
    # Delete all but the first (keeping the oldest)
    for item in items_to_delete:
        print(f"Deleting duplicate ID: {item.id}")
        item.delete()

# For UniqueConstraint on multiple fields (e.g., product, user)
# Find duplicates based on product and user
duplicates_multi = MyModel.objects.values('product', 'user').annotate(count=Count('id')).filter(count__gt=1)
for duplicate in duplicates_multi:
    print(f"Duplicate (product={duplicate['product']}, user={duplicate['user']}) found {duplicate['count']} times.")
    items_to_delete = MyModel.objects.filter(product=duplicate['product'], user=duplicate['user']).order_by('id')[1:]
    for item in items_to_delete:
        print(f"Deleting duplicate ID: {item.id}")
        item.delete()
```

## Code Examples

Here are some concise, copy-paste ready examples illustrating the problem and common solutions.

### Example 1: Basic `unique=True` Field Violation

```python
# myapp/models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

# Scenario: Trying to create two products with the same name
# This will raise django.db.utils.IntegrityError
# Product.objects.create(name="Awesome Gadget", description="A super cool device.")
# Product.objects.create(name="Awesome Gadget", description="Another description.")

# Solution: Using get_or_create
from django.db.utils import IntegrityError

product_name = "Awesome Gadget"
product_description = "A super cool device."

try:
    product, created = Product.objects.get_or_create(
        name=product_name,
        defaults={'description': product_description}
    )
    if created:
        print(f"Product '{product_name}' created successfully.")
    else:
        print(f"Product '{product_name}' already exists. Retrieved existing object.")
        # You might want to update the existing object here if necessary
        # product.description = product_description
        # product.save()
except IntegrityError as e:
    print(f"An unexpected integrity error occurred: {e}") # This handles other potential integrity errors
```

### Example 2: `UniqueConstraint` in `Meta` Violation

```python
# myapp/models.py
from django.db import models

class UserReview(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_user_product_review')
        ]

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

# Scenario: Trying to create two reviews for the same user and product
from django.contrib.auth.models import User

# user = User.objects.first() # Assume a user exists
# product = Product.objects.first() # Assume a product exists

# This will raise django.db.utils.IntegrityError on the second creation
# UserReview.objects.create(user=user, product=product, rating=5)
# UserReview.objects.create(user=user, product=product, rating=4)

# Solution: Check existence before creation (often with get_or_create or form validation)
def create_or_update_review(user_obj, product_obj, new_rating):
    review, created = UserReview.objects.get_or_create(
        user=user_obj,
        product=product_obj,
        defaults={'rating': new_rating}
    )
    if not created:
        print("User already reviewed this product. Updating existing review.")
        review.rating = new_rating
        review.save()
    else:
        print("New review created successfully.")
    return review

# Example usage (assuming user and product objects are available)
# review = create_or_update_review(user, product, 5)
# review_updated = create_or_update_review(user, product, 4)
```

## Environment-Specific Notes

The approach to handling `IntegrityError` can vary slightly based on your deployment environment.

*   **Local Development:** This is where you'll most frequently encounter and debug this error. It's relatively low-stakes. If data gets corrupted, you can often `python manage.py flush` (which deletes all data) or `rm db.sqlite3` (for SQLite) and re-run migrations and seed data. The key is to fix your application logic so the error doesn't reach production.
*   **Docker:** Similar to local development. If your database is running in a Docker container, `docker-compose down -v` will often delete the associated volumes, effectively clearing your database data. If you have persistent volumes configured, remember that data will survive container restarts. For debugging, you can `docker exec -it <db-container-id> bash` to access the database command line.
*   **Cloud (AWS RDS, Google Cloud SQL, Azure Database):** This is where `IntegrityError` in production is most critical.
    *   **Data Integrity:** You absolutely cannot afford to lose production data. Any manual data cleanup must be preceded by robust backups.
    *   **Monitoring:** Set up monitoring and alerting for `IntegrityError` occurrences in your application logs. This helps catch race conditions or new bugs quickly.
    *   **Race Conditions:** Cloud environments with load balancers and auto-scaling groups mean multiple application instances can hit the database simultaneously, increasing the likelihood of race conditions. Solutions like `select_for_update` or robust idempotency become even more important.
    *   **Debugging:** Accessing the database directly requires proper IAM roles and careful security considerations. Use read replicas for investigations if possible to avoid impacting primary database performance.

## Frequently Asked Questions

**Q: Can I just delete the duplicate record?**
**A:** You *can*, but it's crucial to understand *why* the duplicate was created in the first place. If you delete it without fixing the underlying application logic (e.g., missing validation, race condition), the error will likely reappear. Only delete duplicates if you've determined they are truly erroneous data and you have a plan to prevent future occurrences. Always back up your database before deletion.

**Q: How do I find which constraint is causing the error if the message isn't clear?**
**A:** The error message from Django's `IntegrityError` typically includes the constraint name (e.g., `myapp_modelname_fieldname_key` or `unique_constraint_name`). If it's still unclear, examine your `models.py` for any `unique=True` fields or `UniqueConstraint` definitions. You can also inspect your database schema directly (e.g., `\d your_table_name` in PostgreSQL's psql client, or `SHOW CREATE TABLE your_table_name;` in MySQL).

**Q: Is `try...except IntegrityError` a good solution?**
**A:** Generally, no, not for unique constraint violations. It's often better to *prevent* the error from happening in the first place through proper validation (`ModelForm`, DRF serializers) or by using atomic operations like `get_or_create()`. Catching the `IntegrityError` should be reserved for very specific scenarios where you genuinely want to handle an *already existing* duplicate as an acceptable condition (e.g., idempotent operations) rather than letting the creation fail. If you catch it, make sure you know what action to take (e.g., retrieve the existing object, log and ignore).

**Q: How do race conditions cause this?**
**A:** Imagine two users simultaneously try to register with the same email address. Both requests hit your application.
1.  **Request A:** Checks if email exists -> No. Attempts to create user.
2.  **Request B:** Checks if email exists -> No (because A hasn't committed yet). Attempts to create user.
3.  **Request A:** Successfully creates user and commits transaction.
4.  **Request B:** Attempts to create user, but the unique email now exists from Request A. The database rejects this, throwing `IntegrityError`.
`select_for_update()` within an atomic transaction is one way to mitigate this by ensuring only one transaction can proceed with checking and creating a unique record at a time.

## Related Errors