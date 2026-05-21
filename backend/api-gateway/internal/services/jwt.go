package services

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/config"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/models"
)

// JWTClaims represents the claims embedded in a JWT token.
type JWTClaims struct {
	UserID string      `json:"user_id"`
	Email  string      `json:"email"`
	Role   models.Role `json:"role"`
	Exp    int64       `json:"exp"`
	Iat    int64       `json:"iat"`
}

// JWTService handles JWT token generation and validation.
type JWTService struct {
	secret        []byte
	accessExpiry  time.Duration
	refreshExpiry time.Duration
}

// NewJWTService creates a new JWTService from config.
func NewJWTService(cfg *config.Config) *JWTService {
	return &JWTService{
		secret:        []byte(cfg.JWTSecret),
		accessExpiry:  cfg.JWTExpiry,
		refreshExpiry: cfg.RefreshExpiry,
	}
}

var (
	ErrInvalidToken = errors.New("invalid token")
	ErrExpiredToken = errors.New("token has expired")
	ErrInvalidSignature = errors.New("invalid token signature")
)

// GenerateAccessToken generates a new access token for the given user.
func (s *JWTService) GenerateAccessToken(user *models.User) (string, error) {
	claims := JWTClaims{
		UserID: user.ID,
		Email:  user.Email,
		Role:   user.Role,
		Iat:    time.Now().Unix(),
		Exp:    time.Now().Add(s.accessExpiry).Unix(),
	}
	return s.encode(claims)
}

// GenerateRefreshToken generates a new refresh token for the given user.
func (s *JWTService) GenerateRefreshToken(user *models.User) (string, error) {
	claims := JWTClaims{
		UserID: user.ID,
		Email:  user.Email,
		Role:   user.Role,
		Iat:    time.Now().Unix(),
		Exp:    time.Now().Add(s.refreshExpiry).Unix(),
	}
	return s.encode(claims)
}

// ValidateToken validates the token signature and expiry, returning claims if valid.
func (s *JWTService) ValidateToken(tokenString string) (*JWTClaims, error) {
	parts := strings.Split(tokenString, ".")
	if len(parts) != 3 {
		return nil, ErrInvalidToken
	}

	// Verify signature
	signatureInput := parts[0] + "." + parts[1]
	expectedSig := s.sign([]byte(signatureInput))
	actualSig, err := base64URLDecode(parts[2])
	if err != nil {
		return nil, ErrInvalidToken
	}

	if !hmac.Equal(expectedSig, actualSig) {
		return nil, ErrInvalidSignature
	}

	// Decode claims
	claimsJSON, err := base64URLDecode(parts[1])
	if err != nil {
		return nil, ErrInvalidToken
	}

	var claims JWTClaims
	if err := json.Unmarshal(claimsJSON, &claims); err != nil {
		return nil, ErrInvalidToken
	}

	// Check expiry
	if time.Now().Unix() > claims.Exp {
		return nil, ErrExpiredToken
	}

	return &claims, nil
}

// ParseClaims extracts claims from a token without full validation (no expiry check).
func (s *JWTService) ParseClaims(tokenString string) (*JWTClaims, error) {
	parts := strings.Split(tokenString, ".")
	if len(parts) != 3 {
		return nil, ErrInvalidToken
	}

	claimsJSON, err := base64URLDecode(parts[1])
	if err != nil {
		return nil, ErrInvalidToken
	}

	var claims JWTClaims
	if err := json.Unmarshal(claimsJSON, &claims); err != nil {
		return nil, ErrInvalidToken
	}

	return &claims, nil
}

func (s *JWTService) encode(claims JWTClaims) (string, error) {
	header := map[string]string{
		"alg": "HS256",
		"typ": "JWT",
	}

	headerJSON, err := json.Marshal(header)
	if err != nil {
		return "", fmt.Errorf("failed to marshal header: %w", err)
	}

	claimsJSON, err := json.Marshal(claims)
	if err != nil {
		return "", fmt.Errorf("failed to marshal claims: %w", err)
	}

	headerEncoded := base64URLEncode(headerJSON)
	claimsEncoded := base64URLEncode(claimsJSON)

	signatureInput := headerEncoded + "." + claimsEncoded
	signature := s.sign([]byte(signatureInput))
	signatureEncoded := base64URLEncode(signature)

	return signatureInput + "." + signatureEncoded, nil
}

func (s *JWTService) sign(data []byte) []byte {
	mac := hmac.New(sha256.New, s.secret)
	mac.Write(data)
	return mac.Sum(nil)
}

func base64URLEncode(data []byte) string {
	return base64.RawURLEncoding.EncodeToString(data)
}

func base64URLDecode(s string) ([]byte, error) {
	return base64.RawURLEncoding.DecodeString(s)
}
