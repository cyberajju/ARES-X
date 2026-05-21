package middleware

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"

	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/models"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/services"
)

type contextKey string

const (
	UserIDKey  contextKey = "user_id"
	UserRoleKey contextKey = "user_role"
	UserEmailKey contextKey = "user_email"
	ClaimsKey  contextKey = "claims"
)

// Auth returns a middleware that validates JWT tokens from the Authorization header.
func Auth(jwtService *services.JWTService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			authHeader := r.Header.Get("Authorization")
			if authHeader == "" {
				writeAuthError(w, "missing authorization header", http.StatusUnauthorized)
				return
			}

			parts := strings.SplitN(authHeader, " ", 2)
			if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
				writeAuthError(w, "invalid authorization header format", http.StatusUnauthorized)
				return
			}

			tokenString := parts[1]
			claims, err := jwtService.ValidateToken(tokenString)
			if err != nil {
				switch err {
				case services.ErrExpiredToken:
					writeAuthError(w, "token has expired", http.StatusUnauthorized)
				case services.ErrInvalidSignature:
					writeAuthError(w, "invalid token signature", http.StatusUnauthorized)
				default:
					writeAuthError(w, "invalid token", http.StatusUnauthorized)
				}
				return
			}

			// Inject user info into request context
			ctx := r.Context()
			ctx = context.WithValue(ctx, UserIDKey, claims.UserID)
			ctx = context.WithValue(ctx, UserRoleKey, claims.Role)
			ctx = context.WithValue(ctx, UserEmailKey, claims.Email)
			ctx = context.WithValue(ctx, ClaimsKey, claims)

			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetUserID extracts the user ID from the request context.
func GetUserID(ctx context.Context) string {
	if val, ok := ctx.Value(UserIDKey).(string); ok {
		return val
	}
	return ""
}

// GetUserRole extracts the user role from the request context.
func GetUserRole(ctx context.Context) models.Role {
	if val, ok := ctx.Value(UserRoleKey).(models.Role); ok {
		return val
	}
	return ""
}

// GetUserEmail extracts the user email from the request context.
func GetUserEmail(ctx context.Context) string {
	if val, ok := ctx.Value(UserEmailKey).(string); ok {
		return val
	}
	return ""
}

func writeAuthError(w http.ResponseWriter, message string, status int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	resp := models.ErrorResponse{
		Success: false,
		Error:   message,
		Code:    "UNAUTHORIZED",
	}
	json.NewEncoder(w).Encode(resp)
}
