# Admin Operations Guide

## ERP Roles

Create or assign users to these Django groups:

- `Super Admin`
- `Admin`
- `Counselor`
- `Accountant`
- `Attendance Manager`

Superusers bypass group checks, but production staff should use named roles for auditability.

## What Is Now Audited

- successful login
- logout
- admission creation
- fee payment creation
- batch creation
- batch archival
- batch end
- batch restore

Review logs in Django admin under `Audit Logs` and `Login Attempts`.

## Recommended Admin Policies

- restrict superuser accounts to owners or senior operations staff
- assign accountants only to finance workflows
- assign attendance managers only to batch and attendance workflows
- review failed login attempts weekly
- archive batches instead of hard deleting operational records

## Post-Deployment Checklist

1. Run `python manage.py migrate`.
2. Create a superuser if needed.
3. Assign ERP roles to staff users.
4. Verify `/health/` returns a healthy response.
5. Test admission creation, payment posting, and attendance access with real role accounts.
6. Test batch end and restore on a non-production sample batch before using it operationally.

## Batch Lifecycle Workflow

1. Open `Batch Management > End Batch`.
2. Select batch month and year and review warnings.
3. End the batch only after confirming operational completion.
4. Use `Ended Batches` for review and `Restore Batch` if students need to re-enter attendance.
5. Review `Batch Reports` and `BatchActionLog` regularly for accountability.
