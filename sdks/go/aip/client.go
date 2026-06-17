// Package aip implements the Agent Intent Protocol client for Go.
//
// Default platform: https://api.jarvisclaw.ai
//
// Usage:
//
//	client := aip.NewClient() // connects to api.jarvisclaw.ai
//	result, err := client.Resolve(aip.IntentRequest{
//	    Intent: aip.ChatCompletion,
//	    Constraints: &aip.Constraints{MaxPriceUSD: ptr(0.01)},
//	    Preferences: &aip.Preferences{OptimizeFor: aip.OptimizeCost},
//	})
package aip

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	DefaultEndpoint = "https://api.jarvisclaw.ai"
	Version         = "0.1.0"
)

// Intent types
type IntentType string

const (
	ChatCompletion  IntentType = "chat_completion"
	ImageGeneration IntentType = "image_generation"
	TextToSpeech    IntentType = "text_to_speech"
	SpeechToText    IntentType = "speech_to_text"
	Embedding       IntentType = "embedding"
	CodeGeneration  IntentType = "code_generation"
	WebSearch       IntentType = "web_search"
	Moderation      IntentType = "moderation"
	Translation     IntentType = "translation"
)

// OptimizeFor strategy
type OptimizeFor string

const (
	OptimizeBalanced OptimizeFor = "balanced"
	OptimizeQuality  OptimizeFor = "quality"
	OptimizeSpeed    OptimizeFor = "speed"
	OptimizeCost     OptimizeFor = "cost"
)

// Priority levels
type Priority string

const (
	PriorityLow      Priority = "low"
	PriorityNormal   Priority = "normal"
	PriorityHigh     Priority = "high"
	PriorityCritical Priority = "critical"
)

// IntentRequest represents a request to resolve an intent.
type IntentRequest struct {
	Intent      IntentType   `json:"intent"`
	Constraints *Constraints `json:"constraints,omitempty"`
	Preferences *Preferences `json:"preferences,omitempty"`
	Context     *Context     `json:"context,omitempty"`
}

// Constraints are hard requirements providers must satisfy.
type Constraints struct {
	MaxPriceUSD      *float64 `json:"max_price_usd,omitempty"`
	MaxLatencyMs     *int     `json:"max_latency_ms,omitempty"`
	MinQualityScore  *float64 `json:"min_quality_score,omitempty"`
	MinContextTokens *int     `json:"min_context_tokens,omitempty"`
	Features         []string `json:"features,omitempty"`
	ExcludeProviders []string `json:"exclude_providers,omitempty"`
	Region           string   `json:"region,omitempty"`
}

// Preferences are soft optimization directives.
type Preferences struct {
	OptimizeFor        OptimizeFor `json:"optimize_for,omitempty"`
	PreferredProviders []string    `json:"preferred_providers,omitempty"`
}

// Context provides additional information for resolution.
type Context struct {
	TaskDescription string   `json:"task_description,omitempty"`
	EstimatedTokens int      `json:"estimated_tokens,omitempty"`
	Priority        Priority `json:"priority,omitempty"`
}

// ProviderMatch represents a matched provider.
type ProviderMatch struct {
	ProviderID   string   `json:"provider_id"`
	ProviderName string   `json:"provider_name"`
	Model        string   `json:"model"`
	PriceUSD     float64  `json:"price_usd"`
	LatencyMs    int      `json:"latency_ms"`
	QualityScore float64  `json:"quality_score"`
	Features     []string `json:"features"`
	Score        float64  `json:"score"`
	Endpoint     string   `json:"endpoint,omitempty"`
}

// IntentResponse is the resolution result.
type IntentResponse struct {
	Success       bool            `json:"success"`
	Intent        IntentType      `json:"intent"`
	BestMatch     *ProviderMatch  `json:"best_match,omitempty"`
	Alternatives  []ProviderMatch `json:"alternatives,omitempty"`
	ResolveTimeMs float64         `json:"resolve_time_ms"`
	Message       string          `json:"message,omitempty"`
}

// ClientOption configures the AIP client.
type ClientOption func(*Client)

// WithEndpoint sets a custom endpoint.
func WithEndpoint(endpoint string) ClientOption {
	return func(c *Client) { c.endpoint = endpoint }
}

// WithAPIKey sets the API key for authentication.
func WithAPIKey(key string) ClientOption {
	return func(c *Client) { c.apiKey = key }
}

// WithHTTPClient sets a custom HTTP client.
func WithHTTPClient(hc *http.Client) ClientOption {
	return func(c *Client) { c.httpClient = hc }
}

// WithTimeout sets the request timeout.
func WithTimeout(d time.Duration) ClientOption {
	return func(c *Client) { c.httpClient.Timeout = d }
}

// Client is the Agent Intent Protocol client.
type Client struct {
	endpoint   string
	apiKey     string
	httpClient *http.Client
}

// NewClient creates a new AIP client. Defaults to https://api.jarvisclaw.ai.
func NewClient(opts ...ClientOption) *Client {
	c := &Client{
		endpoint:   DefaultEndpoint,
		httpClient: &http.Client{Timeout: 30 * time.Second},
	}
	for _, opt := range opts {
		opt(c)
	}
	return c
}

// Resolve resolves an intent to the best matching provider.
func (c *Client) Resolve(req IntentRequest) (*IntentResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("aip: marshal request: %w", err)
	}

	httpReq, err := http.NewRequest("POST", c.endpoint+"/v1/intent/resolve", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("aip: create request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("User-Agent", "aip-go/"+Version)
	if c.apiKey != "" {
		httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)
	}

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("aip: request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("aip: read response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("aip: server returned %d: %s", resp.StatusCode, string(respBody))
	}

	var result IntentResponse
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("aip: unmarshal response: %w", err)
	}
	return &result, nil
}

// ListIntents returns all supported intent types.
func (c *Client) ListIntents() ([]IntentType, error) {
	httpReq, err := http.NewRequest("GET", c.endpoint+"/v1/intents", nil)
	if err != nil {
		return nil, err
	}
	c.setHeaders(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result struct {
		Intents []IntentType `json:"intents"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.Intents, nil
}

// ListProviders returns available providers, optionally filtered by intent.
func (c *Client) ListProviders(intent IntentType) ([]ProviderMatch, error) {
	url := c.endpoint + "/v1/providers"
	if intent != "" {
		url += "?intent=" + string(intent)
	}

	httpReq, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	c.setHeaders(httpReq)

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result struct {
		Providers []ProviderMatch `json:"providers"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.Providers, nil
}

func (c *Client) setHeaders(req *http.Request) {
	req.Header.Set("User-Agent", "aip-go/"+Version)
	if c.apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+c.apiKey)
	}
}

// Ptr helpers for optional fields
func Float64(v float64) *float64 { return &v }
func Int(v int) *int             { return &v }
