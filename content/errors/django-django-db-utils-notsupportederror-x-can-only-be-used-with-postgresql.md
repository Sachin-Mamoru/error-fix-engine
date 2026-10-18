# django.db.utils.NotSupportedError: X can only be used with PostgreSQL.
> Encountering django.db.utils.NotSupportedError: X can only be used with PostgreSQL means you're leveraging a PostgreSQL-specific feature with an incompatible database backend; this guide explains how to resolve it.

## What This Error Means

This error, `django.db.utils.NotSupportedError: X can only be used with PostgreSQL.`, is a clear indicator of a database incompatibility within your Django application. At its core, it means you are attempting to use a feature, represented by "X" in the error message (e.g., `JSONField`, `ArrayField`, specific database functions, or lookups), that is exclusively supported by PostgreSQL, while your current Django project is configured to use a different database backend, such as SQLite, MySQL, or Oracle.

Django's Object-Relational Mapper (ORM) provides a powerful abstraction layer, allowing developers to interact with various database systems using a unified Python API. However, this abstraction has limits. Advanced, database-specific features, particularly those found in PostgreSQL's rich data type and function set, cannot be universally replicated across all database backends. When Django detects that you're trying to use one of these PostgreSQL-specific features without a PostgreSQL database connected, it raises this `NotSupportedError` to prevent unexpected behavior and data loss.

## Why It Happens

The reason this error occurs boils down to the fundamental differences in capabilities between database systems. PostgreSQL is known for its advanced features, including native support for data types like JSON, arrays, and HStore, as well as powerful text search and geospatial functions. To expose these capabilities to Django developers, the `django.contrib.postgres` module was created. This module extends Django's ORM with specific fields (`JSONField`, `ArrayField`, `HStoreField`) and database functions/lookups that leverage PostgreSQL's native strengths.

When you incorporate these features into your Django models or queries, the ORM generates SQL tailored for PostgreSQL. If your `settings.py` specifies a different database engine (e.g., `django.db.backends.sqlite3` or `django.db.backends.mysql`), the underlying database driver simply won't understand or support the PostgreSQL-specific SQL syntax or data types. Django's ORM catches this mismatch at runtime, raising the `NotSupportedError`.

I've seen this most frequently in scenarios where:
1.  A developer uses SQLite for local development (which is common and convenient) but tries to implement a feature that relies on `JSONField` or `ArrayField`, which are intended for a PostgreSQL production environment.
2.  A project is migrated or cloned, and the database configuration isn't updated to match the original database type, leading to feature requests from the ORM that the current backend can't fulfill.

## Common Causes

Identifying the "X" in the error message is crucial for troubleshooting. Here are the most common causes I've encountered:

*   **Using `JSONField` with a non-PostgreSQL database:** Django's `models.JSONField` (introduced in Django 3.1) is specifically designed to work with PostgreSQL's native JSONB type. If you use it with SQLite or MySQL, this error will occur. (Note: Older Django versions had `jsonfield` via `django.contrib.postgres`, which is also PostgreSQL-specific).
*   **Using `ArrayField` with a non-PostgreSQL database:** Similarly, `models.ArrayField` (from `django.contrib.postgres`) relies on PostgreSQL's array capabilities. Attempting to use it elsewhere triggers the error.
*   **Using `HStoreField` (older feature) with a non-PostgreSQL database:** `HStoreField` (also from `django.contrib.postgres`) maps to PostgreSQL's hstore extension.
*   **Leveraging `django.contrib.postgres` specific lookups or functions:** The `django.contrib.postgres.fields` and `django.contrib.postgres.search` modules provide powerful additions like `SearchVector`, `TrigramSimilarity`, `Unaccent`, and various field lookups (e.g., `__contains` for arrays) that are all PostgreSQL-dependent. Using these in queries will cause the error if your backend isn't PostgreSQL.
*   **`django.contrib.postgres` in `INSTALLED_APPS` without PostgreSQL:** Sometimes, developers add `django.contrib.postgres` to `INSTALLED_APPS` anticipating future use, or it's part of a project template. If no PostgreSQL-specific features are actively used but the module is imported, it might still attempt to register PostgreSQL-specific functions or types during startup, leading to this error if your database backend is incompatible.
*   **Local development setup mismatch:** A common scenario: your production environment uses PostgreSQL, but your local development machine is set up with SQLite for simplicity. When you pull down changes that include PostgreSQL-specific models or queries, your local environment breaks.

## Step-by-Step Fix

Addressing this error requires either aligning your database backend with the code's requirements or refactoring your code to be more database-agnostic.

### Step 1: Identify the problematic 'X' and its source

Examine the full traceback. The "X" in `X can only be used with PostgreSQL` will tell you exactly which feature is causing the problem. Look for `JSONField`, `ArrayField`, `HStoreField`, or specific functions from `django.contrib.postgres`.

**Example Error Message Snippet:**
```
django.db.utils.NotSupportedError: JSONField can only be used with PostgreSQL.
```
This clearly points to `JSONField`.

Once identified, search your project for where `X` is being used (e.g., in your `models.py` or querysets).

### Step 2: Decide on your database strategy

You have two primary paths to resolution:

#### Option A: Switch to PostgreSQL (Recommended if 'X' is critical)

If the PostgreSQL-specific feature (`JSONField`, `ArrayField`, etc.) is central to your application's design, the most straightforward and often correct solution is to switch your database backend to PostgreSQL.

1.  **Install the PostgreSQL database driver:**
    You'll need `psycopg2-binary` to allow Django to communicate with PostgreSQL.

    ```bash
    pip install psycopg2-binary
    ```

2.  **Configure PostgreSQL:**
    Ensure you have a PostgreSQL server running and accessible. Create a database for your project.

3.  **Update `settings.py`:**
    Modify your `DATABASES` setting to point to your PostgreSQL instance.

    ```python
    # myproject/settings.py

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'mydjangoappdb', # Your database name
            'USER': 'mydjangoappuser', # Your database user
            'PASSWORD': 'your_db_password', # Your database password
            'HOST': 'localhost', # Or your PostgreSQL host (e.g., 'db' for Docker)
            'PORT': '5432',
        }
    }

    # Ensure django.contrib.postgres is in INSTALLED_APPS if you're using its features
    INSTALLED_APPS = [
        # ...
        'django.contrib.postgres', # Add this line
        # ...
    ]
    ```

4.  **Run migrations:**
    After configuring the new database, apply your migrations. Note that if you're switching from an existing database with data, you'll need to migrate your data, which is beyond the scope of this article but typically involves data dumps and restores. For a fresh setup:

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

#### Option B: Refactor code for cross-database compatibility (If PostgreSQL is not an option)

If you cannot or choose not to use PostgreSQL (e.g., for simple local development with SQLite, or if your client mandate requires MySQL), you must refactor your code to remove the PostgreSQL-specific features.

1.  **Replace `JSONField`:**
    If you're using `JSONField`, replace it with a `TextField` and handle JSON serialization/deserialization manually in your Python code.

    ```python
    # Original (problematic)
    # from django.db import models
    # class MyModel(models.Model):
    #     data = models.JSONField(default=dict)

    # Refactored for cross-database compatibility
    import json
    from django.db import models

    class MyModel(models.Model):
        _data = models.TextField(db_column='data', default='{}') # Internal storage

        @property
        def data(self):
            return json.loads(self._data)

        @data.setter
        def data(self, value):
            self._data = json.dumps(value)

        def save(self, *args, **kwargs):
            # Ensure the property setter is called if data was modified directly
            # before saving, or if a new instance is being saved.
            if hasattr(self, '_data') and isinstance(self._data, dict): # if data was assigned as dict directly
                self._data = json.dumps(self._data)
            super().save(*args, **kwargs)

    ```
    This approach means you lose the database-level JSON query capabilities but gain compatibility.

2.  **Replace `ArrayField`:**
    For `ArrayField`, you can use a `TextField` and store the array elements as a comma-separated string, a JSON-encoded string, or pickling, depending on your needs. Storing as a JSON string is generally the most robust.

    ```python
    # Original (problematic)
    # from django.contrib.postgres.fields import ArrayField
    # from django.db import models
    # class MyItem(models.Model):
    #     tags = ArrayField(models.CharField(max_length=200), blank=True, default=list)

    # Refactored for cross-database compatibility
    import json
    from django.db import models

    class MyItem(models.Model):
        _tags = models.TextField(db_column='tags', default='[]') # Internal storage for JSON string

        @property
        def tags(self):
            return json.loads(self._tags)

        @tags.setter
        def tags(self, value):
            if not isinstance(value, list):
                raise ValueError("Tags must be a list.")
            self._tags = json.dumps(value)

        def save(self, *args, **kwargs):
            # Ensure the property setter is called if tags was modified directly
            if hasattr(self, '_tags') and isinstance(self._tags, list):
                self._tags = json.dumps(self._tags)
            super().save(*args, **kwargs)
    ```

3.  **Remove or conditionally add `django.contrib.postgres`:**
    If you're no longer using any PostgreSQL-specific features, consider removing `django.contrib.postgres` from your `INSTALLED_APPS`. If you need it for production but not for local development, you might use environment variables or a separate settings file to conditionally include it.

    ```python
    # myproject/settings.py

    INSTALLED_APPS = [
        # ...
        # 'django.contrib.postgres', # Comment out or remove if not using PG features
        # ...
    ]
    ```

4.  **Refactor PostgreSQL-specific queries:**
    If your error stems from a PostgreSQL-specific lookup (e.g., `__search`, `__trigram_similarity`), you'll need to rewrite that query using generic ORM methods or resort to raw SQL if equivalent functionality is needed in your target database.

### Step 3: Run migrations and test

After making changes to your models or database configuration, always run:

```bash
python manage.py makemigrations
python manage.py migrate
```

Thoroughly test your application to ensure that the refactored code works as expected and that all features are functional with your chosen database backend.

## Code Examples

Here are some concise, copy-paste ready examples of problematic code and their fixes.

**Problematic Model (PostgreSQL-specific `JSONField`)**
```python
# myapp/models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    # This will cause NotSupportedError with SQLite, MySQL, etc.
    details = models.JSONField(default=dict)

    def __str__(self):
        return self.name
```

**Fixing `JSONField` for Cross-Database Compatibility (e.g., SQLite)**
```python
# myapp/models.py
import json
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    # Store JSON as a string in a TextField
    _details = models.TextField(db_column='details', default='{}')

    @property
    def details(self):
        """Deserializes JSON string to Python dict on access."""
        return json.loads(self._details)

    @details.setter
    def details(self, value):
        """Serializes Python dict to JSON string on assignment."""
        if not isinstance(value, dict):
            raise ValueError("Details must be a dictionary.")
        self._details = json.dumps(value)

    def save(self, *args, **kwargs):
        # Ensure _details is a JSON string before saving if the property setter wasn't explicitly called
        if hasattr(self, '_details') and isinstance(self._details, dict):
            self._details = json.dumps(self._details)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
```

**Configuring `settings.py` for PostgreSQL**
```python
# myproject/settings.py

# ... other settings ...

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'my_database_name',
        'USER': 'my_db_user',
        'PASSWORD': 'my_db_password',
        'HOST': 'localhost', # or IP/hostname of your DB server
        'PORT': '5432',      # default PostgreSQL port
    }
}

INSTALLED_APPS = [
    # ... Django defaults ...
    'django.contrib.postgres', # Essential for using PostgreSQL-specific features
    # ... your apps ...
]
```

## Environment-Specific Notes

The `NotSupportedError` often highlights differences between development and production environments.

*   **Local Development:**
    It's incredibly common to use SQLite for local development due to its zero-configuration simplicity. However, if your production environment leverages PostgreSQL-specific features (like `JSONField`), this mismatch will lead to `NotSupportedError` locally.
    **Recommendation:** For projects using `django.contrib.postgres` features, I highly recommend using a local PostgreSQL instance (e.g., via Docker) for development to maintain consistency with production. This prevents environment-specific bugs and ensures features work as expected before deployment.

*   **Docker:**
    When deploying with Docker, ensure your `docker-compose.yml` or Kubernetes manifests correctly set up a PostgreSQL service and that your Django application container is configured to connect to it. Environment variables like `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_HOST` are critical. A common mistake is using a `Dockerfile` that works for SQLite, then deploying to Docker Compose with a `db` service for PostgreSQL without updating Django's `settings.py` or environment variables for the app.

    ```yaml
    # Example docker-compose.yml snippet
    services:
      db:
        image: postgres:13
        environment:
          POSTGRES_DB: mydjangoappdb
          POSTGRES_USER: mydjangoappuser
          POSTGRES_PASSWORD: my_db_password
        volumes:
          - postgres_data:/var/lib/postgresql/data/

      web:
        build: .
        command: python manage.py runserver 0.0.0.0:8000
        volumes:
          - .:/app
        ports:
          - "8000:8000"
        env_file:
          - .env.prod # Contains DJANGO_SETTINGS_MODULE and DB environment variables
        depends_on:
          - db
    ```
    Your `.env.prod` would then contain `DATABASE_URL` or individual `DB_NAME`, `DB_USER`, `DB_HOST` settings that override Django's default `DATABASES` for the `web` service.

*   **Cloud (AWS RDS, Heroku Postgres, Azure Database for PostgreSQL):**
    In cloud environments, you'll provision a managed PostgreSQL database service. The key here is correctly configuring your Django application to connect to this service. This typically involves setting database credentials (host, port, name, user, password) via environment variables or a configuration management system, which then populate your `DATABASES` setting. Always verify the connection string or individual parameters are correct for the cloud-hosted PostgreSQL instance.

## Frequently Asked Questions

**Q: Can I use `JSONField` with SQLite or MySQL in Django?**
**A:** No, Django's native `models.JSONField` (and the `JSONField` from `django.contrib.postgres`) are specifically designed to leverage PostgreSQL's native JSONB data type. Attempting to use them with other database backends will result in a `NotSupportedError`. For cross-database compatibility, you must manually serialize/deserialize JSON data using a `models.TextField`.

**Q: My code works in production but not on my local machine. Why?**
**A:** This is a classic symptom of the `NotSupportedError`. Your production environment almost certainly uses PostgreSQL, while your local development environment likely defaults to SQLite for convenience. The features you're using (e.g., `JSONField`, `ArrayField`) are compatible with PostgreSQL but not with SQLite. To fix this, either switch your local environment to PostgreSQL or refactor the code for cross-database compatibility.

**Q: Is there a way to make `django.contrib.postgres` features work with other database systems?**
**A:** No. The features provided by `django.contrib.postgres` are specifically implemented to utilize the unique capabilities of the PostgreSQL database. They do not have equivalents that can be seamlessly translated to other database systems. If you need these features, PostgreSQL is a requirement.

**Q: What if I absolutely need `ArrayField` but cannot use PostgreSQL?**
**A:** If you can't use PostgreSQL, you'll need to simulate `ArrayField` behavior. The most common approach is to store the array data as a JSON-encoded string within a `models.TextField`. You then use Python's `json.loads()` and `json.dumps()` to convert between Python lists and the string representation in the database. This shifts the array management logic from the database to your application code.

## Related Errors