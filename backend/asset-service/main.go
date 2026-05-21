package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/cyberajju/ARES-X/backend/asset-service/internal/config"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/repository"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/router"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/seed"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/services"
)

func main() {
	cfg := config.Load()

	logInfo("server", "starting ARES-X Asset Service", map[string]string{
		"port":      cfg.ServerPort,
		"log_level": cfg.LogLevel,
	})

	// Initialize in-memory repository
	repo := repository.NewInMemoryRepo()

	// Initialize services
	scoringSvc := services.NewScoringService(repo)
	relationshipSvc := services.NewRelationshipService(repo)
	ingestionSvc := services.NewIngestionService(repo, scoringSvc, relationshipSvc, cfg.MaxBulkImportSize)

	// Seed initial data
	seed.LoadSeedData(repo, scoringSvc, relationshipSvc)

	logInfo("server", "seed data loaded", nil)

	// Set up router
	handler := router.New(cfg, repo, ingestionSvc, scoringSvc, relationshipSvc)

	// Create HTTP server
	srv := &http.Server{
		Addr:         ":" + cfg.ServerPort,
		Handler:      handler,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		logInfo("server", fmt.Sprintf("listening on port %s", cfg.ServerPort), nil)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logError("server", "failed to start server", err)
			os.Exit(1)
		}
	}()

	// Graceful shutdown on SIGINT/SIGTERM
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	sig := <-quit

	logInfo("server", fmt.Sprintf("received signal %s, shutting down gracefully", sig.String()), nil)

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logError("server", "forced shutdown", err)
		os.Exit(1)
	}

	logInfo("server", "server stopped", nil)
}

func logInfo(component, message string, fields map[string]string) {
	entry := map[string]interface{}{
		"level":     "info",
		"component": component,
		"message":   message,
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	}
	for k, v := range fields {
		entry[k] = v
	}
	data, _ := json.Marshal(entry)
	fmt.Fprintln(os.Stdout, string(data))
}

func logError(component, message string, err error) {
	entry := map[string]interface{}{
		"level":     "error",
		"component": component,
		"message":   message,
		"error":     err.Error(),
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	}
	data, _ := json.Marshal(entry)
	fmt.Fprintln(os.Stderr, string(data))
}
