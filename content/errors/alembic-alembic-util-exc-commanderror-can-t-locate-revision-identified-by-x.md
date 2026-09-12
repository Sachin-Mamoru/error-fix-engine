# alembic.util.exc.CommandError: Can't locate revision identified by 'X'
> Encountering `alembic.util.exc.CommandError: Can't locate revision identified by 'X'` means Alembic cannot find a migration revision file that is referenced; this guide explains how to fix it.

As a platform engineer, I've seen my share of database migration headaches. This particular Alembic error is one of those frustrating messages that immediately tells you something is out of sync between your database's understanding of its schema history and the migration files available in your project. It's a fundamental break in the migration chain, and it needs careful attention to resolve.

### What This Error Means

At its core, Alembic manages your database schema evolutions using a directed acyclic graph (DAG) of revisions. Each revision is a specific change, identified by a unique ID (the 'X' in the error message) and usually linked to a previous revision. Your database keeps track of the latest applied revision in a special table, typically named `alembic_version`.

The error `alembic.util.exc.CommandError: Can't locate revision identified by 'X'` means that Alembic was asked to operate on a revision 'X' – perhaps to upgrade to it, downgrade from it, or even just display its history – but it couldn't find the corresponding migration script file within your project's `versions/` directory (or wherever you've configured your migration scripts to live). It's like having a library catalog entry for a book that's no longer on the shelves.

This most commonly happens when the `alembic_version` table in your database indicates that it's currently at revision 'X', but the `versions/` directory in your application code does not contain the file `X_my_migration.py`. Alternatively, you might be trying to upgrade to a revision 'Y' which has 'X' as its direct predecessor, but 'X' is missing.

### Why It Happens

Alembic needs a complete and consistent set of migration files to correctly understand the history of your database schema. It uses these files to determine the current state, what upgrades/downgrades are possible, and how to apply them. When a revision identified by 'X' is missing, it breaks this chain.

In my experience, this usually points to a discrepancy between:
1.  **The state recorded in the `alembic_version` table in your database.** This table holds the ID of the last successfully applied migration.
2.  **The actual migration script files available in your project's `versions/` directory.** These are the Python files containing the `upgrade()` and `downgrade()` functions.
3.  **Your expectation of what revisions should be present**, often based on your Git history or a teammate's instructions.

When these three sources of truth don't align, Alembic throws its hands up and declares it "Can't locate revision identified by 'X'". It simply doesn't know how to proceed because a crucial piece of its historical knowledge is gone.

### Common Causes

Based on years of dealing with this, here are the most frequent culprits:

*   **Accidental Deletion or Untracked Files:** This is probably the number one reason. A developer might have inadvertently deleted a migration file, or a newly generated migration file was not committed to version control and therefore isn't present in other environments (like CI/CD or production).
*   **Git History Rewrites (Rebasing, Force Pushing):** When you rebase your branch or force-push changes that rewrite Git history, it can sometimes alter the unique revision IDs of migration files or even remove them if they were introduced and then squashed out. If your `alembic_version` table already knows about the old 'X' revision, but Git history has been rewritten to no longer include it, you're in trouble. I've seen this in production when a junior dev tried to "clean up" migration history before deploying, leading to a scramble.
*   **Environment Discrepancies:** A migration might have been applied in one environment (e.g., staging) but never made it to another (e.g., production) due to a deployment issue or a missed commit. Or, conversely, a local database was upgraded to a revision that doesn't exist in the current codebase pulled from `main`.
*   **Cherry-picking Issues:** If migrations are cherry-picked between branches, especially if dependencies aren't correctly managed, it can result in a fragmented history where an intermediate revision is skipped or missed.
*   **Multiple Heads (Less Common for *This* Error):** While this error is distinct from `Multiple heads identified`, a missing revision can sometimes expose or be related to a complex history that eventually leads to multiple heads if not handled carefully.
*   **Manual `alembic_version` Table Manipulation:** Sometimes, desperate measures lead to directly modifying the `alembic_version` table. If this was done incorrectly, referencing a non-existent revision or skipping one, this error can occur.

### Step-by-Step Fix

Solving this requires a systematic approach, starting with diagnosis and moving towards careful remediation. Always ensure you have a database backup before making significant changes, especially in non-development environments.

1.  **Identify the Missing Revision 'X' and Context:**
    *   Carefully read the error message. What is the exact revision ID 'X' that Alembic can't find?
    *   What command were you running that caused the error (e.g., `alembic upgrade head`, `alembic history`)? This helps understand *why* Alembic was looking for 'X'.

2.  **Inspect Your Project's Migration Files:**
    *   Navigate to your `versions/` directory (or equivalent).
    *   Look for a file named `X_my_migration.py` (where 'X' is the ID from the error). Is it present?
    *   Use `ls -al versions/ | grep X` (on Linux/macOS) or search manually.
    *   **If it's missing:**
        *   Check your Git history: `git log --all --full-history -- versions/` to see if it ever existed or was removed.
        *   Check other branches or teammate's repositories. Can you recover it?

3.  **Check Your Database's `alembic_version` Table:**
    *   Connect to the database where the error occurred (e.g., via `psql`, `mysql`, `sqlite3`).
    *   Query the `alembic_version` table to see what revision the database thinks it's currently at.
    ```sql
    SELECT * FROM alembic_version;
    ```
    *   Is the revision 'X' listed there? Is it the *only* revision listed?
    *   If the database says it's at 'X', but you don't have the file for 'X', this is your primary inconsistency.

4.  **Compare Local History with Expected History (Git):**
    *   Run `alembic history` to see the revision graph that Alembic *can* construct from your local files.
    *   Compare this with your team's main branch or expected history. Are there any discrepancies?
    *   Use `git status` or `git diff` to ensure you haven't accidentally modified or deleted a migration file locally.

5.  **Remediation Options (Choose carefully based on context):**

    *   **Option A: Restore the Missing Migration File (Preferred, if possible)**
        *   If the file `X_my_migration.py` was accidentally deleted or simply not present in your current checkout:
            *   Try to find it in your Git history (`git checkout <commit-hash> -- versions/X_my_migration.py`) or get it from a colleague.
            *   Once restored, ensure it's committed and pushed. Then, try your Alembic command again.
        *   This is the cleanest fix as it maintains the integrity of the migration history.

    *   **Option B: Downgrade the Database (Use with Extreme Caution, especially in production)**
        *   If the database is at revision 'X' but 'X' is missing, and you *know* that the *previous* revision 'Y' (the one `X` was based on) is present and represents a valid schema state, you *might* be able to downgrade.
        *   **CRITICAL:** Ensure that downgrading to 'Y' will not cause data loss or major schema inconsistencies for your current application version. This is rarely safe for production.
        ```bash
        alembic downgrade Y
        ```
        *   After downgrading, you might need to re-run your `alembic upgrade head` command to get to the correct state using the *available* files.

    *   **Option C: Use `alembic stamp` to Realign the Database (Advanced, Highly Situational)**
        *   If you are **absolutely certain** that your current database schema perfectly matches the schema state defined by a *known, existing* revision 'Y' (e.g., your `head` revision, or a specific revision you know was correctly applied), and the `alembic_version` table is just wrong, `alembic stamp` can force the `alembic_version` table to reflect that revision without running any upgrade/downgrade scripts.
        *   **Never use `alembic stamp` unless you understand the implications.** It doesn't modify the schema; it *only* updates the `alembic_version` table. Using it incorrectly will lead to severe schema drift.
        *   To stamp to a specific revision 'Y' (e.g., `head` if your current codebase is supposed to be fully migrated):
            ```bash
            alembic stamp Y
            ```
            Or, to stamp to the latest revision available in your codebase:
            ```bash
            alembic stamp head
            ```
        *   After stamping, try `alembic upgrade head` again. If it runs without errors, your database and migration files are now in sync according to Alembic.

    *   **Option D: Regenerate Migrations from a Clean Database (Last Resort for Development)**
        *   In a development environment, if the mess is too great to untangle, you might consider:
            1.  Deleting your local database.
            2.  Recreating it.
            3.  Running `alembic upgrade head` from a clean slate.
            4.  This is a blunt instrument and only viable for local dev.

### Code Examples

Here are some commands you'll frequently use when troubleshooting this error:

**1. Inspecting Alembic History:**
View the revisions Alembic can see based on your local `versions/` files.

```bash
alembic history
```

**2. Checking the Database's Current Revision:**
Connect to your database and query the `alembic_version` table. The exact command depends on your database.

```sql
-- For PostgreSQL/MySQL
SELECT * FROM alembic_version;

-- For SQLite (assuming alembic_version.db)
.open your_database.db
SELECT * FROM alembic_version;
```

**3. Downgrading to a Specific Revision (e.g., 'Y'):**
Only use if you're sure about the target revision and its implications.

```bash
alembic downgrade Y
```

**4. Stamping the Database to a Specific Revision (e.g., 'Y'):**
Use with extreme caution. 'Y' must be a revision whose schema state is *already* perfectly reflected in your database.

```bash
# To stamp to a specific revision ID
alembic stamp Y

# To stamp to the current HEAD (latest revision in your codebase)
alembic stamp head
```

**5. Generating a Blank Migration (if you need to manually bridge a gap):**
This is typically done *after* you've fixed the `alembic_version` table state or recovered missing files, but sometimes you might need to insert a "noop" migration to get things flowing.

```bash
alembic revision --autogenerate -m "Fixing missing revision chain"
```
*Note: Autogenerate might create an empty migration if your schema already matches, or it might capture new differences.*

### Environment-Specific Notes

The impact and troubleshooting approach can vary slightly depending on your environment.

*   **Local Development:** This is where you'll most frequently encounter and fix this error. You have the most control: direct database access, easy file system manipulation, and the ability to wipe/recreate your database. Don't be afraid to experiment with `alembic stamp` here, but learn from it.
*   **Docker/Containerized Environments:**
    *   Ensure your `versions/` directory is correctly mounted into the container or baked into the image. If your image builds without the latest migrations, you'll see this error.
    *   Rebuild your Docker image if you've added or changed migration files to ensure they are included.
    *   Database access might be through another container or service, requiring specific network configurations.
    *   I've personally run into this when CI/CD pipelines used an older Docker image cache that didn't include recent migration files, causing deployments to fail. Always ensure your build process includes the latest source.
*   **Cloud/CI/CD Pipelines:**
    *   This is where the error is most critical, as it halts deployments.
    *   The primary cause here is often a mismatch between the codebase deployed (missing files) and the existing database state (expecting 'X').
    *   Strict Git practices are essential. Ensure all migration files are committed, pushed, and correctly pulled by your CI/CD system.
    *   Remediation usually involves reverting the code change that introduced the missing file, finding and deploying the correct code, or, in dire circumstances, a carefully managed `alembic stamp` (with multiple reviews and backups).

### Frequently Asked Questions

*   **Q: Can I just delete the `alembic_version` table to fix this?**
    **A:** No, absolutely not, unless you are deliberately starting your database migration history entirely from scratch (e.g., for a new development instance). Deleting this table will make Alembic believe no migrations have ever been applied, and the next `alembic upgrade head` will attempt to apply *all* migrations, likely causing errors if your schema already exists. It's a very destructive action that should only be done with extreme caution and understanding.

*   **Q: What if I have multiple heads identified? Is that related?**
    **A:** While `Can't locate revision identified by 'X'` is a different error from `Multiple heads identified`, they can sometimes appear in complex migration scenarios. This error indicates a missing *node* in the graph, whereas multiple heads mean the graph has *diverged* with multiple "latest" revisions. Resolving a missing revision might sometimes reveal an underlying multiple heads issue, but they are distinct problems.

*   **Q: How can I prevent this error in the future?**
    **A:** Strict version control practices are key:
    1.  **Always commit generated migration files:** Never leave them untracked.
    2.  **Avoid Git history rewrites:** If you must rebase or squash, be extremely careful with commits that introduced migration files, especially if they've already been deployed.
    3.  **Regularly pull and upgrade:** Developers should regularly `git pull` and run `alembic upgrade head` to ensure their local database and codebase are in sync.
    4.  **Clear communication:** Ensure your team knows not to delete migration files.

*   **Q: Is `alembic stamp` safe to use?**
    **A:** `alembic stamp` is safe *only* if you are 100% certain that your database's schema exactly matches the state of the revision you are stamping to. It does *not* modify your database schema; it *only* updates the `alembic_version` table. If your schema does not match the stamped revision, you introduce schema drift that will lead to subtle, hard-to-debug issues later. Use it as a last resort and with extreme caution, ideally after a thorough schema comparison.

### Related Errors