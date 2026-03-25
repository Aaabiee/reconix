# Reconix Data Dictionary

Complete documentation of all tables, columns, data types, constraints, and business rules for the Reconix platform.

---

## Reference Tables

### OPERATORS

**Purpose:** Stores information about Nigerian telecom operators.

**Table Name:** operators

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | SERIAL | PRIMARY KEY | Unique operator identifier |
| code | VARCHAR(100) | NOT NULL, UNIQUE | Operator code (MTN, AIRTEL, GLO, 9MOBILE) |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Full operator name |
| contact_email | VARCHAR(255) | EMAIL CHECK | Primary contact email address |
| contact_phone | VARCHAR(20) | | Phone number in Nigerian format |
| api_endpoint | VARCHAR(255) | | REST API endpoint for operator integration |
| sftp_host | VARCHAR(255) | | SFTP server hostname for file transfers |
| sftp_port | INTEGER | DEFAULT 22 | SFTP server port |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether operator is active in the system |

**Indexes:**
- idx_operators_code: (code) - Fast lookup by operator code

**Business Rules:**
- Code must be 2-10 alphanumeric characters
- Each operator registered once
- Deactivate operators instead of deleting (referential integrity)

---

### BANKS

**Purpose:** Stores information about Nigerian banks for BVN linkage management.

**Table Name:** banks

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | SERIAL | PRIMARY KEY | Unique bank identifier |
| code | VARCHAR(10) | NOT NULL, UNIQUE | Bank code (e.g., GTB, UBA) |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Full bank name |
| swift_code | VARCHAR(11) | | SWIFT code for international payments |
| contact_email | VARCHAR(255) | EMAIL CHECK | Primary contact email |
| contact_phone | VARCHAR(20) | | Phone number in Nigerian format |
| api_endpoint | VARCHAR(255) | | REST API endpoint for delink execution |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether bank is active in system |

**Indexes:**
- idx_banks_code: (code) - Fast lookup by bank code

---

## User & Authentication Tables

### USERS

**Purpose:** Stores system user accounts with role-based access control.

**Table Name:** users

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | SERIAL | PRIMARY KEY | Unique user identifier |
| username | VARCHAR(100) | NOT NULL, UNIQUE | Login username (3-100 chars) |
| email | VARCHAR(255) | NOT NULL, UNIQUE, EMAIL CHECK | Email address (verified) |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password (min 12 rounds) |
| full_name | VARCHAR(255) | NOT NULL | User's full legal name |
| role | VARCHAR(50) | NOT NULL, ENUM CHECK | User role (admin, operator, bank, auditor, api_client) |
| operator_id | INTEGER | FK to operators(id) | Associated operator (if role='operator') |
| bank_id | INTEGER | FK to banks(id) | Associated bank (if role='bank') |
| phone_number | VARCHAR(20) | PHONE CHECK | Nigerian phone number format |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | User account active status |
| is_verified | BOOLEAN | NOT NULL, DEFAULT FALSE | Email/phone verification status |
| last_login_at | TIMESTAMP WITH TIME ZONE | | Last successful login timestamp |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |
| deleted_at | TIMESTAMP WITH TIME ZONE | | Soft delete timestamp (for audit trail) |

**Indexes:**
- idx_users_username: (username) - Login lookup
- idx_users_email: (email) - Email lookup
- idx_users_role: (role) - Role-based queries
- idx_users_operator_id: (operator_id) WHERE operator_id IS NOT NULL
- idx_users_bank_id: (bank_id) WHERE bank_id IS NOT NULL

**Business Rules:**
- Username must be 3-100 characters, alphanumeric + underscore
- Email must be valid and unique
- Phone number must match Nigerian format: +234XXXXXXXXXX or 0XXXXXXXXXX
- Role determines permissions and accessible resources
- Admin users have no operator_id or bank_id
- Operator users must have operator_id set
- Bank users must have bank_id set
- Use soft delete (deleted_at) to maintain audit trail

**Security:**
- Passwords hashed with bcrypt (minimum 12 rounds, 60-character hash)
- Password field never logged or exported
- Account lockout after 5 failed login attempts (enforced in application)
- MFA required for admin and auditor roles

---

### API_KEYS

**Purpose:** Manages API authentication tokens for machine-to-machine (M2M) integrations.

**Table Name:** api_keys

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | SERIAL | PRIMARY KEY | Unique API key identifier |
| user_id | INTEGER | NOT NULL, FK to users(id) | User who owns the key |
| key_hash | VARCHAR(255) | NOT NULL, UNIQUE | SHA-256 hash of the actual API key |
| key_prefix | VARCHAR(20) | NOT NULL | First 8 chars of key (for UI display) |
| name | VARCHAR(100) | NOT NULL | Friendly name (e.g., "MTN Integration") |
| permissions | JSONB | NOT NULL, DEFAULT [] | Array of permission scopes |
| rate_limit_per_minute | INTEGER | DEFAULT 100, CHECK > 0 | API calls per minute |
| rate_limit_per_day | INTEGER | DEFAULT 10000, CHECK > 0 | API calls per day |
| last_used_at | TIMESTAMP WITH TIME ZONE | | Timestamp of last API call |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether key is valid |
| expires_at | TIMESTAMP WITH TIME ZONE | | Expiration timestamp (if applicable) |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| revoked_at | TIMESTAMP WITH TIME ZONE | | Timestamp when key was revoked |

**Indexes:**
- idx_api_keys_user_id: (user_id) - Lookup by user
- idx_api_keys_key_hash: (key_hash) - Lookup by key hash during validation
- idx_api_keys_active: (is_active) WHERE is_active = TRUE

**Permission Scopes:**
- `recycled_sims:read` - Query recycled SIM records
- `recycled_sims:write` - Create/modify recycled SIM records
- `delink_requests:read` - View delink requests
- `delink_requests:write` - Submit delink requests
- `delink_requests:approve` - Approve delink requests (bank role)
- `notifications:read` - View notification history
- `audit_logs:read` - Access audit logs (admin only)
- `system:admin` - Full system access

**Business Rules:**
- API key hash stored, not the actual key (like passwords)
- Keys expire after 1 year by default (configurable)
- Support key rotation without downtime
- Revoked keys cannot be reactivated (create new key instead)
- Rate limiting per API key tier
- Record last_used_at for monitoring key usage
- Log all API key creation/revocation events

---

## SIM & Linkage Tables

### RECYCLED_SIMS

**Purpose:** Core table tracking detected recycled SIM cards with orphaned NIN/BVN linkages.

**Table Name:** recycled_sims

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique recycled SIM record ID |
| sim_serial_number | VARCHAR(20) | NOT NULL, UNIQUE | SIM card ICCID/serial number |
| msisdn | VARCHAR(15) | NOT NULL | Phone number (10-digit format) |
| imsi | VARCHAR(15) | IMSI CHECK | International Mobile Subscriber Identity |
| operator_id | INTEGER | NOT NULL, FK to operators(id) | Associated operator |
| previous_owner_nin | VARCHAR(11) | NIN CHECK | Previous owner's NIN (11 digits) |
| previous_owner_name | VARCHAR(255) | | Previous owner's full name |
| previous_owner_bvn | VARCHAR(11) | BVN CHECK | Previous owner's BVN (11 digits) |
| activation_date | DATE | | Original activation date |
| deactivation_date | DATE | | Deactivation date of previous owner |
| current_activation_date | DATE | | Reactivation date for current owner |
| current_subscriber_name | VARCHAR(255) | | Current subscriber name |
| linkage_status | VARCHAR(50) | NOT NULL, ENUM CHECK | Status of linkage (active, orphaned, resolved, disputed) |
| cleanup_status | VARCHAR(50) | NOT NULL, ENUM CHECK | Cleanup progress (pending, in_progress, completed, failed) |
| delink_request_id | BIGINT | FK to delink_requests(id) | Associated delink request |
| detection_method | VARCHAR(100) | | How SIM was detected (reconciliation, api_query, operator_report) |
| risk_score | NUMERIC(3,2) | DEFAULT 0.0, CHECK 0-1 | Risk assessment score (0.0 = low, 1.0 = critical) |
| notes | TEXT | | Additional notes/context |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Detection timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

**Indexes:**
- idx_recycled_sims_msisdn: (msisdn) - Fast SIM lookup
- idx_recycled_sims_nin: (previous_owner_nin) WHERE NOT NULL - NIN-based queries
- idx_recycled_sims_bvn: (previous_owner_bvn) WHERE NOT NULL - BVN-based queries
- idx_recycled_sims_operator: (operator_id) - Operator-specific reports
- idx_recycled_sims_status: (linkage_status, cleanup_status) - Status-based filtering
- idx_recycled_sims_created: (created_at DESC) - Recent SIMs

**MSISDN Format:** `^(\+234|0)[0-9]{10}$` (Nigeria format, 11 digits)
**NIN Format:** `^[0-9]{11}$` (National ID, 11 digits)
**BVN Format:** `^[0-9]{11}$` (Bank verification, 11 digits)
**IMSI Format:** `^[0-9]{15}$` (International mobile ID, 15 digits)

**Linkage Status Values:**
- `active` - Recycled SIM with active old linkages
- `orphaned` - SIM has no current active linkages
- `resolved` - Linkages successfully deleted
- `disputed` - Linkage authenticity disputed

**Cleanup Status Values:**
- `pending` - Detected but not yet processed
- `in_progress` - Delink workflow initiated
- `completed` - All linkages successfully removed
- `failed` - Delink failed, requires manual intervention

**Risk Score Interpretation:**
- 0.0-0.3: Low risk (verification issues)
- 0.4-0.6: Medium risk (potential fraud indicator)
- 0.7-0.9: High risk (multiple fraud indicators)
- 1.0: Critical (confirmed high-risk linkage)

---

### NIN_LINKAGES

**Purpose:** Tracks historical and current MSISDN-to-NIN (National ID) linkages.

**Table Name:** nin_linkages

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique linkage record ID |
| msisdn | VARCHAR(15) | NOT NULL | Phone number |
| nin | VARCHAR(11) | NOT NULL, NIN CHECK | National Identification Number |
| owner_name | VARCHAR(255) | | Name registered with NIN |
| owner_phone | VARCHAR(15) | | Backup phone for owner |
| linkage_date | DATE | NOT NULL | Date linkage was established |
| verification_status | VARCHAR(50) | NOT NULL, ENUM CHECK | Verification state (verified, pending, failed, unverified) |
| verification_source | VARCHAR(100) | | Source of verification (NIMC, operator, bank) |
| verified_by_nimc | BOOLEAN | DEFAULT FALSE | Whether NIMC confirmed linkage |
| last_verified_at | TIMESTAMP WITH TIME ZONE | | Most recent verification timestamp |
| is_current | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether this is the active linkage |
| linkage_source | VARCHAR(100) | | Source that reported linkage (operator, bank, NIMC) |
| delink_request_id | BIGINT | FK to delink_requests(id) | Associated delink request |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |
| deleted_at | TIMESTAMP WITH TIME ZONE | | Soft delete timestamp |

**Indexes:**
- idx_nin_linkages_msisdn: (msisdn) - MSISDN lookup
- idx_nin_linkages_nin: (nin) - NIN-based queries
- idx_nin_linkages_current: (msisdn) WHERE is_current = TRUE - Active linkage lookup
- idx_nin_linkages_verified: (verification_status) - Verification state queries

**Unique Constraint:**
- One active linkage per MSISDN-NIN pair (is_current=TRUE, deleted_at IS NULL)

**Verification Status Values:**
- `verified` - Confirmed by authoritative source
- `pending` - Awaiting verification
- `failed` - Failed verification attempt
- `unverified` - Not yet verified

---

### BVN_LINKAGES

**Purpose:** Tracks historical and current MSISDN-to-BVN (Bank Verification Number) linkages.

**Table Name:** bvn_linkages

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique linkage record ID |
| msisdn | VARCHAR(15) | NOT NULL | Phone number |
| bvn | VARCHAR(11) | NOT NULL, BVN CHECK | Bank Verification Number |
| account_holder_name | VARCHAR(255) | | Name registered with bank |
| account_number | VARCHAR(20) | | Bank account number |
| bank_id | INTEGER | FK to banks(id) | Associated bank |
| account_type | VARCHAR(50) | | Account type (savings, current, etc.) |
| linkage_date | DATE | NOT NULL | Date linkage was established |
| verification_status | VARCHAR(50) | NOT NULL, ENUM CHECK | Verification state |
| verification_source | VARCHAR(100) | | Source of verification (NIBSS, bank) |
| verified_by_nibss | BOOLEAN | DEFAULT FALSE | Whether NIBSS confirmed linkage |
| last_verified_at | TIMESTAMP WITH TIME ZONE | | Most recent verification timestamp |
| is_current | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether this is the active linkage |
| linkage_source | VARCHAR(100) | | Source that reported linkage |
| delink_request_id | BIGINT | FK to delink_requests(id) | Associated delink request |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |
| deleted_at | TIMESTAMP WITH TIME ZONE | | Soft delete timestamp |

**Indexes:**
- idx_bvn_linkages_msisdn: (msisdn) - MSISDN lookup
- idx_bvn_linkages_bvn: (bvn) - BVN-based queries
- idx_bvn_linkages_bank: (bank_id) WHERE NOT NULL - Bank-specific queries
- idx_bvn_linkages_current: (msisdn) WHERE is_current = TRUE - Active linkage lookup

**Unique Constraint:**
- One active linkage per MSISDN-BVN pair (is_current=TRUE, deleted_at IS NULL)

---

## Delink Workflow Tables

### DELINK_REQUESTS

**Purpose:** Central workflow table tracking the complete lifecycle of delink operations.

**Table Name:** delink_requests

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique delink request ID |
| request_uuid | UUID | NOT NULL, UNIQUE | Public UUID for external reference |
| recycled_sim_id | BIGINT | FK to recycled_sims(id) | Detected recycled SIM record |
| msisdn | VARCHAR(15) | NOT NULL, MSISDN CHECK | Phone number to delink |
| nin | VARCHAR(11) | NIN CHECK | NIN to delink (if applicable) |
| bvn | VARCHAR(11) | BVN CHECK | BVN to delink (if applicable) |
| operator_id | INTEGER | NOT NULL, FK to operators(id) | Operator managing the SIM |
| requested_by_user_id | INTEGER | NOT NULL, FK to users(id) | User who initiated request |
| requested_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Request submission timestamp |
| workflow_status | VARCHAR(50) | NOT NULL, ENUM CHECK | Overall workflow state |
| operator_approval_status | VARCHAR(50) | DEFAULT pending | Operator sign-off state |
| bank_approval_status | VARCHAR(50) | DEFAULT pending | Bank approval state |
| bank_id | INTEGER | FK to banks(id) | Associated bank (if BVN delink) |
| bank_approved_by_user_id | INTEGER | FK to users(id) | Bank representative who approved |
| bank_approved_at | TIMESTAMP WITH TIME ZONE | | Bank approval timestamp |
| nimc_notification_status | VARCHAR(50) | DEFAULT pending | NIMC notification state |
| nimc_reference_id | VARCHAR(50) | | NIMC's reference ID for this delink |
| nimc_notified_at | TIMESTAMP WITH TIME ZONE | | NIMC notification timestamp |
| execution_status | VARCHAR(50) | DEFAULT pending | Delink execution state |
| execution_timestamp | TIMESTAMP WITH TIME ZONE | | When delink was executed |
| executed_by_system_component | VARCHAR(100) | | Component that executed delink |
| completion_timestamp | TIMESTAMP WITH TIME ZONE | | Final completion timestamp |
| is_successful | BOOLEAN | | Success/failure indicator |
| error_message | TEXT | | Human-readable error description |
| error_details | JSONB | | JSON details of error (stack trace, codes) |
| retry_count | INTEGER | DEFAULT 0 | Number of execution retries |
| max_retries | INTEGER | DEFAULT 3 | Maximum allowed retries |
| next_retry_at | TIMESTAMP WITH TIME ZONE | | Scheduled retry timestamp |
| rollback_status | VARCHAR(50) | | Rollback state if needed |
| rollback_reason | TEXT | | Reason for rollback |
| delink_method | VARCHAR(100) | | Method used (api_call, manual_update, etc.) |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Indexes:**
- idx_delink_requests_uuid: (request_uuid) - External reference lookup
- idx_delink_requests_msisdn: (msisdn) - MSISDN-based queries
- idx_delink_requests_status: (workflow_status) - Status filtering
- idx_delink_requests_operator: (operator_id) - Operator-specific requests
- idx_delink_requests_created: (created_at DESC) - Recent requests
- idx_delink_requests_sim: (recycled_sim_id) - SIM-related requests

**Workflow Status Progression:**
```
submitted
  ↓
operator_approved (or rejected)
  ↓
awaiting_bank_approval (if BVN)
  ↓
bank_approved (or rejected)
  ↓
awaiting_nimc_notification
  ↓
execution_in_progress
  ↓
completed (or failed, rolled_back, disputed)
```

**Approval Status Values:**
- `pending` - Awaiting action
- `approved` - Approved by stakeholder
- `rejected` - Rejected by stakeholder
- `escalated` - Escalated for manual review

**Execution Status Values:**
- `pending` - Scheduled but not executed
- `in_progress` - Currently executing
- `completed` - Execution finished
- `failed` - Execution encountered error

**Constraint:** At least one of NIN or BVN must be specified

---

### DELINK_APPROVALS

**Purpose:** Tracks approval chain and history for each delink request.

**Table Name:** delink_approvals

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique approval record ID |
| delink_request_id | BIGINT | NOT NULL, FK to delink_requests(id) | Associated delink request |
| approval_type | VARCHAR(50) | NOT NULL, ENUM CHECK | Approval level (operator, bank, nimc) |
| approver_user_id | INTEGER | FK to users(id) | User who approved/rejected |
| approved_at | TIMESTAMP WITH TIME ZONE | | Approval action timestamp |
| approval_status | VARCHAR(50) | NOT NULL, ENUM CHECK | Approval result |
| approval_notes | TEXT | | Notes or justification |
| approval_ip_address | INET | | IP address of approver |
| approval_method | VARCHAR(50) | | How approval was given (api, web, sms) |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Indexes:**
- idx_delink_approvals_request: (delink_request_id) - Request approval history
- idx_delink_approvals_type: (approval_type) - Approval level queries
- idx_delink_approvals_status: (approval_status) - Status filtering

**Approval Type Values:**
- `operator` - Telecom operator sign-off
- `bank` - Bank confirmation (for BVN delinks)
- `nimc` - NIMC notification/confirmation

---

## Notification Tables

### NOTIFICATION_TEMPLATES

**Purpose:** Stores message templates for multi-channel notifications.

**Table Name:** notification_templates

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | SERIAL | PRIMARY KEY | Unique template ID |
| template_key | VARCHAR(100) | NOT NULL, UNIQUE | System identifier (e.g., "recycled_sim_detected") |
| template_name | VARCHAR(255) | NOT NULL | Human-readable name |
| channel | VARCHAR(50) | NOT NULL, ENUM CHECK | Channel type (sms, email, push_notification, in_app) |
| subject | VARCHAR(255) | | Email subject (email channel only) |
| message_body | TEXT | NOT NULL | Template body with {{VARIABLE}} placeholders |
| variables | JSONB | ARRAY CHECK | Array of variable names in template |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether template is in use |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Default Templates:**
- `recycled_sim_detection` (SMS)
- `recycled_sim_detection_email` (Email)
- `delink_completed` (SMS)
- `delink_failed` (SMS)
- `delink_approval_pending` (Email)

**Template Variables:**
- `{{MSISDN}}` - Phone number
- `{{NIN}}` - National ID
- `{{BVN}}` - Bank verification number
- `{{OWNER_NAME}}` - Previous owner name
- `{{BANK_NAME}}` - Bank name
- `{{REQUEST_ID}}` - Delink request ID
- `{{OPERATOR_NAME}}` - Operator name
- `{{APPROVAL_DEADLINE}}` - Approval deadline date

---

### NOTIFICATIONS

**Purpose:** Tracks all notification dispatch attempts across all channels.

**Table Name:** notifications

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique notification ID |
| notification_uuid | UUID | NOT NULL, UNIQUE | Public UUID for reference |
| template_id | INTEGER | NOT NULL, FK to notification_templates(id) | Template used |
| delink_request_id | BIGINT | FK to delink_requests(id) | Associated delink request |
| recycled_sim_id | BIGINT | FK to recycled_sims(id) | Associated recycled SIM |
| recipient_type | VARCHAR(50) | NOT NULL, ENUM CHECK | Recipient category |
| recipient_identifier | VARCHAR(255) | NOT NULL | Unique recipient ID/contact |
| recipient_name | VARCHAR(255) | | Recipient name |
| recipient_msisdn | VARCHAR(15) | | Phone number (SMS channel) |
| recipient_email | VARCHAR(255) | | Email address (Email channel) |
| recipient_nin | VARCHAR(11) | | NIN (if applicable) |
| channel | VARCHAR(50) | NOT NULL, ENUM CHECK | Notification channel |
| rendered_subject | VARCHAR(255) | | Final subject with substituted variables |
| rendered_message | TEXT | NOT NULL | Final message with substituted variables |
| delivery_status | VARCHAR(50) | NOT NULL, ENUM CHECK | Delivery state |
| delivery_timestamp | TIMESTAMP WITH TIME ZONE | | When message was delivered |
| read_timestamp | TIMESTAMP WITH TIME ZONE | | When recipient read message |
| retry_count | INTEGER | DEFAULT 0 | Number of retry attempts |
| max_retries | INTEGER | DEFAULT 5 | Maximum retries allowed |
| next_retry_at | TIMESTAMP WITH TIME ZONE | | Next scheduled retry |
| error_message | TEXT | | Error description if failed |
| provider_response | JSONB | | Response from SMS/Email provider |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Indexes:**
- idx_notifications_uuid: (notification_uuid) - External reference
- idx_notifications_delink: (delink_request_id) - Delink-related notifications
- idx_notifications_status: (delivery_status) - Status filtering
- idx_notifications_recipient: (recipient_identifier) - Recipient lookup
- idx_notifications_channel: (channel) - Channel-specific queries
- idx_notifications_created: (created_at DESC) - Recent notifications

**Recipient Type Values:**
- `end_user` - Affected individual
- `operator` - Telecom operator
- `bank` - Bank representative
- `nimc` - NIMC notification
- `auditor` - System auditor

**Delivery Status Values:**
- `pending` - Queued for dispatch
- `sent` - Successfully sent
- `delivered` - Confirmed delivery
- `failed` - Failed to send
- `bounced` - Bounced by provider
- `read` - Recipient read notification

**Retry Strategy:**
- Initial retry after 5 minutes
- Exponential backoff: retry_interval = 300 * (2 ^ retry_count) seconds
- Max 5 retries over ~10 hours

---

## Audit & Compliance Tables

### AUDIT_LOGS

**Purpose:** Immutable append-only audit trail of all system actions for compliance and forensics.

**Table Name:** audit_logs

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique audit log entry ID |
| audit_uuid | UUID | NOT NULL, UNIQUE | Immutable UUID for reference |
| event_type | VARCHAR(100) | NOT NULL, ENUM CHECK | Type of event |
| actor_user_id | INTEGER | FK to users(id) | User who performed action (if applicable) |
| actor_ip_address | INET | | IP address of actor |
| actor_user_agent | TEXT | | Browser/client user agent |
| resource_type | VARCHAR(100) | NOT NULL, ENUM CHECK | Type of resource modified |
| resource_id | VARCHAR(100) | | ID of modified resource |
| action | VARCHAR(50) | NOT NULL, ENUM CHECK | Action type |
| action_result | VARCHAR(50) | NOT NULL, ENUM CHECK | Result of action |
| old_values | JSONB | | Previous state (JSON diff) |
| new_values | JSONB | | New state (JSON diff) |
| changes_hash | VARCHAR(64) | | SHA-256 hash of changes for integrity |
| details | JSONB | | Additional context (error codes, etc.) |
| is_security_relevant | BOOLEAN | DEFAULT FALSE | Whether this is a security event |
| severity_level | VARCHAR(50) | DEFAULT info | Event severity |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Event timestamp |

**Indexes:**
- idx_audit_logs_uuid: (audit_uuid) - Immutable reference
- idx_audit_logs_event: (event_type) - Event type queries
- idx_audit_logs_actor: (actor_user_id) - User activity tracking
- idx_audit_logs_resource: (resource_type, resource_id) - Resource change tracking
- idx_audit_logs_created: (created_at DESC) - Chronological queries
- idx_audit_logs_security: (is_security_relevant) WHERE TRUE - Security event filtering

**Immutability:**
- Trigger prevents UPDATE or DELETE on audit_logs table
- Enforced at database level
- All changes logged to secondary immutable store

**Event Types:**
- `user_login`, `user_logout`, `user_created`, `user_modified`, `user_deleted`
- `sim_detected`, `delink_requested`, `delink_approved`, `delink_executed`, `delink_failed`
- `notification_sent`, `notification_failed`
- `api_key_created`, `api_key_revoked`
- `configuration_changed`, `system_event`

**Resource Types:**
- `user`, `recycled_sim`, `delink_request`, `notification`, `api_key`, `system`

**Action Values:**
- `create` - New resource created
- `read` - Resource accessed/queried
- `update` - Resource modified
- `delete` - Resource deleted
- `execute` - Special action (delink execution)

**Result Values:**
- `success` - Action completed successfully
- `failure` - Action failed
- `partial` - Partial success (some sub-actions failed)

**Severity Levels:**
- `info` - Informational, normal operation
- `warning` - Unusual but non-critical
- `error` - Error condition requiring investigation
- `critical` - Security incident or data integrity issue

**JSON Diff Format:**
```json
{
  "field_name": {
    "old": "previous_value",
    "new": "new_value"
  }
}
```

---

## Configuration & Monitoring Tables

### SYSTEM_CONFIG

**Purpose:** Centralized key-value configuration store for system parameters.

**Table Name:** system_config

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | SERIAL | PRIMARY KEY | Unique config ID |
| config_key | VARCHAR(100) | NOT NULL, UNIQUE | Configuration parameter name |
| config_value | TEXT | | Configuration value |
| value_type | VARCHAR(50) | ENUM CHECK | Data type (string, integer, boolean, json) |
| description | TEXT | | Documentation of what this config does |
| is_secret | BOOLEAN | DEFAULT FALSE | Whether value is sensitive (encrypted in transit) |
| is_mutable | BOOLEAN | DEFAULT TRUE | Whether can be changed at runtime |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last modification timestamp |

**Standard Configuration Keys:**
- `max_delink_approvals_days` (integer) - Days allowed for approval workflow
- `reconciliation_schedule_utc` (string) - Daily reconciliation time
- `notification_retry_max_attempts` (integer) - Notification retry limit
- `audit_log_retention_years` (integer) - Audit log retention period
- `api_rate_limit_standard` (integer) - Standard API rate limit
- `enable_delink_auto_execution` (boolean) - Auto-execute delinks

---

### API_REQUEST_LOGS

**Purpose:** Detailed logging of all API requests for monitoring and debugging.

**Table Name:** api_request_logs

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique request log ID |
| request_uuid | UUID | NOT NULL | Unique request identifier |
| user_id | INTEGER | FK to users(id) | User making request (if authenticated) |
| api_key_id | INTEGER | FK to api_keys(id) | API key used (if M2M) |
| http_method | VARCHAR(10) | NOT NULL, ENUM CHECK | HTTP method (GET, POST, etc.) |
| endpoint_path | VARCHAR(500) | NOT NULL | Request path (/api/v1/recycled-sims) |
| query_parameters | JSONB | | Query string parameters |
| request_body_hash | VARCHAR(64) | | SHA-256 hash of request body |
| response_status_code | SMALLINT | NOT NULL | HTTP response code |
| response_time_ms | INTEGER | NOT NULL | Request latency in milliseconds |
| error_message | TEXT | | Error message (if 4xx/5xx) |
| ip_address | INET | NOT NULL | Client IP address |
| user_agent | TEXT | | User-Agent header |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Request timestamp |

**Indexes:**
- idx_api_request_logs_user: (user_id) - User activity
- idx_api_request_logs_endpoint: (endpoint_path) - Endpoint usage
- idx_api_request_logs_status: (response_status_code) - Error tracking
- idx_api_request_logs_created: (created_at DESC) - Recent requests
- idx_api_request_logs_retention: (created_at) WHERE > 30 days ago - Old log cleanup

**Retention Policy:** 30 days (rolling window for performance)

---

### JOB_EXECUTION_LOGS

**Purpose:** Tracks background job execution for async operations.

**Table Name:** job_execution_logs

| Column | Type | Constraints | Description |
|--------|------|-----------|-------------|
| id | BIGSERIAL | PRIMARY KEY | Unique job log ID |
| job_name | VARCHAR(100) | NOT NULL | Job identifier |
| job_uuid | UUID | NOT NULL | Unique job execution ID |
| job_type | VARCHAR(50) | NOT NULL, ENUM CHECK | Job category |
| status | VARCHAR(50) | NOT NULL, ENUM CHECK | Execution status |
| started_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Start time |
| completed_at | TIMESTAMP WITH TIME ZONE | | Completion time |
| duration_seconds | NUMERIC(10,2) | | Execution duration |
| records_processed | INTEGER | | Total records processed |
| records_succeeded | INTEGER | | Successfully processed records |
| records_failed | INTEGER | | Failed record count |
| error_message | TEXT | | Error description (if failed) |
| error_details | JSONB | | Detailed error info |
| retry_count | INTEGER | DEFAULT 0 | Retry attempts |
| next_retry_at | TIMESTAMP WITH TIME ZONE | | Next scheduled retry |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Log creation timestamp |

**Job Types:**
- `reconciliation` - SIM reconciliation
- `delink` - Delink workflow execution
- `notification` - Notification dispatch
- `reporting` - Report generation
- `cleanup` - Data cleanup/archival

**Status Values:**
- `pending` - Queued for execution
- `running` - Currently executing
- `completed` - Successful completion
- `failed` - Failed with error
- `partial_failure` - Some records failed

---

## Views for Reporting

### active_recycled_sims
Lists current active recycled SIMs (orphaned linkages not yet resolved).

### pending_delink_requests
Lists delink requests in progress with approval status and age.

### notification_delivery_status
Summary statistics on notification delivery by channel and status.

### audit_log_security_events
Filtered view of security-relevant audit events for compliance reporting.

---

## Database Constraints Summary

| Constraint Type | Count | Examples |
|-----------------|-------|----------|
| Foreign Keys | 30+ | users.operator_id → operators.id |
| Unique Indexes | 15+ | users(email), api_keys(key_hash) |
| Check Constraints | 35+ | users.role IN (...), msisdn regex |
| NOT NULL | 200+ | All critical fields |
| DEFAULT | 50+ | created_at, is_active |
| Triggers | 1 | audit_logs immutability |

---

## Performance Recommendations

### Query Optimization
- Use indexed fields in WHERE clauses (msisdn, nin, operator_id)
- Filter by status to reduce result sets
- Use LIMIT/OFFSET for pagination
- Consider table partitioning by date for large history tables

### Indexing Strategy
- Composite indexes for multi-field searches
- Partial indexes for status-based queries
- Regular ANALYZE to update statistics
- Monitor index usage with pg_stat_user_indexes

### Connection Pooling
- Use PgBouncer with 1,000 connection limit
- Application-level pooling in Node.js (10-20 pools)
- Monitor active connections and query queue depth

---

## Data Privacy & Compliance

### PII Handling
- NIN and BVN considered highly sensitive PII
- Encrypt at column level using pgcrypto
- Never include in logs or exports without redaction
- Mask in UI with truncation or hash

### Data Retention
- Active records: Retain indefinitely
- Audit logs: 7 years (per NDPR)
- API request logs: 30 days (rolling)
- Deleted user data: Soft-delete + 90 days purge window

### Access Control
- Role-based access at application level
- Database roles for coarse-grained access
- All user actions logged to audit_logs
- API key permissions granular (scopes)

