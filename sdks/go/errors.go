package aip

import "fmt"

// Error represents an API error from the AIP platform.
type Error struct {
	StatusCode int
	Message    string
	Body       map[string]any
}

func (e *Error) Error() string {
	return fmt.Sprintf("aip: [%d] %s", e.StatusCode, e.Message)
}

// IsNotFound returns true if the error is a 404.
func (e *Error) IsNotFound() bool {
	return e.StatusCode == 404
}

// IsRateLimit returns true if the error is a 429.
func (e *Error) IsRateLimit() bool {
	return e.StatusCode == 429
}

// IsServer returns true if the error is a 5xx.
func (e *Error) IsServer() bool {
	return e.StatusCode >= 500
}
