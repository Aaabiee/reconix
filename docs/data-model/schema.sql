-- Reconix Database Schema (PostgreSQL 14+)
-- National-scale identity reconciliation platform for Nigeria
-- Detects recycled SIM cards linked to old NIN/BVN records

-- ============================================================================
-- REFERENCE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS operators (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL UNIQUE,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    api_endpoint VARCHAR(255),
    sftp_host VARCHAR(255),
    sftp_port INTEGER DEFAULT 22,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT valid_code CHECK (code ~ '^[A-Z0-9]{2,10}$'),
    CONSTRAINT valid_email CHECK (contact_email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);
CREATE INDEX idx_operators_code ON operators(code);

INSERT INTO operators (code, name, contact_email, contact_phone) VALUES
    ('MTN', 'MTN Nigeria Communications Limited', 'api@mtn.com.ng', '+234-1-222-7777'),
    ('AIRTEL', 'Airtel Networks Limited', 'api@airtel.com.ng', '+234-1-633-1111'),
    ('GLO', 'Globacom Limited', 'api@glo.com.ng', '+234-1-279-6000'),
    ('9MOBILE', '9mobile Telecom Limited', 'api@9mobile.com.ng', '+234-1-902-9000')
ON CONFLICT (code) DO NOTHING;

CREATE TABLE IF NOT EXISTS banks (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL UNIQUE,
    swift_code VARCHAR(11),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    api_endpoint VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT valid_code CHECK (code ~ '^[A-Z0-9]{3,10}$'),
    CONSTRAINT valid_email CHECK (contact_email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);
CREATE INDEX idx_banks_code ON banks(code);

-- ============================================================================
-- USER & AUTHENTICATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    operator_id INTEGER REFERENCES operators(id),
    bank_id INTEGER REFERENCES banks(id),
    phone_number VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_role CHECK (role IN ('admin', 'operator', 'bank', 'auditor', 'api_client')),
    CONSTRAINT valid_email CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'),
    CONSTRAINT valid_phone CHECK (phone_number ~ '^(\+234|0)[0-9]{10}$' OR phone_number IS NULL)
);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_operator_id ON users(operator_id) WHERE operator_id IS NOT NULL;
CREATE INDEX idx_users_bank_id ON users(bank_id) WHERE bank_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    rate_limit_per_minute INTEGER DEFAULT 100,
    rate_limit_per_day INTEGER DEFAULT 10000,
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_permissions CHECK (jsonb_typeof(permissions) = 'array'),
    CONSTRAINT valid_rate_limits CHECK (rate_limit_per_minute > 0 AND rate_limit_per_day > 0)
);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- SIM & LINKAGE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS recycled_sims (
    id BIGSERIAL PRIMARY KEY,
    sim_serial_number VARCHAR(20) NOT NULL UNIQUE,
    msisdn VARCHAR(15) NOT NULL,
    imsi VARCHAR(15),
    operator_id INTEGER NOT NULL REFERENCES operators(id),
    previous_owner_nin VARCHAR(11),
    previous_owner_name VARCHAR(255),
    previous_owner_bvn VARCHAR(11),
    activation_date DATE,
    deactivation_date DATE,
    current_activation_date DATE,
    current_subscriber_name VARCHAR(255),
    linkage_status VARCHAR(50) NOT NULL,
    cleanup_status VARCHAR(50) NOT NULL,
    delink_request_id BIGINT,
    detection_method VARCHAR(100),
    risk_score NUMERIC(3,2) DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_msisdn CHECK (msisdn ~ '^(\+234|0)[0-9]{10}$'),
    CONSTRAINT valid_imsi CHECK (imsi ~ '^[0-9]{15}$' OR imsi IS NULL),
    CONSTRAINT valid_nin CHECK (previous_owner_nin ~ '^[0-9]{11}$' OR previous_owner_nin IS NULL),
    CONSTRAINT valid_bvn CHECK (previous_owner_bvn ~ '^[0-9]{11}$' OR previous_owner_bvn IS NULL),
    CONSTRAINT valid_linkage_status CHECK (linkage_status IN ('active', 'orphaned', 'resolved', 'disputed')),
    CONSTRAINT valid_cleanup_status CHECK (cleanup_status IN ('pending', 'in_progress', 'completed', 'failed')),
    CONSTRAINT valid_risk_score CHECK (risk_score >= 0 AND risk_score <= 1)
);
CREATE INDEX idx_recycled_sims_msisdn ON recycled_sims(msisdn);
CREATE INDEX idx_recycled_sims_nin ON recycled_sims(previous_owner_nin) WHERE previous_owner_nin IS NOT NULL;
CREATE INDEX idx_recycled_sims_bvn ON recycled_sims(previous_owner_bvn) WHERE previous_owner_bvn IS NOT NULL;
CREATE INDEX idx_recycled_sims_operator ON recycled_sims(operator_id);
CREATE INDEX idx_recycled_sims_status ON recycled_sims(linkage_status, cleanup_status);
CREATE INDEX idx_recycled_sims_created ON recycled_sims(created_at DESC);

CREATE TABLE IF NOT EXISTS nin_linkages (
    id BIGSERIAL PRIMARY KEY,
    msisdn VARCHAR(15) NOT NULL,
    nin VARCHAR(11) NOT NULL,
    owner_name VARCHAR(255),
    owner_phone VARCHAR(15),
    linkage_date DATE NOT NULL,
    verification_status VARCHAR(50) NOT NULL,
    verification_source VARCHAR(100),
    verified_by_nimc BOOLEAN DEFAULT FALSE,
    last_verified_at TIMESTAMP WITH TIME ZONE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    linkage_source VARCHAR(100),
    delink_request_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_msisdn CHECK (msisdn ~ '^(\+234|0)[0-9]{10}$'),
    CONSTRAINT valid_nin CHECK (nin ~ '^[0-9]{11}$'),
    CONSTRAINT valid_verification CHECK (verification_status IN ('verified', 'pending', 'failed', 'unverified')),
    CONSTRAINT unique_active_linkage UNIQUE (msisdn, nin) WHERE is_current = TRUE AND deleted_at IS NULL
);
CREATE INDEX idx_nin_linkages_msisdn ON nin_linkages(msisdn);
CREATE INDEX idx_nin_linkages_nin ON nin_linkages(nin);
CREATE INDEX idx_nin_linkages_current ON nin_linkages(msisdn) WHERE is_current = TRUE;
CREATE INDEX idx_nin_linkages_verified ON nin_linkages(verification_status);

CREATE TABLE IF NOT EXISTS bvn_linkages (
    id BIGSERIAL PRIMARY KEY,
    msisdn VARCHAR(15) NOT NULL,
    bvn VARCHAR(11) NOT NULL,
    account_holder_name VARCHAR(255),
    account_number VARCHAR(20),
    bank_id INTEGER REFERENCES banks(id),
    account_type VARCHAR(50),
    linkage_date DATE NOT NULL,
    verification_status VARCHAR(50) NOT NULL,
    verification_source VARCHAR(100),
    verified_by_nibss BOOLEAN DEFAULT FALSE,
    last_verified_at TIMESTAMP WITH TIME ZONE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    linkage_source VARCHAR(100),
    delink_request_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_msisdn CHECK (msisdn ~ '^(\+234|0)[0-9]{10}$'),
    CONSTRAINT valid_bvn CHECK (bvn ~ '^[0-9]{11}$'),
    CONSTRAINT valid_verification CHECK (verification_status IN ('verified', 'pending', 'failed', 'unverified')),
    CONSTRAINT unique_active_bvn_linkage UNIQUE (msisdn, bvn) WHERE is_current = TRUE AND deleted_at IS NULL
);
CREATE INDEX idx_bvn_linkages_msisdn ON bvn_linkages(msisdn);
CREATE INDEX idx_bvn_linkages_bvn ON bvn_linkages(bvn);
CREATE INDEX idx_bvn_linkages_bank ON bvn_linkages(bank_id) WHERE bank_id IS NOT NULL;
CREATE INDEX idx_bvn_linkages_current ON bvn_linkages(msisdn) WHERE is_current = TRUE;

-- ============================================================================
-- DELINK WORKFLOW TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS delink_requests (
    id BIGSERIAL PRIMARY KEY,
    request_uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    recycled_sim_id BIGINT REFERENCES recycled_sims(id),
    msisdn VARCHAR(15) NOT NULL,
    nin VARCHAR(11),
    bvn VARCHAR(11),
    operator_id INTEGER NOT NULL REFERENCES operators(id),
    requested_by_user_id INTEGER NOT NULL REFERENCES users(id),
    requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    workflow_status VARCHAR(50) NOT NULL,
    operator_approval_status VARCHAR(50) DEFAULT 'pending',
    bank_approval_status VARCHAR(50) DEFAULT 'pending',
    bank_id INTEGER REFERENCES banks(id),
    bank_approved_by_user_id INTEGER REFERENCES users(id),
    bank_approved_at TIMESTAMP WITH TIME ZONE,
    nimc_notification_status VARCHAR(50) DEFAULT 'pending',
    nimc_reference_id VARCHAR(50),
    nimc_notified_at TIMESTAMP WITH TIME ZONE,
    execution_status VARCHAR(50) DEFAULT 'pending',
    execution_timestamp TIMESTAMP WITH TIME ZONE,
    executed_by_system_component VARCHAR(100),
    completion_timestamp TIMESTAMP WITH TIME ZONE,
    is_successful BOOLEAN,
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    rollback_status VARCHAR(50),
    rollback_reason TEXT,
    delink_method VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_msisdn CHECK (msisdn ~ '^(\+234|0)[0-9]{10}$'),
    CONSTRAINT valid_nin CHECK (nin ~ '^[0-9]{11}$' OR nin IS NULL),
    CONSTRAINT valid_bvn CHECK (bvn ~ '^[0-9]{11}$' OR bvn IS NULL),
    CONSTRAINT valid_workflow_status CHECK (workflow_status IN (
        'submitted', 'operator_approved', 'awaiting_bank_approval',
        'bank_approved', 'awaiting_nimc_notification', 'execution_in_progress',
        'completed', 'failed', 'rollback_requested', 'rolled_back', 'disputed'
    )),
    CONSTRAINT valid_approval_status CHECK (
        operator_approval_status IN ('pending', 'approved', 'rejected', 'escalated')
        AND bank_approval_status IN ('pending', 'approved', 'rejected', 'escalated')
        AND nimc_notification_status IN ('pending', 'notified', 'failed', 'acknowledged')
    ),
    CONSTRAINT valid_execution_status CHECK (
        execution_status IN ('pending', 'in_progress', 'completed', 'failed')
    ),
    CONSTRAINT valid_rollback_status CHECK (
        rollback_status IN ('pending', 'completed', 'failed', NULL)
    ),
    CONSTRAINT at_least_one_linkage CHECK (nin IS NOT NULL OR bvn IS NOT NULL)
);
CREATE INDEX idx_delink_requests_uuid ON delink_requests(request_uuid);
CREATE INDEX idx_delink_requests_msisdn ON delink_requests(msisdn);
CREATE INDEX idx_delink_requests_status ON delink_requests(workflow_status);
CREATE INDEX idx_delink_requests_operator ON delink_requests(operator_id);
CREATE INDEX idx_delink_requests_created ON delink_requests(created_at DESC);
CREATE INDEX idx_delink_requests_sim ON delink_requests(recycled_sim_id);

CREATE TABLE IF NOT EXISTS delink_approvals (
    id BIGSERIAL PRIMARY KEY,
    delink_request_id BIGINT NOT NULL REFERENCES delink_requests(id) ON DELETE CASCADE,
    approval_type VARCHAR(50) NOT NULL,
    approver_user_id INTEGER REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approval_status VARCHAR(50) NOT NULL,
    approval_notes TEXT,
    approval_ip_address INET,
    approval_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_approval_type CHECK (approval_type IN ('operator', 'bank', 'nimc')),
    CONSTRAINT valid_approval_status CHECK (approval_status IN ('pending', 'approved', 'rejected', 'escalated'))
);
CREATE INDEX idx_delink_approvals_request ON delink_approvals(delink_request_id);
CREATE INDEX idx_delink_approvals_type ON delink_approvals(approval_type);
CREATE INDEX idx_delink_approvals_status ON delink_approvals(approval_status);

-- ============================================================================
-- NOTIFICATION TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_templates (
    id SERIAL PRIMARY KEY,
    template_key VARCHAR(100) NOT NULL UNIQUE,
    template_name VARCHAR(255) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    subject VARCHAR(255),
    message_body TEXT NOT NULL,
    variables JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_channel CHECK (channel IN ('sms', 'email', 'push_notification', 'in_app')),
    CONSTRAINT valid_variables CHECK (jsonb_typeof(variables) = 'array' OR variables IS NULL)
);
CREATE INDEX idx_notification_templates_key ON notification_templates(template_key);
CREATE INDEX idx_notification_templates_channel ON notification_templates(channel);

INSERT INTO notification_templates (template_key, template_name, channel, message_body) VALUES
    ('recycled_sim_detection', 'Recycled SIM Detection Notification', 'sms',
     'Your SIM card may be a recycled one. Contact your bank or telecom operator immediately for details.'),
    ('recycled_sim_detection_email', 'Recycled SIM Detection Email', 'email',
     'We have detected that your SIM card ({{MSISDN}}) may be a recycled one. Please contact us immediately.'),
    ('delink_completed', 'Delink Process Completed', 'sms',
     'Your SIM card linkage has been successfully removed from your NIN/BVN.'),
    ('delink_failed', 'Delink Process Failed', 'sms',
     'The delink process for your account has encountered an error. Please contact support.')
ON CONFLICT (template_key) DO NOTHING;

CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    notification_uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    template_id INTEGER NOT NULL REFERENCES notification_templates(id),
    delink_request_id BIGINT REFERENCES delink_requests(id),
    recycled_sim_id BIGINT REFERENCES recycled_sims(id),
    recipient_type VARCHAR(50) NOT NULL,
    recipient_identifier VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    recipient_msisdn VARCHAR(15),
    recipient_email VARCHAR(255),
    recipient_nin VARCHAR(11),
    channel VARCHAR(50) NOT NULL,
    rendered_subject VARCHAR(255),
    rendered_message TEXT NOT NULL,
    delivery_status VARCHAR(50) NOT NULL,
    delivery_timestamp TIMESTAMP WITH TIME ZONE,
    read_timestamp TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 5,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    provider_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_recipient_type CHECK (recipient_type IN ('end_user', 'operator', 'bank', 'nimc', 'auditor')),
    CONSTRAINT valid_channel CHECK (channel IN ('sms', 'email', 'push_notification', 'in_app')),
    CONSTRAINT valid_delivery_status CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed', 'bounced', 'read'))
);
CREATE INDEX idx_notifications_uuid ON notifications(notification_uuid);
CREATE INDEX idx_notifications_delink ON notifications(delink_request_id);
CREATE INDEX idx_notifications_status ON notifications(delivery_status);
CREATE INDEX idx_notifications_recipient ON notifications(recipient_identifier);
CREATE INDEX idx_notifications_channel ON notifications(channel);
CREATE INDEX idx_notifications_created ON notifications(created_at DESC);

-- ============================================================================
-- AUDIT LOGGING
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    audit_uuid UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    actor_user_id INTEGER REFERENCES users(id),
    actor_ip_address INET,
    actor_user_agent TEXT,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    action_result VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changes_hash VARCHAR(64),
    details JSONB,
    is_security_relevant BOOLEAN DEFAULT FALSE,
    severity_level VARCHAR(50) DEFAULT 'info',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'user_login', 'user_logout', 'user_created', 'user_modified', 'user_deleted',
        'sim_detected', 'delink_requested', 'delink_approved', 'delink_executed', 'delink_failed',
        'notification_sent', 'notification_failed',
        'api_key_created', 'api_key_revoked',
        'configuration_changed', 'system_event'
    )),
    CONSTRAINT valid_resource_type CHECK (resource_type IN (
        'user', 'recycled_sim', 'delink_request', 'notification', 'api_key', 'system'
    )),
    CONSTRAINT valid_action CHECK (action IN ('create', 'read', 'update', 'delete', 'execute')),
    CONSTRAINT valid_result CHECK (action_result IN ('success', 'failure', 'partial')),
    CONSTRAINT valid_severity CHECK (severity_level IN ('info', 'warning', 'error', 'critical'))
);
CREATE INDEX idx_audit_logs_uuid ON audit_logs(audit_uuid);
CREATE INDEX idx_audit_logs_event ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_user_id);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_security ON audit_logs(is_security_relevant) WHERE is_security_relevant = TRUE;

-- Ensure audit logs are immutable (append-only)
CREATE TRIGGER audit_logs_immutable BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION raise_immutable_error();

CREATE OR REPLACE FUNCTION raise_immutable_error()
RETURNS TRIGGER LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable and cannot be modified or deleted';
END;
$$;

-- ============================================================================
-- SYSTEM CONFIGURATION
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    value_type VARCHAR(50),
    description TEXT,
    is_secret BOOLEAN DEFAULT FALSE,
    is_mutable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_value_type CHECK (value_type IN ('string', 'integer', 'boolean', 'json'))
);
CREATE INDEX idx_system_config_key ON system_config(config_key);

INSERT INTO system_config (config_key, config_value, value_type, description) VALUES
    ('max_delink_approvals_days', '2', 'integer', 'Maximum days allowed for delink approval workflow'),
    ('reconciliation_schedule_utc', '02:00', 'string', 'Daily reconciliation job execution time (UTC)'),
    ('notification_retry_max_attempts', '5', 'integer', 'Maximum retry attempts for failed notifications'),
    ('notification_retry_interval_seconds', '300', 'integer', 'Seconds to wait between notification retries'),
    ('audit_log_retention_years', '7', 'integer', 'Audit log retention period in years'),
    ('api_rate_limit_standard', '100', 'integer', 'Standard API rate limit (requests/minute)'),
    ('api_rate_limit_premium', '1000', 'integer', 'Premium API rate limit (requests/minute)'),
    ('enable_delink_auto_execution', 'false', 'boolean', 'Enable automatic delink execution after approvals'),
    ('nimc_api_timeout_seconds', '30', 'integer', 'NIMC API call timeout in seconds'),
    ('nibss_api_timeout_seconds', '15', 'integer', 'NIBSS API call timeout in seconds')
ON CONFLICT (config_key) DO NOTHING;

-- ============================================================================
-- PERFORMANCE & MONITORING TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_request_logs (
    id BIGSERIAL PRIMARY KEY,
    request_uuid UUID NOT NULL DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    api_key_id INTEGER REFERENCES api_keys(id),
    http_method VARCHAR(10) NOT NULL,
    endpoint_path VARCHAR(500) NOT NULL,
    query_parameters JSONB,
    request_body_hash VARCHAR(64),
    response_status_code SMALLINT NOT NULL,
    response_time_ms INTEGER NOT NULL,
    error_message TEXT,
    ip_address INET NOT NULL,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_method CHECK (http_method IN ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'))
);
CREATE INDEX idx_api_request_logs_user ON api_request_logs(user_id);
CREATE INDEX idx_api_request_logs_endpoint ON api_request_logs(endpoint_path);
CREATE INDEX idx_api_request_logs_status ON api_request_logs(response_status_code);
CREATE INDEX idx_api_request_logs_created ON api_request_logs(created_at DESC);
-- Retention policy: keep logs for 30 days for performance
CREATE INDEX idx_api_request_logs_retention ON api_request_logs(created_at) WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days';

CREATE TABLE IF NOT EXISTS job_execution_logs (
    id BIGSERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    job_uuid UUID NOT NULL DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds NUMERIC(10, 2),
    records_processed INTEGER,
    records_succeeded INTEGER,
    records_failed INTEGER,
    error_message TEXT,
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_job_type CHECK (job_type IN ('reconciliation', 'delink', 'notification', 'reporting', 'cleanup')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'partial_failure'))
);
CREATE INDEX idx_job_execution_logs_name ON job_execution_logs(job_name);
CREATE INDEX idx_job_execution_logs_status ON job_execution_logs(status);
CREATE INDEX idx_job_execution_logs_type ON job_execution_logs(job_type);
CREATE INDEX idx_job_execution_logs_created ON job_execution_logs(created_at DESC);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

CREATE VIEW active_recycled_sims AS
SELECT
    rs.id,
    rs.sim_serial_number,
    rs.msisdn,
    rs.operator_id,
    op.name as operator_name,
    rs.previous_owner_nin,
    rs.previous_owner_bvn,
    rs.linkage_status,
    rs.cleanup_status,
    rs.risk_score,
    rs.created_at
FROM recycled_sims rs
JOIN operators op ON rs.operator_id = op.id
WHERE rs.linkage_status = 'active'
AND rs.cleanup_status IN ('pending', 'in_progress');

CREATE VIEW pending_delink_requests AS
SELECT
    dr.id,
    dr.request_uuid,
    dr.msisdn,
    op.name as operator_name,
    dr.workflow_status,
    dr.operator_approval_status,
    dr.bank_approval_status,
    dr.requested_at,
    (CURRENT_TIMESTAMP - dr.requested_at) as age_duration
FROM delink_requests dr
JOIN operators op ON dr.operator_id = op.id
WHERE dr.workflow_status NOT IN ('completed', 'failed', 'rolled_back')
ORDER BY dr.requested_at ASC;

CREATE VIEW notification_delivery_status AS
SELECT
    channel,
    delivery_status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_delivery_time_seconds,
    DATE(created_at) as date
FROM notifications
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY channel, delivery_status, DATE(created_at);

CREATE VIEW audit_log_security_events AS
SELECT
    audit_uuid,
    event_type,
    actor_user_id,
    resource_type,
    resource_id,
    action_result,
    severity_level,
    actor_ip_address,
    created_at
FROM audit_logs
WHERE is_security_relevant = TRUE
ORDER BY created_at DESC;

-- ============================================================================
-- GRANTS FOR ROLE-BASED ACCESS
-- ============================================================================

-- Create application roles (to be used by application code, not directly by users)
CREATE ROLE reconix_app_user;
CREATE ROLE reconix_readonly_user;

-- Grant appropriate permissions
GRANT CONNECT ON DATABASE postgres TO reconix_app_user;
GRANT CONNECT ON DATABASE postgres TO reconix_readonly_user;

GRANT USAGE ON SCHEMA public TO reconix_app_user, reconix_readonly_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO reconix_app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO reconix_app_user;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO reconix_readonly_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO reconix_readonly_user;

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE recycled_sims IS 'Tracks SIM cards detected as recycled with old NIN/BVN linkages still active';
COMMENT ON TABLE nin_linkages IS 'Historical and current linkages between MSISDN and NIN (National ID Number)';
COMMENT ON TABLE bvn_linkages IS 'Historical and current linkages between MSISDN and BVN (Bank Verification Number)';
COMMENT ON TABLE delink_requests IS 'Workflow records for requesting and tracking delink operations';
COMMENT ON TABLE audit_logs IS 'Immutable audit trail of all system actions for compliance and security';
COMMENT ON TABLE notifications IS 'Notification delivery tracking across SMS, Email, Push, and In-app channels';
COMMENT ON TABLE api_keys IS 'API authentication tokens for machine-to-machine integrations';

-- ============================================================================
-- INITIAL DATA & CONSTRAINTS VERIFICATION
-- ============================================================================

-- Create extension for UUID support (if not exists)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create extension for password hashing (if not exists)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Verify schema creation
SELECT 'Schema creation completed successfully' as status;
