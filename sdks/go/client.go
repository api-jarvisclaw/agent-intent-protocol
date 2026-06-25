// Package aip provides a thin HTTP client for the Agent Intent Protocol.
//
// The AIP client allows AI agents to declare what they need (intent + constraints)
// and lets the platform decide how to fulfill it optimally.
//
// Usage:
//
//	client := aip.NewClient("your-api-key")
//	resp, err := client.Resolve(ctx, &aip.IntentRequest{
//	    Intent: "chat",
//	    Preferences: &aip.Preferences{OptimizeFor: "quality"},
//	})
package aip

import (
	"bytes"
	"context"
	"crypto/ecdsa"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"time"

	"github.com/ethereum/go-ethereum/crypto"
)

const (
	// DefaultEndpoint is the default AIP platform URL.
	DefaultEndpoint = "https://api.jarvisclaw.ai"
	// DefaultTimeout is the default HTTP timeout.
	DefaultTimeout = 30 * time.Second
)

// Client is a thin HTTP client for the AIP platform.
type Client struct {
	endpoint   string
	apiKey     string
	privateKey *ecdsa.PrivateKey
	httpClient *http.Client
}

// Option configures the Client.
type Option func(*Client)

// WithEndpoint overrides the default platform endpoint.
func WithEndpoint(endpoint string) Option {
	return func(c *Client) {
		c.endpoint = endpoint
	}
}

// WithHTTPClient provides a custom http.Client.
func WithHTTPClient(hc *http.Client) Option {
	return func(c *Client) {
		c.httpClient = hc
	}
}

// WithTimeout sets the HTTP client timeout.
func WithTimeout(d time.Duration) Option {
	return func(c *Client) {
		c.httpClient.Timeout = d
	}
}

// WithPrivateKey sets a hex-encoded Ethereum private key for wallet auth (EIP-191).
func WithPrivateKey(hexKey string) Option {
	return func(c *Client) {
		key, err := crypto.HexToECDSA(hexKey)
		if err == nil {
			c.privateKey = key
		}
	}
}

// NewClient creates a new AIP client with an explicit API key.
func NewClient(apiKey string, opts ...Option) *Client {
	c := &Client{
		endpoint: DefaultEndpoint,
		apiKey:   apiKey,
		httpClient: &http.Client{
			Timeout: DefaultTimeout,
		},
	}
	for _, opt := range opts {
		opt(c)
	}
	return c
}

// NewClientFromEnv creates a client using environment variables.
// Priority: JARVISCLAW_API_KEY > AIP_API_KEY for api_key,
// JARVISCLAW_PRIVATE_KEY > AIP_PRIVATE_KEY for wallet auth.
// AIP_ENDPOINT overrides the default endpoint.
func NewClientFromEnv(opts ...Option) *Client {
	apiKey := os.Getenv("JARVISCLAW_API_KEY")
	if apiKey == "" {
		apiKey = os.Getenv("AIP_API_KEY")
	}

	c := &Client{
		endpoint: DefaultEndpoint,
		apiKey:   apiKey,
		httpClient: &http.Client{
			Timeout: DefaultTimeout,
		},
	}

	// Private key from env
	pk := os.Getenv("JARVISCLAW_PRIVATE_KEY")
	if pk == "" {
		pk = os.Getenv("AIP_PRIVATE_KEY")
	}
	if pk != "" {
		if key, err := crypto.HexToECDSA(pk); err == nil {
			c.privateKey = key
		}
	}

	// Endpoint override
	if ep := os.Getenv("AIP_ENDPOINT"); ep != "" {
		c.endpoint = ep
	}

	for _, opt := range opts {
		opt(c)
	}
	return c
}

// ─── Core Methods ────────────────────────────────────────────

// Resolve resolves an intent to the best provider without executing it.
func (c *Client) Resolve(ctx context.Context, req *IntentRequest) (*ResolveResponse, error) {
	var resp ResolveResponse
	if err := c.post(ctx, "/v1/aip/resolve", req, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// Execute resolves and immediately executes an intent in one call.
func (c *Client) Execute(ctx context.Context, req *ExecuteRequest) (ExecuteResponse, error) {
	var resp ExecuteResponse
	if err := c.post(ctx, "/v1/aip/execute", req, &resp); err != nil {
		return nil, err
	}
	return resp, nil
}

// Discover lists available intents and services on the platform.
func (c *Client) Discover(ctx context.Context, category string) (*DiscoverResponse, error) {
	params := url.Values{}
	if category != "" {
		params.Set("category", category)
	}
	var resp DiscoverResponse
	if err := c.get(ctx, "/v1/aip/discover", params, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// ─── Convenience: Chat ──────────────────────────────────────

// Chat sends a chat completion request through the AIP intent system.
func (c *Client) Chat(ctx context.Context, req *ChatRequest) (*ChatResponse, error) {
	execReq := &ExecuteRequest{
		Intent: "chat",
		Payload: map[string]any{
			"messages": req.Messages,
		},
	}
	if req.Model != "" {
		execReq.Payload["model"] = req.Model
	}
	if req.Temperature != nil {
		execReq.Payload["temperature"] = *req.Temperature
	}
	if req.MaxTokens != nil {
		execReq.Payload["max_tokens"] = *req.MaxTokens
	}
	if req.TopP != nil {
		execReq.Payload["top_p"] = *req.TopP
	}

	var resp ChatResponse
	if err := c.post(ctx, "/v1/aip/execute", execReq, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// ChatDirect sends a direct OpenAI-compatible chat completion request.
func (c *Client) ChatDirect(ctx context.Context, req *ChatRequest) (*ChatResponse, error) {
	var resp ChatResponse
	if err := c.post(ctx, "/v1/chat/completions", req, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// ─── Convenience: Media ─────────────────────────────────────

// GenerateImage generates an image from a text prompt.
func (c *Client) GenerateImage(ctx context.Context, prompt string, opts map[string]any) (ExecuteResponse, error) {
	payload := map[string]any{"prompt": prompt}
	for k, v := range opts {
		payload[k] = v
	}
	return c.Execute(ctx, &ExecuteRequest{
		Intent:  "image_generation",
		Payload: payload,
	})
}

// GenerateVideo generates a video from a text prompt.
func (c *Client) GenerateVideo(ctx context.Context, prompt string, opts map[string]any) (ExecuteResponse, error) {
	payload := map[string]any{"prompt": prompt}
	for k, v := range opts {
		payload[k] = v
	}
	return c.Execute(ctx, &ExecuteRequest{
		Intent:  "video_generation",
		Payload: payload,
	})
}

// TextToSpeech converts text to audio.
func (c *Client) TextToSpeech(ctx context.Context, text string, opts map[string]any) (ExecuteResponse, error) {
	payload := map[string]any{"text": text}
	for k, v := range opts {
		payload[k] = v
	}
	return c.Execute(ctx, &ExecuteRequest{
		Intent:  "text_to_speech",
		Payload: payload,
	})
}

// ─── Convenience: Services ──────────────────────────────────

// Search performs a web search.
func (c *Client) Search(ctx context.Context, query string, opts map[string]any) (ExecuteResponse, error) {
	payload := map[string]any{"query": query}
	for k, v := range opts {
		payload[k] = v
	}
	return c.Execute(ctx, &ExecuteRequest{
		Intent:  "search",
		Payload: payload,
	})
}

// Marketplace interacts with the marketplace.
func (c *Client) Marketplace(ctx context.Context, action string, params map[string]any) (ExecuteResponse, error) {
	payload := map[string]any{"action": action}
	for k, v := range params {
		payload[k] = v
	}
	return c.Execute(ctx, &ExecuteRequest{
		Intent:  "marketplace",
		Payload: payload,
	})
}

// ─── Utility ────────────────────────────────────────────────

// Health checks the platform health.
func (c *Client) Health(ctx context.Context) (*HealthResponse, error) {
	var resp HealthResponse
	if err := c.get(ctx, "/v1/aip/health", nil, &resp); err != nil {
		return nil, err
	}
	return &resp, nil
}

// Models lists available models (alias for Discover with "ai" category).
func (c *Client) Models(ctx context.Context) (*DiscoverResponse, error) {
	return c.Discover(ctx, "ai")
}

// ─── HTTP Internals ─────────────────────────────────────────

func (c *Client) post(ctx context.Context, path string, body any, result any) error {
	data, err := json.Marshal(body)
	if err != nil {
		return fmt.Errorf("aip: marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.endpoint+path, bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("aip: create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	c.setAuth(req)

	return c.do(req, result)
}

func (c *Client) get(ctx context.Context, path string, params url.Values, result any) error {
	u := c.endpoint + path
	if len(params) > 0 {
		u += "?" + params.Encode()
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return fmt.Errorf("aip: create request: %w", err)
	}
	c.setAuth(req)

	return c.do(req, result)
}

// setAuth applies authentication headers to the request.
// If privateKey is set, uses EIP-191 wallet signature.
// Otherwise falls back to Bearer token with apiKey.
func (c *Client) setAuth(req *http.Request) {
	if c.privateKey != nil {
		timestamp := strconv.FormatInt(time.Now().Unix(), 10)
		message := "aip-auth:" + timestamp
		hash := crypto.Keccak256Hash([]byte(fmt.Sprintf("\x19Ethereum Signed Message:\n%d%s", len(message), message)))
		sig, err := crypto.Sign(hash.Bytes(), c.privateKey)
		if err == nil {
			address := crypto.PubkeyToAddress(c.privateKey.PublicKey)
			req.Header.Set("X-Wallet-Address", address.Hex())
			req.Header.Set("X-Timestamp", timestamp)
			req.Header.Set("X-Signature", hex.EncodeToString(sig))
		}
	} else if c.apiKey != "" {
		req.Header.Set("Authorization", "Bearer "+c.apiKey)
	}
}

func (c *Client) do(req *http.Request, result any) error {
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("aip: http error: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("aip: read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		apiErr := &Error{
			StatusCode: resp.StatusCode,
			Message:    http.StatusText(resp.StatusCode),
		}
		// Try to parse error body for more detail
		var errBody map[string]any
		if json.Unmarshal(respBody, &errBody) == nil {
			apiErr.Body = errBody
			if msg, ok := errBody["error"].(string); ok {
				apiErr.Message = msg
			} else if detail, ok := errBody["detail"].(string); ok {
				apiErr.Message = detail
			}
		}
		return apiErr
	}

	if result != nil {
		if err := json.Unmarshal(respBody, result); err != nil {
			return fmt.Errorf("aip: decode response: %w", err)
		}
	}
	return nil
}
