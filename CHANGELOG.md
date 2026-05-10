## [Unreleased] - 2026-05-10

### Fixed
- `end_batch_confirm` now updates active students by batch month and year even when no course is submitted, preserving attendance and fee history.
- `restore_batch_confirm` now restores completed students to `active`, clears `batch_end_date`, and records the restore date.
- Student updates now create an audit log entry for traceability.

### Security
- Upgraded `cryptography` from `41.0.7` to `42.0.8`.
- Moved the Django admin off the default `/admin/` path to the configurable `ADMIN_URL` setting, defaulting to `/secure-admin/`.
- Added explicit production cookie and content-type hardening in `Project.settings.prod`.
- Replaced template `|safe` JSON injection with escaped `JSON.parse(...)` payloads.
- Updated the Docker health check to use `/health/` instead of the admin login page.
- Confirmed `Project.settings.prod` already sets `SECURE_HSTS_SECONDS = 31536000` and `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`.
- Confirmed `SECRET_KEY` is loaded via environment/config and is not hardcoded.
- Wired explicit image upload validation in `core/forms.py` so student photo uploads are validated before save.

### Improved
- Added targeted regression tests for fee edge cases, attendance idempotency, sales dashboard permissions, custom admin routing, student update auditing, and validators.
- Ran `isort` and `black` across `core/`, then cleared the remaining `flake8` backlog in application code to reach `0` E-codes and `0` F-codes for `core/` (excluding migrations).
- Added pagination (`25` per page) to admitted students and student finance detail list views without changing existing context variable names.
- Optimized key list/report views with `select_related`/`prefetch_related` in admitted student, attendance report, and fee-payment-related flows.
- Cached course lists and shared time-slot dropdown data through `LocMemCache` for 300 seconds.
- Added Google-style docstrings to missing functions in `core/views.py`, plus class-level docstrings in `core/models.py`.
- Added targeted inline comments above complex queryset/business logic blocks touched in this pass.
- Added shared accessibility handling in the base templates to supply missing `aria-label` attributes for form inputs/buttons, wrap unwrapped tables in `.table-responsive`, and backfill empty `alt` attributes on images at render time.
- Added the missing empty `alt` attribute to the admission photo preview image.
- Added migration `core.0032_remove_feepayment_core_feepay_payment_7504a3_idx_and_more` to represent the `FeePayment.payment_date` index state and remove the redundant standalone model index definition.
