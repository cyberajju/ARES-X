package middleware

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

// responseWriter wraps http.ResponseWriter to capture the status code.
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func newResponseWriter(w http.ResponseWriter) *responseWriter {
	return &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Logging returns a middleware that logs each request in structured JSON format.
func Logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// Get or generate request ID
		requestID := r.Header.Get("X-Request-ID")
		if requestID == "" {
			requestID = generateRequestID()
		}

		// Set request ID on response header
		w.Header().Set("X-Request-ID", requestID)

		// Wrap response writer to capture status code
		wrapped := newResponseWriter(w)

		// Process request
		next.ServeHTTP(wrapped, r)

		// Log entry
		duration := time.Since(start)
		logEntry := map[string]interface{}{
			"level":      "info",
			"component":  "http",
			"method":     r.Method,
			"path":       r.URL.Path,
			"status":     wrapped.statusCode,
			"duration_ms": duration.Milliseconds(),
			"request_id": requestID,
			"client_ip":  clientIP(r),
			"user_agent": r.UserAgent(),
			"timestamp":  time.Now().UTC().Format(time.RFC3339),
		}

		data, err := json.Marshal(logEntry)
		if err == nil {
			fmt.Fprintln(os.Stdout, string(data))
		}
	})
}

func generateRequestID() string {
	b := make([]byte, 16)
	_, _ = rand.Read(b)
	// Format as UUID-like: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
	return fmt.Sprintf("%s-%s-%s-%s-%s",
		hex.EncodeToString(b[0:4]),
		hex.EncodeToString(b[4:6]),
		hex.EncodeToString(b[6:8]),
		hex.EncodeToString(b[8:10]),
		hex.EncodeToString(b[10:16]),
	)
}

func clientIP(r *http.Request) string {
	// Check X-Forwarded-For header first
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		return xff
	}
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return xri
	}
	return r.RemoteAddr
}
