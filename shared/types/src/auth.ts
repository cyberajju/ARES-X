/**
 * Authentication and authorization types for the ARES-X platform.
 * @module auth
 */

/** User roles within the ARES-X platform. */
export enum Role {
  Admin = 'admin',
  Analyst = 'analyst',
  Operator = 'operator',
  Executive = 'executive',
  ReadOnly = 'read_only',
}

/** Represents a user account in the system. */
export interface User {
  /** Unique user identifier. */
  id: string;
  /** User's email address. */
  email: string;
  /** User's display name. */
  displayName: string;
  /** Assigned role determining access level. */
  role: Role;
  /** Whether the user account is active. */
  isActive: boolean;
  /** Whether MFA is enabled for this user. */
  mfaEnabled: boolean;
  /** URL to user's avatar image. */
  avatarUrl?: string;
  /** Department the user belongs to. */
  department?: string;
  /** Timestamp of last successful login. */
  lastLoginAt?: string;
  /** Timestamp when the user was created. */
  createdAt: string;
  /** Timestamp of last account update. */
  updatedAt: string;
}

/** Represents an active user session. */
export interface Session {
  /** Unique session identifier. */
  id: string;
  /** ID of the user who owns this session. */
  userId: string;
  /** JWT access token. */
  accessToken: string;
  /** Refresh token for obtaining new access tokens. */
  refreshToken: string;
  /** Timestamp when the session expires. */
  expiresAt: string;
  /** IP address of the client. */
  ipAddress: string;
  /** User agent string of the client. */
  userAgent: string;
  /** Timestamp when the session was created. */
  createdAt: string;
}

/** JWT payload structure for access tokens. */
export interface JWTPayload {
  /** Subject - user ID. */
  sub: string;
  /** User's email address. */
  email: string;
  /** User's role. */
  role: Role;
  /** Issued at timestamp (Unix). */
  iat: number;
  /** Expiration timestamp (Unix). */
  exp: number;
  /** Issuer identifier. */
  iss: string;
  /** Session ID. */
  sessionId: string;
}

/** Request body for user login. */
export interface LoginRequest {
  /** User's email address. */
  email: string;
  /** User's password. */
  password: string;
}

/** Response body for successful login. */
export interface LoginResponse {
  /** The authenticated user. */
  user: User;
  /** Session information including tokens. */
  session: Session;
  /** Whether MFA verification is required. */
  mfaRequired: boolean;
}

/** Request body for MFA verification. */
export interface MFARequest {
  /** Session ID from the initial login. */
  sessionId: string;
  /** The MFA code entered by the user. */
  code: string;
  /** Type of MFA being used. */
  method: 'totp' | 'sms' | 'email';
}
