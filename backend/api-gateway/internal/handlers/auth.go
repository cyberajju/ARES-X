package handlers

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"time"

	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/middleware"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/models"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/services"
)

// Demo users for development
var demoUsers = map[string]*demoUser{
	"admin@ares-x.mil": {
		User: models.User{
			ID:        "usr-001",
			Email:     "admin@ares-x.mil",
			Name:      "Admin User",
			Role:      models.RoleAdmin,
			MFAActive: true,
			Active:    true,
			CreatedAt: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
			UpdatedAt: time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		},
		Password: "admin-secret-2024",
	},
	"analyst@ares-x.mil": {
		User: models.User{
			ID:        "usr-002",
			Email:     "analyst@ares-x.mil",
			Name:      "Security Analyst",
			Role:      models.RoleAnalyst,
			MFAActive: false,
			Active:    true,
			CreatedAt: time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC),
			UpdatedAt: time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC),
		},
		Password: "analyst-secret-2024",
	},
	"operator@ares-x.mil": {
		User: models.User{
			ID:        "usr-003",
			Email:     "operator@ares-x.mil",
			Name:      "Network Operator",
			Role:      models.RoleOperator,
			MFAActive: false,
			Active:    true,
			CreatedAt: time.Date(2024, 2, 1, 0, 0, 0, 0, time.UTC),
			UpdatedAt: time.Date(2024, 2, 1, 0, 0, 0, 0, time.UTC),
		},
		Password: "operator-secret-2024",
	},
}

type demoUser struct {
	User     models.User
	Password string
}

// AuthHandler handles authentication-related endpoints.
type AuthHandler struct {
	jwtService   *services.JWTService
	auditService *services.AuditService
}

// NewAuthHandler creates a new AuthHandler.
func NewAuthHandler(jwtService *services.JWTService, auditService *services.AuditService) *AuthHandler {
	return &AuthHandler{
		jwtService:   jwtService,
		auditService: auditService,
	}
}

// Login handles POST /api/v1/auth/login
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	var creds models.Credentials
	if err := json.NewDecoder(r.Body).Decode(&creds); err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "invalid request body",
			Code:    "BAD_REQUEST",
		})
		return
	}

	if creds.Email == "" || creds.Password == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "email and password are required",
			Code:    "VALIDATION_ERROR",
			Details: []models.ValidationError{
				{Field: "email", Message: "email is required"},
				{Field: "password", Message: "password is required"},
			},
		})
		return
	}

	// Find demo user
	demo, exists := demoUsers[creds.Email]
	if !exists || demo.Password != creds.Password {
		h.auditService.LogEvent(services.EventAuthFailure, creds.Email, "invalid credentials", clientIP(r))
		writeJSON(w, http.StatusUnauthorized, models.ErrorResponse{
			Success: false,
			Error:   "invalid email or password",
			Code:    "INVALID_CREDENTIALS",
		})
		return
	}

	if !demo.User.Active {
		writeJSON(w, http.StatusForbidden, models.ErrorResponse{
			Success: false,
			Error:   "account is disabled",
			Code:    "ACCOUNT_DISABLED",
		})
		return
	}

	// Generate tokens
	accessToken, err := h.jwtService.GenerateAccessToken(&demo.User)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, models.ErrorResponse{
			Success: false,
			Error:   "failed to generate access token",
			Code:    "INTERNAL_ERROR",
		})
		return
	}

	refreshToken, err := h.jwtService.GenerateRefreshToken(&demo.User)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, models.ErrorResponse{
			Success: false,
			Error:   "failed to generate refresh token",
			Code:    "INTERNAL_ERROR",
		})
		return
	}

	h.auditService.LogEvent(services.EventLogin, demo.User.ID, "successful login", clientIP(r))

	writeJSON(w, http.StatusOK, models.ApiResponse[models.AuthResponse]{
		Success: true,
		Data: models.AuthResponse{
			User:         &demo.User,
			AccessToken:  accessToken,
			RefreshToken: refreshToken,
			ExpiresIn:    900, // 15 minutes in seconds
		},
		Message: "login successful",
	})
}

// Logout handles POST /api/v1/auth/logout
func (h *AuthHandler) Logout(w http.ResponseWriter, r *http.Request) {
	userID := middleware.GetUserID(r.Context())
	h.auditService.LogEvent(services.EventLogout, userID, "user logged out", clientIP(r))

	writeJSON(w, http.StatusOK, models.ApiResponse[any]{
		Success: true,
		Message: "logged out successfully",
	})
}

// RefreshToken handles POST /api/v1/auth/refresh
func (h *AuthHandler) RefreshToken(w http.ResponseWriter, r *http.Request) {
	var req models.RefreshRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "invalid request body",
			Code:    "BAD_REQUEST",
		})
		return
	}

	if req.RefreshToken == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "refresh_token is required",
			Code:    "VALIDATION_ERROR",
		})
		return
	}

	claims, err := h.jwtService.ValidateToken(req.RefreshToken)
	if err != nil {
		writeJSON(w, http.StatusUnauthorized, models.ErrorResponse{
			Success: false,
			Error:   "invalid or expired refresh token",
			Code:    "INVALID_REFRESH_TOKEN",
		})
		return
	}

	// Find user and generate new access token
	demo, exists := demoUsers[claims.Email]
	if !exists {
		writeJSON(w, http.StatusUnauthorized, models.ErrorResponse{
			Success: false,
			Error:   "user not found",
			Code:    "USER_NOT_FOUND",
		})
		return
	}

	accessToken, err := h.jwtService.GenerateAccessToken(&demo.User)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, models.ErrorResponse{
			Success: false,
			Error:   "failed to generate access token",
			Code:    "INTERNAL_ERROR",
		})
		return
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[models.AuthResponse]{
		Success: true,
		Data: models.AuthResponse{
			User:         &demo.User,
			AccessToken:  accessToken,
			RefreshToken: req.RefreshToken,
			ExpiresIn:    900,
		},
		Message: "token refreshed",
	})
}

// InitMFA handles POST /api/v1/auth/mfa/setup
func (h *AuthHandler) InitMFA(w http.ResponseWriter, r *http.Request) {
	userEmail := middleware.GetUserEmail(r.Context())

	secret := generateRandomHex(20)

	setup := models.MFASetup{
		Secret:    secret,
		QRCodeURL: "otpauth://totp/ARES-X:" + userEmail + "?secret=" + secret + "&issuer=ARES-X",
		Issuer:    "ARES-X",
		Account:   userEmail,
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[models.MFASetup]{
		Success: true,
		Data:    setup,
		Message: "MFA setup initialized",
	})
}

// VerifyMFA handles POST /api/v1/auth/mfa/verify
func (h *AuthHandler) VerifyMFA(w http.ResponseWriter, r *http.Request) {
	var req models.MFAVerifyRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "invalid request body",
			Code:    "BAD_REQUEST",
		})
		return
	}

	if req.Code == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "code is required",
			Code:    "VALIDATION_ERROR",
		})
		return
	}

	// In demo mode, accept any 6-digit code
	if len(req.Code) != 6 {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "invalid MFA code format",
			Code:    "INVALID_MFA_CODE",
		})
		return
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[any]{
		Success: true,
		Message: "MFA verified successfully",
	})
}

func generateRandomHex(n int) string {
	b := make([]byte, n)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func clientIP(r *http.Request) string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		return xff
	}
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return xri
	}
	return r.RemoteAddr
}
