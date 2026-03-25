export type SimStatus = 'active' | 'recycled' | 'dormant' | 'blacklisted';
export type DelinkStatus = 'pending' | 'approved' | 'completed' | 'rejected' | 'cancelled';
export type NotificationType = 'info' | 'warning' | 'error' | 'success';

export interface RecycledSim {
  id: string;
  phoneNumber: string;
  nin: string;
  bvn: string;
  operatorCode: string;
  operatorName: string;
  simStatus: SimStatus;
  lastUsedDate: string;
  recycledDate: string;
  detectionMethod: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface DelinkRequest {
  id: string;
  recycledSimId: string;
  phoneNumber: string;
  nin: string;
  bvn: string;
  operatorCode: string;
  status: DelinkStatus;
  requestedBy: string;
  requestedAt: string;
  approvedBy?: string;
  approvedAt?: string;
  completedAt?: string;
  reason?: string;
  notes?: string;
  delinkReason?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Notification {
  id: string;
  userId: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  actionUrl?: string;
  relatedEntityId?: string;
  relatedEntityType?: string;
  createdAt: string;
}

export interface AuditLog {
  id: string;
  userId: string;
  userEmail: string;
  action: string;
  entityType: string;
  entityId: string;
  changes: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  status: 'success' | 'failure';
  errorMessage?: string;
  createdAt: string;
}

export interface DashboardStats {
  totalRecycledSims: number;
  totalDelinkRequests: number;
  pendingDelinkRequests: number;
  completedDelinkRequests: number;
  totalOperators: number;
  successRate: number;
}

export interface TrendData {
  date: string;
  recycledSims: number;
  delinkRequests: number;
  completedDelinkRequests: number;
}

export interface RecycledSimsByOperator {
  operatorCode: string;
  operatorName: string;
  count: number;
  percentage: number;
}

export interface BulkUploadResult {
  id: string;
  fileName: string;
  totalRows: number;
  successCount: number;
  failureCount: number;
  status: 'processing' | 'completed' | 'failed';
  errors?: Array<{
    row: number;
    error: string;
  }>;
  uploadedBy: string;
  createdAt: string;
  completedAt?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  keyPrefix: string;
  keySuffix: string;
  permissions: string[];
  lastUsedAt?: string;
  expiresAt?: string;
  createdAt: string;
  revokedAt?: string;
}
