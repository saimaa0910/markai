// Common Audit Interface
export interface AuditMeta {
  id: string;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
  deletedAt?: string | null;
}

// User role definition
export type UserRole = 'OWNER' | 'ADMIN' | 'MEMBER' | 'GUEST';

// Generic API response structure
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}
