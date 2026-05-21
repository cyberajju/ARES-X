/**
 * API utility types for the ARES-X platform.
 * @module api
 */

/** HTTP methods supported by the API. */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

/** Generic API response wrapper. */
export interface ApiResponse<T> {
  /** Whether the request was successful. */
  success: boolean;
  /** Response data (present on success). */
  data: T;
  /** ISO timestamp of the response. */
  timestamp: string;
  /** Unique request identifier for tracing. */
  requestId: string;
}

/** Paginated API response wrapper. */
export interface PaginatedResponse<T> {
  /** Whether the request was successful. */
  success: boolean;
  /** Array of items for the current page. */
  data: T[];
  /** Pagination metadata. */
  pagination: PaginationMeta;
  /** ISO timestamp of the response. */
  timestamp: string;
  /** Unique request identifier for tracing. */
  requestId: string;
}

/** Pagination metadata included in paginated responses. */
export interface PaginationMeta {
  /** Current page number (1-based). */
  page: number;
  /** Number of items per page. */
  pageSize: number;
  /** Total number of items across all pages. */
  totalCount: number;
  /** Total number of pages. */
  totalPages: number;
  /** Whether there is a next page. */
  hasNext: boolean;
  /** Whether there is a previous page. */
  hasPrevious: boolean;
}

/** Error response structure. */
export interface ErrorResponse {
  /** Always false for error responses. */
  success: false;
  /** Error details. */
  error: ErrorDetail;
  /** ISO timestamp of the response. */
  timestamp: string;
  /** Unique request identifier for tracing. */
  requestId: string;
}

/** Detailed error information. */
export interface ErrorDetail {
  /** Machine-readable error code. */
  code: string;
  /** Human-readable error message. */
  message: string;
  /** Additional error details or field-level errors. */
  details?: Record<string, string>;
  /** HTTP status code. */
  statusCode: number;
}

/** API endpoint definition for documentation and client generation. */
export interface ApiEndpoint {
  /** HTTP method. */
  method: HttpMethod;
  /** URL path pattern (e.g., /api/v1/assets/:id). */
  path: string;
  /** Human-readable description. */
  description: string;
  /** Whether authentication is required. */
  requiresAuth: boolean;
  /** Minimum role required to access this endpoint. */
  requiredRole?: string;
  /** Rate limit (requests per minute). */
  rateLimit?: number;
}
