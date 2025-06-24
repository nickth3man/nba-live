# Local Database Files

This directory is designated for storing local database files, such as SQLite snapshots, that are used for development purposes and are not intended for production.

---

## Key Responsibilities

*   Provides a consistent location for local database files.
*   Is explicitly ignored by `git` to prevent large data files from being committed to the repository.

## Structure

*This directory is intended to hold database files (e.g., `.sqlite`) that are generated during local development.*

---

## Important Note

Files in this directory **should not be committed to version control**. The production database is managed in a separate, dedicated Docker volume.