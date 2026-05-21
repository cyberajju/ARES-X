package config

import (
	"os"
	"strconv"
	"time"
)

// Config holds all application configuration loaded from environment variables.
type Config struct {
	ServerPort          string
	JWTSecret           string
	JWTExpiry           time.Duration
	RefreshExpiry       time.Duration
	DatabaseURL         string
	RedisURL            string
	GraphEngineURL      string
	AssetServiceURL     string
	AttackPathEngineURL string
	LogLevel            string
	Environment         string
	AllowedOrigins      []string
}

// Load creates a new Config from environment variables with sensible defaults.
func Load() *Config {
	jwtExpiry := getEnvDuration("JWT_EXPIRY_MINUTES", 15)
	refreshExpiry := getEnvDuration("REFRESH_EXPIRY_MINUTES", 10080) // 7 days

	return &Config{
		ServerPort:          getEnv("SERVER_PORT", "8080"),
		JWTSecret:           getEnv("JWT_SECRET", "ares-x-default-secret-change-in-production"),
		JWTExpiry:           jwtExpiry,
		RefreshExpiry:       refreshExpiry,
		DatabaseURL:         getEnv("DATABASE_URL", "postgres://ares:ares@localhost:5432/ares_x?sslmode=disable"),
		RedisURL:            getEnv("REDIS_URL", "redis://localhost:6379/0"),
		GraphEngineURL:      getEnv("GRAPH_ENGINE_URL", "http://localhost:8081"),
		AssetServiceURL:     getEnv("ASSET_SERVICE_URL", "http://localhost:8082"),
		AttackPathEngineURL: getEnv("ATTACK_PATH_ENGINE_URL", "http://localhost:8083"),
		LogLevel:            getEnv("LOG_LEVEL", "info"),
		Environment:         getEnv("ENVIRONMENT", "development"),
		AllowedOrigins:      []string{getEnv("ALLOWED_ORIGINS", "http://localhost:3000")},
	}
}

func getEnv(key, defaultValue string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}
	return defaultValue
}

func getEnvDuration(key string, defaultMinutes int) time.Duration {
	if value, ok := os.LookupEnv(key); ok {
		if minutes, err := strconv.Atoi(value); err == nil {
			return time.Duration(minutes) * time.Minute
		}
	}
	return time.Duration(defaultMinutes) * time.Minute
}
