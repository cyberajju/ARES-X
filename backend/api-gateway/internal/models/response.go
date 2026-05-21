package models

// ApiResponse is a generic API response wrapper.
type ApiResponse[T any] struct {
	Success bool   `json:"success"`
	Data    T      `json:"data,omitempty"`
	Message string `json:"message,omitempty"`
}

// PaginatedResponse is a generic paginated API response wrapper.
type PaginatedResponse[T any] struct {
	Success    bool   `json:"success"`
	Data       []T    `json:"data"`
	Total      int    `json:"total"`
	Page       int    `json:"page"`
	PageSize   int    `json:"page_size"`
	TotalPages int    `json:"total_pages"`
	Message    string `json:"message,omitempty"`
}

// ErrorResponse represents an API error response.
type ErrorResponse struct {
	Success bool              `json:"success"`
	Error   string            `json:"error"`
	Code    string            `json:"code,omitempty"`
	Details []ValidationError `json:"details,omitempty"`
}

// ValidationError represents a field validation error.
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
}
