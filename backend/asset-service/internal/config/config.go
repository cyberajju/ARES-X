package config

import (
	"os"
	"strconv"
)

// Config holds all configuration for the asset service.
type Config struct {
	ServerPort        string
	DatabaseURL       string
	LogLevel          string
	MaxBulkImportSize int
}

// Load reads configuration from environment variables with sensible defaults.
func Load() *Config {
	return &Config{
		ServerPort:        getEnv("ASSET_SERVICE_PORT", "8081"),
		DatabaseURL:       getEnv("DATABASE_URL", "postgres://ares:ares@localhost:5432/ares_assets?sslmode=disable"),
		LogLevel:          getEnv("LOG_LEVEL", "info"),
		MaxBulkImportSize: getEnvInt("MAX_BULK_IMPORT_SIZE", 1000),
	}
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func getEnvInt(key string, defaultVal int) int {
	if val := os.Getenv(key); val != "" {
		if n, err := strconv.Atoi(val); err == nil {
			return n
		}
	}
	return defaultVal
}
