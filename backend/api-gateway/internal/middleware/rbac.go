package middleware

import (
	"encoding/json"
	"net/http"

	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/models"
)

// RequireRole returns a middleware that enforces a minimum role level.
// Uses role hierarchy: Admin > Analyst > Operator > Executive > ReadOnly
func RequireRole(minRole models.Role) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			userRole := GetUserRole(r.Context())
			if userRole == "" {
				writeRBACError(w, "no role found in context", http.StatusForbidden)
				return
			}

			if !userRole.HasMinRole(minRole) {
				writeRBACError(w, "insufficient permissions", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

// RequireAnyRole returns a middleware that requires the user to have one of the specified roles.
func RequireAnyRole(roles ...models.Role) func(http.Handler) http.Handler {
	roleSet := make(map[models.Role]bool)
	for _, role := range roles {
		roleSet[role] = true
	}

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			userRole := GetUserRole(r.Context())
			if userRole == "" {
				writeRBACError(w, "no role found in context", http.StatusForbidden)
				return
			}

			if !roleSet[userRole] {
				writeRBACError(w, "insufficient permissions", http.StatusForbidden)
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}

func writeRBACError(w http.ResponseWriter, message string, status int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	resp := models.ErrorResponse{
		Success: false,
		Error:   message,
		Code:    "FORBIDDEN",
	}
	json.NewEncoder(w).Encode(resp)
}
