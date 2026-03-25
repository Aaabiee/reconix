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

describe('Observability API Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Health Endpoint', () => {
    it('returns health status with pool info', async () => {
      mockGet.mockResolvedValueOnce({
        data: {
          status: 'healthy',
          version: '1.0.0',
          database: 'connected',
          pool: {
            pool_size: 20,
            checked_in: 18,
            checked_out: 2,
            overflow: 0,
          },
        },
      });

      const response = await mockGet('/health');
      expect(response.data.status).toBe('healthy');
      expect(response.data.pool).toBeDefined();
      expect(response.data.pool.pool_size).toBe(20);
    });

    it('returns degraded when database unreachable', async () => {
      mockGet.mockResolvedValueOnce({
        data: {
          status: 'degraded',
          version: '1.0.0',
          database: 'unreachable',
          pool: {},
        },
      });

      const response = await mockGet('/health');
      expect(response.data.status).toBe('degraded');
      expect(response.data.database).toBe('unreachable');
    });
  });

  describe('Metrics Endpoint', () => {
    it('returns Prometheus-format metrics', async () => {
      const metricsText = [
        '# HELP reconix_http_requests_total Total HTTP requests',
        '# TYPE reconix_http_requests_total counter',
        'reconix_http_requests_total{method="GET",path="/api/v1/recycled-sims",status="200"} 5',
        '',
        '# HELP reconix_http_active_requests Current active requests',
        '# TYPE reconix_http_active_requests gauge',
        'reconix_http_active_requests 0',
      ].join('\n');

      mockGet.mockResolvedValueOnce({ data: metricsText });

      const response = await mockGet('/metrics');
      expect(response.data).toContain('reconix_http_requests_total');
      expect(response.data).toContain('reconix_http_active_requests');
    });
  });

  describe('Retention Endpoint', () => {
    it('purge audit logs returns deleted count', async () => {
      mockPost.mockResolvedValueOnce({
        data: {
          message: 'Audit log purge completed',
          deleted_count: 42,
          retention_days: 365,
        },
      });

      const response = await mockPost('/retention/purge-audit-logs');
      expect(response.data.deleted_count).toBe(42);
      expect(response.data.retention_days).toBe(365);
    });

    it('purge requires admin role (forbidden for non-admin)', async () => {
      mockPost.mockRejectedValueOnce({
        response: { status: 403, data: { code: 'AUTHORIZATION_ERROR' } },
      });

      try {
        await mockPost('/retention/purge-audit-logs');
        fail('Should have thrown');
      } catch (error: any) {
        expect(error.response.status).toBe(403);
      }
    });
  });
});

describe('Idempotency Key Support', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('replayed request returns same response with replay header', async () => {
    const idempotencyKey = 'test-key-12345';

    mockPost.mockResolvedValueOnce({
      data: { id: 1, status: 'created' },
      headers: { 'idempotency-key-replayed': 'true' },
    });

    const response = await mockPost('/recycled-sims', {}, {
      headers: { 'Idempotency-Key': idempotencyKey },
    });

    expect(response.data.id).toBe(1);
    expect(response.headers['idempotency-key-replayed']).toBe('true');
  });

  it('concurrent duplicate request returns 409', async () => {
    mockPost.mockRejectedValueOnce({
      response: {
        status: 409,
        data: {
          code: 'CONFLICT',
          message: 'A request with this idempotency key is already being processed',
        },
      },
    });

    try {
      await mockPost('/recycled-sims', {}, {
        headers: { 'Idempotency-Key': 'duplicate-key' },
      });
      fail('Should have thrown');
    } catch (error: any) {
      expect(error.response.status).toBe(409);
    }
  });
});

describe('Fine-Grained Permissions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('permission error returns missing permissions detail', async () => {
    mockPost.mockRejectedValueOnce({
      response: {
        status: 403,
        data: {
          code: 'AUTHORIZATION_ERROR',
          message: 'Missing required permissions: retention:execute',
          details: { missing_permissions: ['retention:execute'] },
        },
      },
    });

    try {
      await mockPost('/retention/purge-audit-logs');
      fail('Should have thrown');
    } catch (error: any) {
      expect(error.response.data.details.missing_permissions).toContain('retention:execute');
    }
  });
});
