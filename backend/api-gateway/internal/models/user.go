package models

import "time"

// Role represents a user role in the system.
type Role string

const (
	RoleAdmin     Role = "admin"
	RoleAnalyst   Role = "analyst"
	RoleOperator  Role = "operator"
	RoleExecutive Role = "executive"
	RoleReadOnly  Role = "readonly"
)

// RoleHierarchy maps roles to their hierarchy level (higher = more permissions).
var RoleHierarchy = map[Role]int{
	RoleAdmin:     5,
	RoleAnalyst:   4,
	RoleOperator:  3,
	RoleExecutive: 2,
	RoleReadOnly:  1,
}

// HasMinRole checks if the role meets the minimum required role level.
func (r Role) HasMinRole(minRole Role) bool {
	return RoleHierarchy[r] >= RoleHierarchy[minRole]
}

// User represents a system user.
type User struct {
	ID        string    `json:"id"`
	Email     string    `json:"email"`
	Name      string    `json:"name"`
	Role      Role      `json:"role"`
	MFAActive bool      `json:"mfa_active"`
	Active    bool      `json:"active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// Session represents an active user session.
type Session struct {
	ID           string    `json:"id"`
	UserID       string    `json:"user_id"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
	CreatedAt    time.Time `json:"created_at"`
}

// Credentials represents login credentials.
type Credentials struct {
	Email    string `json:"email"`
	Password string `json:"password"`
	MFACode  string `json:"mfa_code,omitempty"`
}

// MFASetup holds MFA setup information.
type MFASetup struct {
	Secret    string `json:"secret"`
	QRCodeURL string `json:"qr_code_url"`
	Issuer    string `json:"issuer"`
	Account   string `json:"account"`
}

// MFAVerifyRequest represents a request to verify an MFA code.
type MFAVerifyRequest struct {
	Code string `json:"code"`
}

// AuthResponse is the response returned after successful authentication.
type AuthResponse struct {
	User         *User  `json:"user"`
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int64  `json:"expires_in"`
}

// RefreshRequest represents a token refresh request.
type RefreshRequest struct {
	RefreshToken string `json:"refresh_token"`
}
