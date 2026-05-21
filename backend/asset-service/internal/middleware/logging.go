package middleware

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

// responseRecorder wraps http.ResponseWriter to capture status code.
type responseRecorder struct {
	http.ResponseWriter
	statusCode int
}

func (r *responseRecorder) WriteHeader(code int) {
	r.statusCode = code
	r.ResponseWriter.WriteHeader(code)
}

// Logging wraps an HTTP handler with structured request logging.
func Logging(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		rec := &responseRecorder{ResponseWriter: w, statusCode: http.StatusOK}

		next.ServeHTTP(rec, r)

		duration := time.Since(start)

		entry := map[string]interface{}{
			"level":      "info",
			"component":  "http",
			"method":     r.Method,
			"path":       r.URL.Path,
			"status":     rec.statusCode,
			"duration_ms": duration.Milliseconds(),
			"remote":     r.RemoteAddr,
			"timestamp":  time.Now().UTC().Format(time.RFC3339),
		}

		data, _ := json.Marshal(entry)
		fmt.Fprintln(os.Stdout, string(data))
	})
}
