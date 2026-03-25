# Reconix Workflow Documentation

Comprehensive description of all business processes and operational workflows in the Reconix platform.

---

## 1. SIM Recycling Detection Workflow

### Overview
The Reconciliation Service continuously monitors telecom operator databases to identify recycled SIM cards that retain linkages to the previous owner's NIN or BVN records. This is the foundational workflow that triggers all downstream delink actions.

### Frequency & Scheduling
- **Execution Schedule:** Daily at 02:00 UTC (off-peak hours)
- **Duration:** Typically 2-4 hours depending on data volume
- **Concurrency:** One reconciliation job at a time (prevents database lock contention)

### Inputs
1. **Operator SIM Inventory:** CSV files from telecom operators (MTN, Airtel, Glo, 9mobile)
   - Format: MSISDN, SIM_SERIAL, IMSI, ACTIVATION_DATE, SUBSCRIBER_NAME
   - Delivery: Daily SFTP export from each operator (02:00 UTC)
   - Size: 10-50 million records per operator per day

2. **Historical SIM Registry:** Previous day's recycled_sims table entries
   - Used to identify newly recycled (reactivated) SIMs
   - Tracks linkage history

3. **NIMC API Access:** NIN verification and current linkages
   - Rate limit: 10,000 requests/day per operator
   - Response: Name, gender, DOB, photo, verification status

4. **NIBSS API Access:** BVN verification and bank linkages
   - Rate limit: 5,000 requests/day
   - Response: Account holder name, associated banks

### Process Steps

#### Phase 1: Data Acquisition (30 minutes)
1. Reconciliation Service scheduled trigger fires at 02:00 UTC
2. Connect to each operator SFTP server with credentials from system_config
3. Download daily SIM inventory CSV files
4. Validate file structure and checksum
5. Load CSV into temporary staging table (temp_sim_inventory)
6. Log reconciliation job start with job_uuid

#### Phase 2: Linkage Detection (2-3 hours)
For each MSISDN in the inventory:

1. **Lookup Current Owner:**
   - Query nin_linkages WHERE msisdn AND is_current=TRUE
   - Query bvn_linkages WHERE msisdn AND is_current=TRUE
   - Retrieve previous owner NIN, BVN, activation dates

2. **Compare with New Owner:**
   - Extract current subscriber from operator inventory
   - Compare name, activation date
   - Determine if SIM has been recycled (different person, later activation)

3. **Verify with External APIs:**
   - If old linkage exists:
     - Call NIMC API: Verify NIN still exists and is valid
     - Call NIBSS API: Check for associated bank accounts
     - Store responses with timestamp and verification status

4. **Calculate Risk Score:**
   ```
   risk_score = (
     0.4 * (days_between_deactivation_reactivation < 7 ? 1 : 0) +
     0.3 * (bvn_found_in_system ? 1 : 0) +
     0.2 * (nimc_verification_failed ? 1 : 0) +
     0.1 * (operator_reported_recycled ? 1 : 0)
   )
   ```

5. **Determine Linkage Status:**
   - `active` = Old linkage verified, SIM recycled (HIGH RISK)
   - `orphaned` = Linkage exists but unverified (MEDIUM RISK)
   - `resolved` = Previous delink successful, no current linkage
   - `disputed` = Linkage authenticity challenged

#### Phase 3: Data Persistence (30 minutes)
1. Insert new recycled_sim records:
   ```sql
   INSERT INTO recycled_sims (
     sim_serial_number, msisdn, imsi, operator_id,
     previous_owner_nin, previous_owner_bvn,
     current_subscriber_name,
     linkage_status, cleanup_status,
     risk_score, detection_method, created_at
   ) VALUES (...)
   ON CONFLICT (sim_serial_number) DO UPDATE
   SET updated_at = CURRENT_TIMESTAMP
   ```

2. Create corresponding nin_linkages and bvn_linkages records

3. Publish events to RabbitMQ:
   - Topic: `recycled_sim.detected`
   - Payload: recycled_sim_id, msisdn, nin, bvn, risk_score, operator

4. Update job status in job_execution_logs:
   - Set: status='completed', records_processed, records_succeeded, records_failed
   - Calculate duration_seconds

#### Phase 4: Error Handling
- **API Rate Limit Exceeded:** Queue remaining requests for retry during next cycle
- **Network Timeout:** Retry up to 3 times with exponential backoff (5s, 30s, 60s)
- **Invalid Data:** Log error record, continue with next MSISDN
- **Database Lock:** Implement conflict-free upsert logic, retry insert up to 5 times

### Outputs

1. **Recycled SIM Records:** New recycled_sims entries with detection metadata
2. **Linkage Records:** nin_linkages and bvn_linkages created/updated
3. **Notifications:** Events published to notification service
4. **Reports:** Reconciliation stats logged (email to operations team)

### Monitoring & Alerts

| Condition | Alert Type | Action |
|-----------|-----------|--------|
| Job duration > 6 hours | WARNING | Investigate data volume or performance |
| Error rate > 5% | WARNING | Review invalid data, API issues |
| Job failed to complete | CRITICAL | Manual intervention required |
| Fewer SIMs detected than expected | WARNING | Check operator data exports |
| NIMC API unavailable | WARNING | Use cached data from previous cycle |

---

## 2. Delink Request Workflow

### Overview
When a recycled SIM is detected, a delink request workflow is initiated to systematically remove the old owner's NIN/BVN linkages from the system. The workflow involves multi-stakeholder approvals and coordinated execution across multiple systems.

### High-Level Flow
```
Submitted → Operator Approved → Bank Approved → NIMC Notified → Executed → Completed
```

### Workflow States & Transitions

#### State: SUBMITTED
- **Entry:** Operator user submits delink request via API
- **Data Required:** MSISDN, NIN (optional), BVN (optional), reason/justification
- **Actions:**
  - Validate request: Check SIM exists, linkage exists, not duplicate
  - Create delink_requests record with workflow_status='submitted'
  - Publish event: `delink.request.submitted`
  - Send notification to operator: Confirmation of submission
- **Exit Criteria:** Request created and persisted
- **Next State:** operator_approved (manual approval) or awaiting_bank_approval (if BVN)

#### State: OPERATOR_APPROVED
- **Entry:** Operator manager reviews and approves request
- **Data Required:** Operator approval, optional notes
- **Actions:**
  - Create delink_approvals record: approval_type='operator', status='approved'
  - Update workflow_status → 'operator_approved'
  - Check if bank approval needed:
    - If BVN linkage: Transition to 'awaiting_bank_approval'
    - If NIN only: Transition to 'awaiting_nimc_notification'
  - Send notification to bank (if applicable): "Delink approval pending"
- **Exit Criteria:** Approval recorded, bank notified
- **SLA:** 24 hours from submission

#### State: AWAITING_BANK_APPROVAL
- **Entry:** Bank approval required for BVN delink
- **Data Required:** Bank review, approval decision
- **Actions:**
  - Create delink_approvals record: approval_type='bank'
  - If approved:
    - Update bank_approval_status='approved'
    - Update workflow_status → 'bank_approved'
    - Send notification to NIMC: Delink request approved
  - If rejected:
    - Update bank_approval_status='rejected'
    - Update workflow_status → 'failed'
    - Create rollback record
    - Notify operator: Delink rejected
- **Exit Criteria:** Bank decision recorded
- **SLA:** 48 hours from operator approval

#### State: BANK_APPROVED
- **Entry:** Bank has approved the delink
- **Data Required:** Bank confirmation details
- **Actions:**
  - Update workflow_status → 'awaiting_nimc_notification'
  - Publish event: `delink.bank.approved`
  - Schedule NIMC notification in queue
- **Exit Criteria:** Status updated, NIMC notification queued

#### State: AWAITING_NIMC_NOTIFICATION
- **Entry:** Ready for NIMC notification
- **Data Required:** NIMC API credentials, NIN, request context
- **Actions:**
  - Call NIMC API: POST /delink-request with NIN, MSISDN, operator, justification
  - Store NIMC response: nimc_reference_id, nimc_notified_at
  - Update nimc_notification_status='notified'
  - Update workflow_status → 'execution_in_progress'
  - Publish event: `delink.nimc.notified`
  - Retry logic: 3 attempts with 5-minute intervals if NIMC unavailable
- **Exit Criteria:** NIMC notified and acknowledged
- **SLA:** 2 hours from bank approval

#### State: EXECUTION_IN_PROGRESS
- **Entry:** Ready to execute actual delink
- **Data Required:** Bank API credentials, account details
- **Actions:**
  1. **NIN Delink (if applicable):**
     - Call bank API: DELETE /linkages/nin/{nin}/msisdn/{msisdn}
     - Verify deletion in bank system
     - Update nin_linkages: is_current=FALSE, deleted_at=CURRENT_TIMESTAMP
     - Log audit entry: action='delete', resource_type='nin_linkages'

  2. **BVN Delink (if applicable):**
     - Call bank API: DELETE /linkages/bvn/{bvn}/msisdn/{msisdn}
     - Verify deletion confirmed
     - Update bvn_linkages: is_current=FALSE, deleted_at=CURRENT_TIMESTAMP
     - Log audit entry: action='delete', resource_type='bvn_linkages'

  3. **Consistency Check:**
     - Verify no active linkages remain for MSISDN-NIN-BVN combination
     - Check in both local DB and external systems
     - Handle partial failures: Only mark as failed if core linkage not deleted

  4. **Update Records:**
     - Update recycled_sims: linkage_status='resolved', cleanup_status='completed'
     - Update delink_requests: execution_status='completed', is_successful=TRUE
     - Update workflow_status → 'completed'
     - Publish event: `delink.completed`

- **Error Handling:**
  - If bank API call fails:
    - Retry up to 3 times (exponential backoff)
    - If still failing, set execution_status='failed', queue for manual review
    - Publish event: `delink.failed`
  - Rollback logic: If delink partially successful, create compensating transaction

- **Exit Criteria:** Delinks executed and verified
- **SLA:** 1 hour from NIMC notification

#### State: COMPLETED
- **Entry:** Delink successfully executed
- **Duration:** Terminal state
- **Actions:**
  - Send final notification to operator: "Delink completed"
  - Update recycled_sims: cleanup_status='completed'
  - Create audit log: event_type='delink_executed', action_result='success'
  - Archive notification history

#### State: FAILED
- **Entry:** Delink execution failed after retries
- **Actions:**
  - Update workflow_status → 'failed'
  - Store error_message and error_details (JSON)
  - Publish event: `delink.failed`
  - Send notification to operations team: Manual intervention required
  - Create escalation task
- **Recovery:**
  - Manual review by administrator
  - Option 1: Retry delink (workflow_status → 'execution_in_progress')
  - Option 2: Rollback (workflow_status → 'rolled_back')
  - Option 3: Mark as disputed (workflow_status → 'disputed')

### Delink Request API Endpoint

**POST /api/v1/delink-requests**

```json
{
  "msisdn": "08012345678",
  "nin": "12345678901",
  "bvn": "98765432101",
  "operator_id": 1,
  "reason": "Recycled SIM detected with orphaned linkages",
  "requested_by": "operator_user_id"
}
```

**Response:**
```json
{
  "request_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "status": "submitted",
  "created_at": "2024-03-22T10:30:00Z",
  "estimated_completion": "2024-03-24T10:30:00Z"
}
```

### Monitoring & SLA

| Phase | SLA | Escalation |
|-------|-----|-----------|
| Submission to Operator Approval | 24 hours | Notify operator manager |
| Operator Approval to Bank Approval | 48 hours | Notify bank head office |
| NIMC Notification | 2 hours | Retry with manual escalation |
| Execution | 1 hour | Manual intervention |
| Total Workflow | 96 hours | Director review |

---

## 3. Multi-Channel Notification Workflow

### Overview
The Notification Service handles delivery of messages across SMS, Email, Push Notification, and In-app channels to inform stakeholders of recycled SIM detection and delink status.

### Notification Types

| Event | Channel | Recipient | Template |
|-------|---------|-----------|----------|
| SIM Recycled Detected | SMS | Previous owner | recycled_sim_detection |
| SIM Recycled Detected | Email | Operator | recycled_sim_detection_email |
| Delink Initiated | Email | Bank | delink_approval_pending |
| Delink Completed | SMS | Operator | delink_completed |
| Delink Failed | Email | Operations Team | delink_failed |

### Workflow Steps

#### 1. Event Reception
- Subscribe to RabbitMQ topics:
  - `recycled_sim.detected` → Trigger SIM detection notifications
  - `delink.*.event` → Trigger delink status notifications
  - `notification.*.requested` → Trigger manual notifications

#### 2. Template Rendering
```
1. Fetch template from notification_templates
2. Render variables:
   - {{MSISDN}} = "08012345678"
   - {{NIN}} = "120****1234" (masked)
   - {{BVN}} = "119****8765" (masked)
   - {{OWNER_NAME}} = "John Doe"
   - {{BANK_NAME}} = "Guaranty Trust Bank"
   - {{REQUEST_ID}} = "550e8400-e29b..."
3. Apply channel-specific formatting:
   - SMS: Truncate to 160 chars, remove HTML
   - Email: Format as HTML with logo/styling
   - Push: Limit to 240 chars, add emoji
4. Substitute variables and validate
```

#### 3. Recipient Resolution
- **SMS:** Use phonenumber from previous_owner_phone or recipient_msisdn
- **Email:** Use contact_email from users/operators/banks tables
- **Push:** Use device_token from user preferences
- **In-app:** Post to user's notification inbox

#### 4. Delivery Execution

**SMS Flow:**
```
1. Validate MSISDN format
2. Connect to SMS gateway (AWS SNS or Twilio)
3. Send message with MessageAttribute tags (operator, sim_id)
4. Receive delivery receipt (queued, sent, failed)
5. Store delivery_timestamp and provider_response
6. Set delivery_status accordingly
```

**Email Flow:**
```
1. Validate email address format
2. Connect to email provider (SendGrid or SES)
3. Send email with tracking pixel
4. Receive delivery confirmation
5. Store delivery timestamp
6. Monitor bounce/complaint webhooks
```

**Push Notification Flow:**
```
1. Resolve device token from user preferences
2. Connect to push service (Firebase Cloud Messaging)
3. Send notification with metadata
4. Receive delivery confirmation
5. Track engagement (open, click-through)
```

#### 5. Delivery Tracking & Retry

```
Initial Attempt (T=0):
- Send notification
- Wait 5 minutes for delivery receipt
- If no receipt: Set next_retry_at = T+5min

Retry 1 (T+5min):
- Resend notification
- If failed: next_retry_at = T+35min (30 min wait)

Retry 2 (T+35min):
- Resend
- If failed: next_retry_at = T+95min (60 min wait)

Retry 3 (T+95min):
- Resend
- If failed: next_retry_at = T+215min (120 min wait)

Retry 4 (T+215min):
- Final attempt
- If failed: Mark as delivery_status='failed'
- Alert operations team
```

#### 6. Delivery Status Update

| Status | Meaning | Next Action |
|--------|---------|------------|
| pending | Queued, not yet sent | Wait for send attempt |
| sent | Sent to provider | Wait for delivery receipt |
| delivered | Confirmed delivered to recipient | None (success) |
| failed | Failed after all retries | Manual escalation |
| bounced | Email bounced (invalid address) | Remove from contact list |
| read | Recipient opened/read message | Analytics tracking |

#### 7. Error Handling

**Provider Errors:**
- 4xx Errors (rate limit, invalid address): Don't retry same recipient
- 5xx Errors (provider down): Retry with exponential backoff
- Timeout: Retry after 5 minutes

**Data Validation Errors:**
- Invalid phone number: Don't attempt send, log error
- Missing email: Query from alternative source, retry
- Unknown recipient_type: Log audit event, skip notification

### Monitoring & Metrics

```
SMS Delivery:
- Delivery success rate: Target >95%
- Average delivery time: <30 seconds
- Cost per message: ~₦0.50 per SMS

Email Delivery:
- Delivery success rate: Target >98%
- Average delivery time: <5 minutes
- Bounce rate: Target <1%

Push Notifications:
- Delivery success rate: Target >90%
- Average delivery time: <2 seconds
- Open rate target: >30%
```

---

## 4. Bulk CSV Upload & Processing Workflow

### Overview
The Admin Dashboard supports bulk import of recycled SIM data via CSV file upload. The system validates, processes, and reconciles the data asynchronously while providing real-time progress updates.

### File Format

**CSV Header:**
```
MSISDN,SIM_SERIAL,IMSI,OPERATOR,PREVIOUS_NIN,PREVIOUS_NAME,PREVIOUS_BVN,ACTIVATION_DATE,DEACTIVATION_DATE
```

**Example Rows:**
```
08012345678,8923405555000000123,627010145678901234,MTN,12345678901,JOHN DOE,98765432101,2023-01-15,2024-01-10
08098765432,8923405555000000456,627010145678901567,AIRTEL,11111222223,JANE SMITH,88888777776,2023-02-20,2024-02-18
```

### Upload Workflow

#### Phase 1: Client-Side Upload (5-10 minutes)
1. User selects CSV file via file picker
2. Client validates:
   - File size < 100MB
   - MIME type = text/csv
   - Row count displayed in preview
3. User reviews preview (first 5 rows) for correctness
4. Click "Upload" button

#### Phase 2: Server-Side Ingestion (1-5 minutes)
1. **Receive Upload:**
   - API endpoint: POST /api/v1/bulk/upload
   - Content-Type: multipart/form-data
   - File stored in temp directory: /tmp/upload_xxxxxx.csv

2. **Initial Validation:**
   - Check file size within limits
   - Verify CSV structure (header row)
   - Verify required columns present
   - Check row count

3. **Create Bulk Job Record:**
   ```sql
   INSERT INTO bulk_import_jobs (
     job_uuid, file_path, file_size, row_count,
     status, initiated_by_user_id
   ) VALUES (...)
   ```

4. **Response to Client:**
   - HTTP 202 Accepted (async processing)
   - Return job_uuid and status URL
   - Redirect user to job progress page

5. **Publish Job Event:**
   - Topic: `bulk.import.queued`
   - Payload: job_uuid, file_path, row_count

#### Phase 3: Asynchronous Processing (30 min - 2 hours)
1. **Job Processor Consumes Event:**
   - Download temp file from storage
   - Stream CSV to prevent memory overflow (for large files)

2. **Process Each Row:**
   ```
   FOR EACH ROW in CSV:
     1. Parse fields: MSISDN, SIM_SERIAL, OPERATOR, NIN, BVN, dates
     2. Validate data:
        - MSISDN format check
        - NIN/BVN 11-digit check
        - Operator exists in DB
        - Date format validation
     3. Check for duplicates:
        - SIM_SERIAL already in recycled_sims?
        - MSISDN already linked?
     4. IF validation passes:
        - INSERT into recycled_sims
        - INSERT into nin_linkages (if NIN provided)
        - INSERT into bvn_linkages (if BVN provided)
        - Increment success counter
        - Publish: recycled_sim.detected event
     5. ELSE IF validation fails:
        - Store error record with row number and error message
        - Increment error counter
        - Continue to next row
   ```

3. **Error Recovery:**
   - Collect errors in error_records table (linked to bulk job)
   - Continue processing remaining rows (fail-safe approach)
   - Log validation errors for user review

4. **Completion:**
   - Update bulk_import_jobs: status='completed'
   - Calculate statistics: rows_processed, rows_succeeded, rows_failed
   - Store completion_timestamp

#### Phase 4: Result Notification & UI Update (1 minute)
1. **Generate Results Report:**
   ```
   Bulk Import Job Complete
   ========================
   Job ID: 550e8400-e29b-41d4-a716-446655440000
   File: recycled_sims_2024_03_22.csv

   Summary:
   - Total rows: 50,000
   - Successfully imported: 49,850 (99.7%)
   - Failed: 150 (0.3%)
   - Duration: 45 minutes

   Failures (top 10):
   - Row 152: MSISDN format invalid (08012345)
   - Row 305: Unknown operator (UNKNOWN_OP)
   - Row 1200: NIN already linked to active MSISDN
   ```

2. **Store Results:**
   - Create bulk_import_results record
   - Store report as JSON in system_config

3. **Send Notification to Uploader:**
   - Email with result summary
   - Downloadable error CSV for failed rows
   - Link to detailed results in dashboard

4. **UI Display:**
   - Real-time progress bar updated via WebSocket
   - Final summary displayed with download links
   - Allow download of error report

### Error Handling

| Error Type | Example | Handling |
|-----------|---------|----------|
| Format Error | Invalid MSISDN | Skip row, log error, continue |
| Duplicate | SIM_SERIAL exists | Skip row, log as duplicate |
| FK Error | Unknown operator | Skip row, log invalid operator |
| Conflict | MSISDN already linked | Update existing record or skip |
| Data Error | NIN not 11 digits | Skip row, log validation error |

### Monitoring & Alerts

- **Upload Warning:** File > 50MB (may take > 1 hour)
- **Error Alert:** Error rate > 5% (potential data quality issue)
- **Performance Alert:** Processing time > 3 hours (investigate bottleneck)
- **Job Failure:** If job fails entirely, retry up to 2 times

---

## 5. User & Role Management Workflow

### Overview
Admin users manage system users, assign roles, and control access to sensitive features and data.

### User Provisioning

1. **Create User:**
   - Admin selects: Username, Email, Role, Operator/Bank (if applicable)
   - System generates temporary password
   - User invited via email with password reset link

2. **User Verification:**
   - User clicks link, sets permanent password
   - Verify email (click confirmation link)
   - Optional: Set up MFA (QR code for authenticator app)

3. **Access Control:**
   - Role determines visible features and data
   - Operator users see only own operator's SIMs
   - Bank users see only own bank's BVN linkages
   - Auditors see all data but read-only

### Role Definitions

| Role | Permissions | Data Access |
|------|-----------|------------|
| **Admin** | Create/delete users, configure system, view audit logs | All data |
| **Operator** | Submit delink requests, view own SIMs, manage bulk uploads | Own operator's SIMs |
| **Bank** | Approve delink requests, manage BVN linkages | Own bank's BVN linkages |
| **Auditor** | View audit logs, generate compliance reports | All data (read-only) |
| **API Client** | Programmatic API access via API key | Limited by API key scopes |

---

## 6. Audit & Compliance Workflow

### Overview
All user actions, data modifications, and system events are logged to immutable audit logs for compliance and forensic investigations.

### Audit Logging

**Logged Events:**
1. User login/logout
2. User creation/modification/deletion
3. SIM reconciliation job execution
4. Delink request creation/approval/execution
5. Notification dispatch
6. API key creation/revocation
7. Configuration changes
8. Report generation
9. Bulk data imports

**Audit Entry Structure:**
```json
{
  "audit_uuid": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "delink_approved",
  "actor_user_id": 42,
  "actor_ip_address": "192.168.1.100",
  "resource_type": "delink_requests",
  "resource_id": "123456",
  "action": "update",
  "action_result": "success",
  "old_values": {
    "workflow_status": "awaiting_bank_approval",
    "bank_approval_status": "pending"
  },
  "new_values": {
    "workflow_status": "bank_approved",
    "bank_approval_status": "approved",
    "bank_approved_at": "2024-03-22T14:30:00Z"
  },
  "is_security_relevant": true,
  "severity_level": "info",
  "created_at": "2024-03-22T14:30:00Z"
}
```

### Compliance Reporting

**Monthly Audit Reports:**
- User access patterns
- Delink workflow metrics
- Security events summary
- Data protection compliance status

**Annual Security Audit:**
- Third-party penetration testing
- Code review for vulnerabilities
- Infrastructure security assessment
- Disaster recovery testing

---

## Process Orchestration & Error Recovery

### Job Scheduling

All workflows are orchestrated using background job queues (RabbitMQ) to enable:
- Reliable message delivery
- Retry mechanisms
- Dead letter queues for failed jobs
- Job status tracking and monitoring

### Compensation & Rollback

If a delink execution partially fails:
1. Identify which linkages were successfully deleted
2. Create compensating transaction to restore state
3. Notify bank and operator of partial completion
4. Queue for manual review and resolution

### Disaster Recovery

In case of system failure:
1. Unprocessed jobs remain in queue
2. Processed-but-not-confirmed jobs reprocessed (idempotency key prevents duplicates)
3. Failed jobs moved to dead letter queue
4. Manual review and replay after system recovery

