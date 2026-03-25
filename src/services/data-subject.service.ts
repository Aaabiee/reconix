import api from '@/services/api';

export interface PersonalDataExport {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  organization: string;
  created_at: string;
  last_login: string | null;
  audit_log_count: number;
  delink_requests_initiated: number;
  data_retention_policy: string;
}

export interface DataDeletionResponse {
  request_id: string;
  status: string;
  records_queued_for_deletion: number;
  estimated_completion: string;
  retention_notice: string;
}

export interface ConsentRecord {
  user_id: number;
  consent_given: boolean;
  consent_date: string;
  purposes: string[];
  legal_basis: string;
  data_controller: string;
  data_protection_officer: string;
  right_to_withdraw: boolean;
}

export interface PrivacyPolicy {
  policy_version: string;
  effective_date: string;
  data_controller: string;
  regulation: string;
  purposes_of_processing: string[];
  data_subject_rights: string[];
  retention_periods: Record<string, string>;
  security_measures: string[];
}

export interface AccessRequest {
  email: string;
  request_type: 'access' | 'deletion' | 'rectification' | 'portability';
  reason?: string;
}

export interface AccessRequestResponse {
  request_id: string;
  status: string;
  request_type: string;
  submitted_at: string;
  estimated_completion: string;
}

export const dataSubjectService = {
  async getMyData(): Promise<PersonalDataExport> {
    const response = await api.get<PersonalDataExport>('/data-subject/my-data');
    return response.data;
  },

  async requestDeletion(): Promise<DataDeletionResponse> {
    const response = await api.post<DataDeletionResponse>('/data-subject/delete-my-data');
    return response.data;
  },

  async getConsent(): Promise<ConsentRecord> {
    const response = await api.get<ConsentRecord>('/data-subject/consent');
    return response.data;
  },

  async getPrivacyPolicy(): Promise<PrivacyPolicy> {
    const response = await api.get<PrivacyPolicy>('/data-subject/privacy-policy');
    return response.data;
  },

  async submitAccessRequest(request: AccessRequest): Promise<AccessRequestResponse> {
    const response = await api.post<AccessRequestResponse>(
      '/data-subject/access-request',
      request,
    );
    return response.data;
  },
};
