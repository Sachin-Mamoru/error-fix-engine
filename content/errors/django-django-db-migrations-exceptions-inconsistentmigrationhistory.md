# django.db.migrations.exceptions.InconsistentMigrationHistory
> Encountering an InconsistentMigrationHistory exception means your Django project's database migration state is out of sync with its code, and this guide provides a clear, practical path to resolution.

## What This Error Means

The `django.db.migrations.exceptions.InconsistentMigrationHistory` error indicates a critical mismatch between your Django project's migration files (the Python files that define database schema changes) and the actual state recorded in your database's `django_migrations` table. Django uses this table to keep track of which migrations have been applied. When this error appears, it means Django cannot confidently determine the database's current schema state based on its migration history, preventing it from applying new migrations or even running `makemigrations`.

Essentially, Django is saying, "I have these instructions for changing the database, and the database claims to have followed some of them, but what the database says it did doesn't line up with the instructions I have here." This is a safety mechanism designed to prevent you from accidentally corrupting your database or applying changes based on an incorrect understanding of its current state.

## Why It Happens

Django's migration system is robust, but it relies on a consistent history. Each migration file has a unique name and a dependency chain. When you run `python manage.py migrate`, Django looks at your migration files, compares them to the entries in the `django_migrations` table, and applies any new migrations in the correct order.

This specific error occurs when:
1.  **A migration file exists in your codebase that is marked as applied in `django_migrations`, but the actual database schema does not reflect that migration.** This is less common but can happen if a migration was partially applied and then failed, or if a database was restored from an older backup.
2.  **A migration file is missing from your codebase, but it is recorded as applied in the `django_migrations` table.** This is a frequent cause and often results from Git operations (like rebasing, force pushing, or improper merges) that remove or reorder migration files, or simply accidentally deleting migration files.
3.  **The order of migrations in your codebase doesn't match the order recorded in `django_migrations`.** This can lead to Django trying to apply a migration that depends on another one it hasn't seen yet, or one that it thinks has already been applied out of order.
4.  **A new migration file depends on an older migration that Django can't find** (either missing or misidentified).

The system is designed to be atomic; a migration is either fully applied or not at all. This error surfaces when that atomicity is broken, or when the external state (the database) doesn't match the internal state (the migration files).

## Common Causes

In my experience, encountering `InconsistentMigrationHistory` usually stems from one of a few common scenarios:

*   **Manual Database Changes:** This is arguably the most common culprit. Directly altering the database schema (e.g., adding a column, changing a table name) via SQL commands or a database GUI without generating and applying a corresponding Django migration can confuse Django. It expects to be the sole orchestrator of schema changes.
*   **Git Operations Gone Wrong:** I've seen this frequently in production when teams use Git rebase or force pushes that rewrite history. If migration files are reordered, deleted, or their content is altered after they've been committed and potentially applied to a shared database, Django will detect this inconsistency. Merging branches with conflicting migrations without proper squashing or handling can also lead to issues.
*   **Restoring Database Backups:** Restoring a database snapshot that is older than your current codebase's migration history will cause this. The database's `django_migrations` table will reflect an older state, while your project expects a more recent one.
*   **Deleting Migration Files:** Sometimes, developers delete older migration files to clean up the `migrations/` directory. If these migrations were already applied to a database (and recorded in `django_migrations`), Django will no longer find the file but still expect it based on the database's history. This is why squashing migrations is preferred over deletion.
*   **Improper Use of `--fake` or `--fake-initial`:** While these flags are useful, their incorrect application can lead to the `django_migrations` table recording an applied migration that never actually ran, or vice versa, creating a future inconsistency.
*   **Concurrent Deployment Issues:** In rare cases, if multiple deployment processes attempt to run migrations simultaneously without proper locking or coordination, race conditions could potentially lead to a corrupted `django_migrations` table or an inconsistent state.

## Step-by-Step Fix

Before attempting any fix, **always back up your database.** This is non-negotiable, especially in production environments. Any direct manipulation of migration history carries risk.

1.  ### Understand the Current State
    The error message itself will often point to the specific app and migration that is causing the problem (e.g., `app_label.00xx_migration_name`).
    First, inspect what Django believes the migration state should be:

    ```bash
    python manage.py showmigrations
    ```

    Look for `[X]` (applied) and `[ ]` (pending) next to your migrations. Pay close attention to the migration mentioned in the error. Then, connect to your database and inspect the `django_migrations` table directly. For PostgreSQL, it might look like this:

    ```sql
    SELECT * FROM django_migrations ORDER BY app, id;
    ```

    Compare the output:
    *   Does Django's `showmigrations` show `[X]` for the problematic migration, but it's *not* in `django_migrations`?
    *   Is the migration in `django_migrations`, but `showmigrations` shows `[ ]`?
    *   Is the migration missing entirely from your filesystem but present in `django_migrations`?

2.  ### Backup Your Database
    Seriously, do this. If you mess up, a rollback is your only safe option.

    ```bash
    # Example for PostgreSQL, adapt for your database
    pg_dump -U your_user -h your_host your_database_name > db_backup_$(date +%F).sql
    ```

3.  ### Identify and Resolve the Specific Inconsistency

    **Scenario A: Migration exists in DB (`django_migrations`) but not on disk OR is out of order.**
    This often happens after a Git rebase/reset or accidental deletion of migration files. Django sees an entry in the `django_migrations` table but can't find the corresponding file.
    *   **Solution:** Your primary goal here is to get the migration files on disk to match what's in the `django_migrations` table.
        *   If the migration file was *accidentally deleted*, try to restore it from Git history.
        *   If the migration was *squashed* or *reordered* in Git, you might need to revert your codebase to a state where the migrations align, then re-apply squashed migrations carefully.
        *   **Manual cleanup (last resort):** If you are absolutely certain the migration file is gone and its effects are either irrelevant or already manually applied, you *could* remove the corresponding entry from the `django_migrations` table. This is dangerous and should be avoided in production unless you fully understand the consequences.

    **Scenario B: Migration exists on disk, but not in DB (`django_migrations`), yet its changes are already in the schema.**
    This typically occurs if you manually applied database changes, restored an older backup, or ran a migration with `--fake` incorrectly. Django tries to apply a migration, but the necessary tables/columns already exist, causing an error.
    *   **Solution:** Use the `--fake` flag to tell Django to mark the migration as applied without running its `operations`.

        ```bash
        python manage.py migrate <app_label> <migration_name> --fake
        ```
        Replace `<app_label>` with the name of the Django app (e.g., `users`) and `<migration_name>` with the full name of the migration file without the `.py` extension (e.g., `0003_add_email_field`).
        After faking the problematic migration, try running `python manage.py migrate` again for any remaining pending migrations.

    **Scenario C: Migration exists on disk, not in DB, and its changes are *not* in the schema (it genuinely needs to be applied).**
    This means Django is failing to apply a necessary migration for other reasons, and the `InconsistentMigrationHistory` error is a symptom. This is less common but can occur if dependencies are truly broken.
    *   **Solution:** You might need to examine the specific migration file for syntax errors or issues in its `dependencies` tuple. If it depends on a migration that truly hasn't been applied, you might need to force apply preceding migrations or resolve issues in them first.

4.  ### Re-run Migrations
    Once you've addressed the specific inconsistency, try running `migrate` again:

    ```bash
    python manage.py migrate
    ```

    If successful, Django will apply any remaining pending migrations. If you encounter the error again, you might have multiple inconsistencies or missed the root cause. Repeat the diagnostic steps.

## Code Examples

Checking migration status:
```bash
python manage.py showmigrations
```
This command outputs a list of all migrations, showing an `[X]` if applied and `[ ]` if pending.

Faking a specific migration:
```bash
python manage.py migrate myapp 0005_add_profile_model --fake
```
This tells Django that the migration `0005_add_profile_model` in `myapp` has already been applied to the database, so it simply marks it as such in `django_migrations` without executing any SQL. This is incredibly useful when the database schema *already* reflects the state after that migration, but `django_migrations` doesn't know it.

SQL to inspect `django_migrations` table (example for PostgreSQL):
```sql
SELECT app, name, applied FROM django_migrations ORDER BY app, id;
```
This will show you the exact entries Django stores for its migration history.

Generating new migrations if you've made manual schema changes (after resolving history):
```bash
python manage.py makemigrations myapp
```
This will generate new migration files based on changes in your models compared to the last applied migration.

## Environment-Specific Notes

The approach to fixing `InconsistentMigrationHistory` can vary slightly depending on your environment.

*   **Local Development:** This is the easiest place to fix such issues. If your database is a simple SQLite file (`db.sqlite3`), you can often resolve the issue by deleting the `db.sqlite3` file entirely, then running `python manage.py makemigrations` and `python manage.py migrate` from scratch. This effectively resets your local database to an empty state and builds it up cleanly. For other local databases, you might drop the entire database and recreate it. Of course, this means losing all local data, so only do it if acceptable.
*   **Docker/Containerized Environments:** When working with Docker, your database is likely running in its own container, and its data is persisted in a Docker volume. When an inconsistency occurs, you'll need to run the `migrate --fake` commands *inside* the database container or on the application container that connects to it.
    ```bash
    docker-compose exec web python manage.py migrate myapp 0005_add_profile_model --fake
    docker-compose exec web python manage.py migrate
    ```
    Ensure your CI/CD pipeline correctly handles migration application. I've often seen this error when a `Dockerfile` rebuilds images without considering database volume persistence, or if `migrate` runs too early/late in the entrypoint.
*   **Cloud (e.g., AWS RDS, Azure SQL, Google Cloud SQL):** Production environments demand extreme caution. Direct shell access to the database server might be limited, so you'll typically use `psql`, `mysql`, or another client from your local machine or a bastion host. Always test the fix on a staging environment that mirrors production before attempting it live. Database backups are absolutely paramount here. Utilize CI/CD pipelines that incorporate migration health checks and apply migrations transactionally. If you need to manually intervene in `django_migrations` directly with SQL, ensure you are in a maintenance window and have robust roll-back plans. I always advise against direct SQL manipulation of `django_migrations` in production unless it's a critical disaster recovery scenario and other options are exhausted.

## Frequently Asked Questions

**Q: Can I just delete my `django_migrations` table?**
A: **Absolutely not in production, and generally not recommended even in development unless you fully understand the implications.** Deleting this table removes Django's entire history of applied migrations. When you next run `migrate`, Django will try to apply *all* migrations from the beginning, likely causing errors because tables and columns already exist. It's a quick way to completely desync your database and codebase. Only do this in development if you are prepared to drop and recreate your entire database from scratch.

**Q: When should I use `--fake` vs. `--fake-initial`?**
A: Use `--fake` when a specific migration file (e.g., `0005_add_profile_model`) is present in your codebase, but its changes are *already applied* to the database schema, yet the `django_migrations` table doesn't record it. It marks an existing migration as applied. `--fake-initial` is used specifically for the *first* migration of an app when the tables for that app already exist in the database (e.g., you're bringing an existing database under Django's migration control for the first time).

**Q: My deployment pipeline failed with this error. What's the best practice?**
A: Immediately halt further deployments to prevent cascading issues. Backup your production database. Diagnose the specific migration and app indicated in the error message using `showmigrations` on your deployment server. Carefully identify if the migration truly hasn't been applied or if it's already there but unrecorded. Then, apply the `--fake` solution for the specific problematic migration if the latter is true. Always test the exact fix on a staging environment first. Ensure your CI/CD applies migrations as a distinct, atomic step *before* your application code starts serving traffic.

**Q: What if the error points to a migration file that doesn't exist anymore?**
A: This means an entry for that migration still exists in your `django_migrations` table, but the corresponding `.py` file is missing from your project's `migrations/` directory. This is a classic symptom of Git history rewriting or accidental deletion. You have two main options:
1.  **Restore the migration file:** The safest option is to find the missing migration file in your Git history and restore it.
2.  **Manually remove the `django_migrations` entry (risky):** If you are absolutely certain that the database schema is correct *without* that migration, and that migration was a mistake or truly irrelevant, you could *carefully* delete the corresponding row from the `django_migrations` table. This should be a last resort and only after thorough analysis and backup.

## Related Errors
*(none)*