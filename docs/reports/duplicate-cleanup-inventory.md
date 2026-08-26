# Duplicate and Cleanup Inventory

## Scope

This inventory focuses on the source, docs, and application trees under the workspace and highlights items that are likely to be removable or worth consolidating.

## High-confidence cleanup candidates

### 1. Generated Next.js build artifacts

The workspace contains many generated files under the web app build/output directories, including manifests, prerender artifacts, and hashed chunk files. These are not source-of-truth files and should generally be excluded from version control and removed from local working trees when not needed for debugging.

Examples observed:
- Next.js manifests such as build-manifest.json, prerender-manifest.json, and routes-manifest.json
- Hashed server chunk files under the web app output tree
- Internal action chunk files generated for multiple routes

### 2. Python cache and test artifacts

The repository currently contains Python cache artifacts such as __pycache__ and pytest cache folders. These are build/runtime noise and should be cleaned regularly.

Examples observed:
- .pytest_cache
- __pycache__ directories
- compiled .pyc files under source and test trees

### 3. Duplicate filenames that are not true duplicates but share a common name

A broad filename scan shows many repeated names such as index.ts, constants.py, service.py, and README.md across different modules. These are not automatically safe to delete because they often belong to different subsystems.

The cleanup action should be limited to:
- generated artifacts
- clearly redundant local build output
- duplicated documentation or placeholder files that are explicitly superseded

## Recommended approach

1. Add generated directories to .gitignore if they are not already excluded.
2. Remove local build caches and temporary output before shipping changes.
3. Review duplicate filenames only when the owning module is clearly redundant or has been superseded.
4. Avoid deleting files just because their basename is duplicated; confirm the module purpose first.

## Suggested immediate actions

- Remove local Next.js output artifacts from the web app if present.
- Remove Python cache and pytest artifacts from the workspace.
- Keep source files with repeated names unless there is evidence they are duplicate implementations.
