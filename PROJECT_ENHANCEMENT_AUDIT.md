# Project Enhancement Audit

## Executive Summary

The project had solid domain coverage for an institute management system, but it was still operating as a tightly coupled single-app Django codebase with business logic concentrated in `core/views.py`. The implemented upgrade pass establishes a safer ERP-grade foundation without forcing a risky full rewrite.

## High-Risk Findings Identified

- Monolithic view layer with cross-cutting business logic, security, imports, reporting, and backup operations mixed together
- Coarse-grained access control based mainly on `login_required` and `staff_member_required`
- No native audit trail for sensitive actions
- No admission-grade student identifier lifecycle
- No archive strategy for operational records
- Authentication lacked brute-force throttling
- No session idle timeout
- Production settings assumed optional dependencies that were not safely guarded
- Tests were effectively absent

## Implemented in This Upgrade

### Architecture

- Added domain view modules:
  - `admissions/views.py`
  - `finance/views.py`
  - `attendance/views.py`
  - `batch_management/views.py`
  - `reports/views.py`
- Added service layer:
  - `core/services/admission_service.py`
  - `core/services/fee_service.py`
  - `core/services/batch_service.py`

### Security

- Added login attempt throttling
- Added session idle timeout middleware
- Added ERP role-based access helpers using Django groups
- Added health endpoint for deployment monitoring
- Added ZIP validation utility for safer backup/import workflows

### Data Model

- Added `student_id` to admissions with yearly sequence generation
- Added archive fields to students, enquiries, and batches
- Added `created_at` to admissions and `updated_at` to enquiries
- Added `AuditLog` and `LoginAttempt` tables
- Added indexing for `batch_month`

### Business Workflow

- Admissions now create audit records
- Fee payments now:
  - validate amounts centrally
  - update fees atomically
  - sync installment breakdowns automatically
  - write audit events
- Batch deletion is now archive-oriented in the new workflow path
- Batch lifecycle management now supports:
  - active vs completed batch eligibility
  - reversible restore flow
  - per-batch action logging
  - pending-fee warnings before completion

### Testing

- Added automated tests for:
  - login throttling
  - fee payment integrity
  - admission creation and student ID generation
  - role-based batch access

## Remaining Roadmap

### Next Refactor Wave

- move the remaining `core/views.py` endpoints into domain modules
- split models into app-specific modules
- introduce API serializers and versioned REST endpoints
- isolate backup/import/export into an `ops` module

### ERP / CRM Expansion

- enquiry stages and lead funnel ownership
- notification center
- document center
- certificate automation
- expense management
- payroll
- branch / franchise ownership model
- parent and student portal

### SaaS Readiness

- tenant-aware data model
- white-label branding settings
- subscription and billing module
- per-tenant storage and reporting isolation
- API-first workflow surface for mobile apps

## Immediate Operational Recommendation

Apply migration `core.0029_erp_foundation_upgrade` before production rollout, create the ERP role groups in admin, assign users to the new roles, and move production data to PostgreSQL if SQLite is still in operational use.
