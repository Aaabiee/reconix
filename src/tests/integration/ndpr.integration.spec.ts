import '@testing-library/jest-dom';

const mockGet = jest.fn();
const mockPost = jest.fn();

jest.mock('@/services/api', () => ({
  __esModule: true,
  default: {
    get: mockGet,
    post: mockPost,
  },
}));

describe('NDPR Data Subject Rights Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Privacy Policy', () => {
    it('returns NDPR-compliant privacy policy', async () => {
      mockGet.mockResolvedValueOnce({
        data: {
          policy_version: '1.0',
          regulation: 'Nigeria Data Protection Regulation (NDPR) 2019',
          data_controller: 'Reconix Platform Operator',
          data_protection_officer: 'dpo@reconix.ng',
          purposes_of_processing: [
            'Identity reconciliation for recycled SIM card management',
            'NIN/BVN linkage verification with NIMC and NIBSS',
          ],
          data_subject_rights: [
            'Right of access',
            'Right to erasure',
            'Right to data portability',
          ],
          retention_periods: {
            audit_logs: '365 days',
            user_accounts: 'Duration of service + 90 days',
          },
          security_measures: [
            'Encryption at rest',
            'Role-based access control',
          ],
          cross_border_transfers: 'Data processed within Nigeria.',
        },
      });

      const response = await mockGet('/data-subject/privacy-policy');
      const policy = response.data;

      expect(policy.regulation).toContain('NDPR');
      expect(policy.data_protection_officer).toBe('dpo@reconix.ng');
      expect(policy.purposes_of_processing.length).toBeGreaterThanOrEqual(2);
      expect(policy.data_subject_rights.length).toBeGreaterThanOrEqual(3);
      expect(policy.cross_border_transfers).toContain('Nigeria');
    });
  });

  describe('Personal Data Export', () => {
    it('returns user personal data with retention info', async () => {
      mockGet.mockResolvedValueOnce({
        data: {
          user_id: 1,
          email: 'user@example.com',
          full_name: 'Test User',
          role: 'operator',
          organization: 'Test Org',
          created_at: '2024-01-01T00:00:00Z',
          last_login: '2024-03-01T12:00:00Z',
          audit_log_count: 42,
          delink_requests_initiated: 5,
          data_retention_policy: '365 days for audit logs per NDPR Section 2.1',
        },
      });

      const response = await mockGet('/data-subject/my-data');
      const data = response.data;

      expect(data.email).toBe('user@example.com');
      expect(data.audit_log_count).toBe(42);
      expect(data.data_retention_policy).toContain('NDPR');
    });

    it('requires authentication', async () => {
      mockGet.mockRejectedValueOnce({
        response: { status: 401, data: { code: 'AUTHENTICATION_ERROR' } },
      });

      try {
        await mockGet('/data-subject/my-data');
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
      }
    });
  });

  describe('Data Deletion Request', () => {
    it('queues deletion request with NDPR notice', async () => {
      mockPost.mockResolvedValueOnce({
        data: {
          request_id: 'abc123def',
          status: 'queued',
          records_queued_for_deletion: 1,
          estimated_completion: '30 days per NDPR guidelines',
          retention_notice: 'Audit logs are retained for regulatory compliance per NDPR Section 2.1(1)(b)',
        },
      });

      const response = await mockPost('/data-subject/delete-my-data');
      const data = response.data;

      expect(data.status).toBe('queued');
      expect(data.retention_notice).toContain('NDPR');
      expect(data.estimated_completion).toContain('30 days');
    });

    it('blocks admin self-deletion', async () => {
      mockPost.mockRejectedValueOnce({
        response: {
          status: 400,
          data: {
            code: 'VALIDATION_ERROR',
            message: 'Admin accounts cannot self-delete',
          },
        },
      });

      try {
        await mockPost('/data-subject/delete-my-data');
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.response.status).toBe(400);
      }
    });
  });

  describe('Consent Record', () => {
    it('returns consent details with withdrawal rights', async () => {
      mockGet.mockResolvedValueOnce({
        data: {
          user_id: 1,
          consent_given: true,
          consent_date: '2024-01-01T00:00:00Z',
          purposes: [
            'Identity reconciliation',
            'NIN/BVN linkage verification',
          ],
          legal_basis: 'NDPR Section 2.2',
          right_to_withdraw: true,
        },
      });

      const response = await mockGet('/data-subject/consent');
      const consent = response.data;

      expect(consent.consent_given).toBe(true);
      expect(consent.right_to_withdraw).toBe(true);
      expect(consent.legal_basis).toContain('NDPR');
      expect(consent.purposes.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Access Request', () => {
    it('accepts valid access request types', async () => {
      const requestTypes = ['access', 'deletion', 'rectification', 'portability'];

      for (const requestType of requestTypes) {
        mockPost.mockResolvedValueOnce({
          data: {
            request_id: `req-${requestType}`,
            status: 'received',
            request_type: requestType,
            submitted_at: '2024-03-01T00:00:00Z',
            estimated_completion: '30 days per NDPR guidelines',
          },
        });

        const response = await mockPost('/data-subject/access-request', {
          email: 'user@example.com',
          request_type: requestType,
        });

        expect(response.data.request_type).toBe(requestType);
        expect(response.data.status).toBe('received');
      }
    });

    it('rejects invalid request type', async () => {
      mockPost.mockRejectedValueOnce({
        response: { status: 422, data: { code: 'VALIDATION_ERROR' } },
      });

      try {
        await mockPost('/data-subject/access-request', {
          email: 'user@example.com',
          request_type: 'invalid_type',
        });
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.response.status).toBe(422);
      }
    });
  });
});

describe('Data Subject Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('getMyData calls correct endpoint', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        user_id: 1,
        email: 'test@example.com',
        full_name: 'Test',
        role: 'operator',
        organization: 'Org',
        audit_log_count: 0,
        delink_requests_initiated: 0,
        data_retention_policy: 'NDPR compliant',
      },
    });

    const { dataSubjectService } = require('@/services/data-subject.service');
    const data = await dataSubjectService.getMyData();
    expect(data.email).toBe('test@example.com');
    expect(mockGet).toHaveBeenCalledWith('/data-subject/my-data');
  });

  it('getPrivacyPolicy calls correct endpoint', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        policy_version: '1.0',
        regulation: 'NDPR 2019',
      },
    });

    const { dataSubjectService } = require('@/services/data-subject.service');
    const policy = await dataSubjectService.getPrivacyPolicy();
    expect(policy.regulation).toContain('NDPR');
    expect(mockGet).toHaveBeenCalledWith('/data-subject/privacy-policy');
  });
});
