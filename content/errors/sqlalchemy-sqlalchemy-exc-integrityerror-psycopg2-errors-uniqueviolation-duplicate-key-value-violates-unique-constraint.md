# sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint
> Encountering a duplicate key value violation in SQLAlchemy means you're trying to insert or update data that conflicts with a unique constraint; this guide explains how to identify and fix it.

## What This Error Means

When you encounter `sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint`, your application has attempted an operation that violates a core database principle: data integrity. Specifically, it means you tried to insert or update a row in your database, but the values you provided for one or more columns already exist in another row, and those columns are constrained to be unique.

SQLAlchemy acts as an ORM (Object-Relational Mapper) wrapper around the raw database driver (in this case, `psycopg2` for PostgreSQL). The `IntegrityError` is SQLAlchemy's way of telling you that the underlying database driver reported an integrity violation. The `psycopg2.errors.UniqueViolation` part pinpoints the exact type of integrity issue: a unique constraint has been violated. This typically occurs on columns designated as `UNIQUE` or on primary key columns, which are implicitly unique.

## Why It Happens

This error fundamentally happens because the state your application is trying to achieve in the database conflicts with the rules defined in the database schema. Databases enforce unique constraints to ensure data consistency and prevent ambiguous or duplicate records. When your application tries to write data that breaks these rules, the database rejects the transaction and `psycopg2` (and subsequently SQLAlchemy) raises an error.

In my experience, this often surfaces due to a few common scenarios:

1.  **Application Logic Flaw:** The most frequent cause is a bug in the application logic that doesn't account for existing data, leading it to try and insert a record that's already there (or has the same unique values).
2.  **Concurrency Issues:** Multiple users or processes attempt to create or update records with the same unique values simultaneously. Even if your application checks for existence first, a small window exists where another process can insert the data before your transaction commits, leading to a race condition.
3.  **Data Migration or Seeding Issues:** When importing data, especially from external sources, you might encounter duplicates if the source data isn't properly de-duplicated or if the migration script doesn't handle existing records gracefully.
4.  **Testing Environment Relics:** During development, I've seen this happen when test data isn't properly cleared between runs, or when an accidental re-insertion occurs against a persistent development database.

## Common Causes

Let's break down the specific situations that commonly lead to this `UniqueViolation`:

*   **Primary Key Duplication:** Every table has a primary key (PK), which must be unique and non-NULL. If you manually specify a PK value for a new record and that value already exists, this error will occur. Most ORM setups use auto-incrementing primary keys, which reduces this specific manual error, but it can still happen if you're importing data or explicitly setting PKs.
*   **Unique Index Violation:** Beyond the primary key, you can define unique constraints or unique indexes on other columns or combinations of columns. Common examples include a `users` table where `email` must be unique, or an `orders` table where `order_number` must be unique. Attempting to insert a user with an email that already exists will trigger this.
*   **Accidental Double-Insertion:** A user might click a "submit" button twice rapidly, or a retry mechanism might re-send a request after an initial attempt partially succeeds but the client thinks it failed. If the backend is not designed to be idempotent for record creation, two identical records could try to be inserted.
*   **Race Conditions:** As mentioned, if two separate processes or threads try to create a record with the same unique attribute at nearly the same time, both might perform a `SELECT` to check for existence, find nothing, and then both proceed with `INSERT`. One will succeed, the other will fail with a `UniqueViolation`.
*   **Corrupted or Inconsistent Data:** While less common, sometimes manual database edits or faulty data imports can introduce inconsistencies, causing subsequent legitimate application operations to hit unique constraints unexpectedly.

## Step-by-Step Fix

Fixing this error requires a methodical approach, starting with understanding *where* the violation is occurring.

1.  **Analyze the Traceback:**
    The traceback from SQLAlchemy and `psycopg2` will usually tell you which SQL statement failed and, crucially, which unique constraint was violated. Look for a line similar to `DETAIL: Key (email)=(test@example.com) already exists.` This detail is gold. It tells you the column (`email`) and the conflicting value (`test@example.com`).

    ```python
    Traceback (most recent call last):
      File "app.py", line 25, in <module>
        session.commit()
      File "<env>/lib/python3.9/site-packages/sqlalchemy/orm/session.py", line 1476, in commit
        self._transaction.commit(_to_root=True)
      File "<env>/lib/python3.9/site-packages/sqlalchemy/orm/session.py", line 828, in commit
        self._finish_transaction(db_transaction, error_handler=lambda e: self._handle_commit_block(e, db_transaction))
      File "<env>/lib/python3.9/site-packages/sqlalchemy/orm/session.py", line 872, in _finish_transaction
        self._commit_impl(db_transaction)
      File "<env>/lib/python3.9/site-packages/sqlalchemy/orm/session.py", line 898, in _commit_impl
        db_transaction.commit()
      File "<env>/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 2038, in commit
        self._do_commit()
      File "<env>/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 2068, in _do_commit
        self.connection.commit()
      File "<env>/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 1058, in commit
        self._execute_impl(self._commit_impl)
      File "<env>/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 1083, in _execute_impl
        util.raise_(_wrap_exception(e, self._dbapi_connection))
      File "<env>/lib/python3.9/site-packages/sqlalchemy/util/langhelpers.py", line 146, in raise_
        raise exc_info[1].with_traceback(exc_info[2])
      File "<env>/lib/python3.9/site-packages/sqlalchemy/engine/base.py", line 1049, in _execute_impl
        self.connection.commit()
    sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "uq_users_email"
    DETAIL:  Key (email)=(amara@example.com) already exists.
    ```

2.  **Identify the Table and Column/Constraint:**
    From the `DETAIL` in the traceback, you know the column (`email`) and the constraint (`uq_users_email`). If the detail isn't clear, you can sometimes infer the table from the context of your code or the constraint name (e.g., `uq_users_email` strongly suggests the `users` table).

3.  **Inspect Database Schema:**
    Connect to your PostgreSQL database using `psql` or a GUI tool and inspect the table's schema.

    ```bash
    psql -U your_user -d your_db
    \d your_table_name
    ```
    This will show you all columns, indexes, and constraints, confirming the unique constraint reported in the error.

4.  **Review Application Logic:**
    Trace the code path that leads to the `INSERT` or `UPDATE` statement that failed.
    *   Where is the data coming from?
    *   Is there a `SELECT` query happening *before* the `INSERT` to check for existence?
    *   Could the value be generated, and if so, is the generation truly unique?
    *   Is this part of an API endpoint? Is it being called multiple times?
    *   Are you handling user input correctly? Perhaps a case-insensitive unique constraint is needed, but the current one is case-sensitive.

5.  **Implement Preventative Measures (Code Changes):**

    *   **Check for Existence:** Before inserting, query the database to see if the unique value already exists. If it does, either update the existing record or signal an error back to the user/caller.

        ```python
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy import create_engine
        from my_app.models import User # Assuming User model with 'email' field

        # ... setup engine and session ...
        engine = create_engine('postgresql://user:password@host/dbname')
        Session = sessionmaker(bind=engine)
        session = Session()

        new_email = "amara@example.com"
        existing_user = session.query(User).filter_by(email=new_email).first()

        if existing_user:
            print(f"User with email {new_email} already exists. Updating instead of creating.")
            # Update existing user or raise a more friendly error
            existing_user.username = "AmaraDUpdated"
        else:
            new_user = User(username="AmaraD", email=new_email)
            session.add(new_user)
            print(f"Creating new user {new_email}.")

        session.commit()
        session.close()
        ```

    *   **UPSERT (Update or Insert):** For PostgreSQL, leverage `ON CONFLICT DO UPDATE` to gracefully handle duplicates. SQLAlchemy supports this through its `insert()` construct.

        ```python
        from sqlalchemy import insert
        from my_app.models import User

        # ... session setup ...

        user_data = {"username": "AmaraD", "email": "amara@example.com", "age": 30}

        # This attempts to insert. If email conflicts, it updates username and age.
        stmt = insert(User).values(**user_data).on_conflict_do_update(
            index_elements=[User.email], # The unique column(s) that cause the conflict
            set_={
                "username": user_data["username"],
                "age": user_data["age"]
            }
        )
        session.execute(stmt)
        session.commit()
        session.close()
        ```

    *   **Proper Error Handling:** Wrap your database operations in `try...except IntegrityError` blocks to catch the error and handle it gracefully, rather than crashing the application. This is especially useful for race conditions where `ON CONFLICT` isn't suitable or when you want to return a specific error message to the user.

        ```python
        from sqlalchemy.exc import IntegrityError
        from my_app.models import User

        # ... session setup ...

        new_user = User(username="TestUser", email="test@example.com")
        try:
            session.add(new_user)
            session.commit()
            print("User added successfully!")
        except IntegrityError as e:
            session.rollback() # Crucial: rollback the transaction
            if "(psycopg2.errors.UniqueViolation)" in str(e):
                print(f"Error: User with this email already exists.")
                # You might log the full error or return a specific API error code
            else:
                print(f"An unexpected integrity error occurred: {e}")
                raise # Re-raise if it's not a unique violation we know how to handle
        finally:
            session.close()
        ```

6.  **Consider Concurrency:** If race conditions are a primary concern, `ON CONFLICT DO UPDATE` is often the most robust solution for UPSERT scenarios. For simple insertions, sometimes relying on the unique constraint and catching the `IntegrityError` is acceptable, treating it as an "optimistic concurrency" approach. Database-level locking is rarely needed for simple unique constraint violations but can be part of more complex transaction isolation strategies.

7.  **Test Thoroughly:** After implementing changes, ensure your tests cover both successful inserts and attempts to insert duplicate data, verifying that your error handling or prevention mechanisms work as expected.

## Code Examples

Here are concise, copy-paste ready examples for typical scenarios.

**Example 1: Triggering the Error (for demonstration)**

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError

# Define the base for declarative models
Base = declarative_base()

class User(Base):
    __tablename__ = 'users_example' # Use a distinct name for examples
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

# Database setup (using an in-memory SQLite for simplicity, but same logic for PostgreSQL)
# For PostgreSQL: engine = create_engine('postgresql://user:password@host/dbname')
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# First user - successful
user1 = User(username="alice", email="alice@example.com")
session.add(user1)
session.commit()
print(f"Added: {user1}")

# Second user with duplicate email - will raise IntegrityError
user2 = User(username="bob", email="alice@example.com")
try:
    session.add(user2)
    session.commit()
    print(f"Added: {user2}") # This line won't be reached
except IntegrityError as e:
    session.rollback() # Rollback the failed transaction
    print(f"Caught expected error: {e}")
    # The actual psycopg2 error would be different for SQLite, but the concept is the same.
    # For PostgreSQL, it would contain 'psycopg2.errors.UniqueViolation'
    print("Database state after rollback is consistent.")
finally:
    session.close()

# Example using a different unique constraint (username)
session = Session() # Re-establish session after close
user3 = User(username="alice", email="charlie@example.com")
try:
    session.add(user3)
    session.commit()
    print(f"Added: {user3}")
except IntegrityError as e:
    session.rollback()
    print(f"Caught expected error for username: {e}")
finally:
    session.close()
```

**Example 2: Handling with `ON CONFLICT DO UPDATE` (UPSERT)**

```python
from sqlalchemy import create_engine, Column, Integer, String, insert
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products_example'
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False) # Unique SKU
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}', price={self.price})>"

engine = create_engine('sqlite:///:memory:') # Use 'postgresql://...' for PostgreSQL
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Initial product insert
product_data_1 = {"sku": "A101", "name": "Laptop", "price": 1200}
stmt1 = insert(Product).values(**product_data_1)
session.execute(stmt1)
session.commit()
print(f"Initial insert for SKU {product_data_1['sku']}: {session.query(Product).filter_by(sku='A101').first()}")

# UPSERT: Attempt to insert same SKU, but update name and price if conflict
product_data_2 = {"sku": "A101", "name": "Gaming Laptop", "price": 1500}
stmt2 = insert(Product).values(**product_data_2).on_conflict_do_update(
    index_elements=[Product.sku], # The unique column(s)
    set_={
        "name": product_data_2["name"],
        "price": product_data_2["price"]
    }
)
session.execute(stmt2)
session.commit()
print(f"UPSERT for SKU {product_data_2['sku']}: {session.query(Product).filter_by(sku='A101').first()}")

# UPSERT: Insert a new product if SKU doesn't exist
product_data_3 = {"sku": "B202", "name": "Monitor", "price": 300}
stmt3 = insert(Product).values(**product_data_3).on_conflict_do_nothing(
    index_elements=[Product.sku]
) # Or do_update if you want to update on conflict
session.execute(stmt3)
session.commit()
print(f"UPSERT for SKU {product_data_3['sku']}: {session.query(Product).filter_by(sku='B202').first()}")

session.close()
```

## Environment-Specific Notes

*   **Local Development:** This is where you'll most frequently encounter and debug `IntegrityError`s. The advantage is that you can quickly reset your database, modify code, and iterate. If you're using a local PostgreSQL instance, `DROP TABLE` and `CREATE TABLE` can be a quick fix for development data issues, but be cautious not to propagate such habits to production. I often use `alembic downgrade base` and `alembic upgrade head` to reset schema and re-apply migrations when I'm prototyping models.
*   **Docker Containers:** When running your database in Docker (e.g., `postgres:latest`), ensure that your database data is persisted using a Docker volume. If not, every time the container restarts, your database will be reset to an empty state, potentially masking unique constraint issues that would appear with persistent data. Using a named volume (`docker volume create my_pg_data` and then mounting it) is crucial.
*   **Cloud (AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL):** In cloud environments, databases are managed services, offering higher availability and automatic backups. Troubleshooting `IntegrityError` here requires careful use of logs (CloudWatch Logs for RDS, Cloud Logging for GCP). You cannot directly shell into the database server for schema inspection. Instead, you'd use client tools like `psql` or the cloud provider's console/CLI. Data recovery from backups is an option for severe data corruption, but for simple unique violations, it's about fixing the application logic. I've seen this error occur in production systems when deploying new features with incomplete data migrations or when a legacy system accidentally pushes duplicate data. Monitoring tools and proper logging become indispensable for rapid diagnosis.

## Frequently Asked Questions

**Q: Can I just ignore `IntegrityError`?**
**A:** No, absolutely not. An `IntegrityError` indicates a violation of your database's schema rules, meaning your data would be inconsistent if the operation were allowed. Ignoring it would lead to corrupted data, which can break application logic or lead to incorrect reports down the line.

**Q: Is `IntegrityError` always a bug in my application code?**
**A:** While often a bug in application logic (e.g., trying to insert a duplicate without checking), it can also highlight a valid race condition in a highly concurrent system. In these cases, the "fix" isn't necessarily a bug fix but implementing robust concurrency handling (like UPSERTs or specific error recovery).

**Q: How do I find *which* specific unique constraint or index is being violated?**
**A:** The `DETAIL:` message in the `IntegrityError` traceback is your best friend. It explicitly states the key (e.g., `(email)=(test@example.com)`) and often the name of the unique constraint (e.g., `uq_users_email`). If the detail is generic, inspecting the table's indexes and constraints (`\d your_table` in `psql`) will reveal them.

**Q: Should I just use `UPDATE` instead of `INSERT` to avoid this error?**
**A:** It depends on your business logic. If you intend to create a new record if it doesn't exist, but modify an existing one if it does, then an UPSERT (using `ON CONFLICT DO UPDATE`) is the correct approach. If a duplicate should always be an error, then checking for existence or catching the `IntegrityError` is appropriate. Simply replacing all `INSERT`s with `UPDATE`s without proper checks could lead to unintended data overwrites.

**Q: What about race conditions when checking for existence before inserting?**
**A:** This is a classic problem. Even if you `SELECT` to see if a record exists and then `INSERT` if it doesn't, another process could `INSERT` in the tiny window between your `SELECT` and `INSERT`. For PostgreSQL, the `ON CONFLICT DO UPDATE` or `ON CONFLICT DO NOTHING` clauses are designed to solve this at the database level, ensuring atomicity and preventing race conditions for UPSERT-like operations. Otherwise, catching the `IntegrityError` and retrying or reporting the conflict is the robust way to handle it.

## Related Errors
*(none)*