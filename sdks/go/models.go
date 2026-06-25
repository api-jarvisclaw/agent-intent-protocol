package aip

// IntentRequest is the payload for resolving an intent.
type IntentRequest struct {
	Intent      string            `json:"intent"`
	Constraints *Constraints      `json:"constraints,omitempty"`
	Preferences *Preferences      `json:"preferences,omitempty"`
	Context     map[string]any    `json:"context,omitempty"`
}

// Constraints are hard requirements that providers must satisfy.
type Constraints struct {
	MaxPriceUSD      float64  `json:"max_price_usd,omitempty"`
	MaxLatencyMs     int      `json:"max_latency_ms,omitempty"`
	MinQualityScore  float64  `json:"min_quality_score,omitempty"`
	Features         []string `json:"features,omitempty"`
	ExcludeProviders []string `json:"exclude_providers,omitempty"`
}

// Preferences are soft optimization directives.
type Preferences struct {
	OptimizeFor        string   `json:"optimize_for,omitempty"`
	PreferredProviders []string `json:"preferred_providers,omitempty"`
}

// ResolveResponse is the response from intent resolution.
type ResolveResponse struct {
	Success       bool          `json:"success"`
	Intent        string        `json:"intent"`
	BestMatch     *ProviderMatch `json:"best_match,omitempty"`
	Alternatives  []ProviderMatch `json:"alternatives,omitempty"`
	ResolveTimeMs float64       `json:"resolve_time_ms"`
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
	Endpoint     string   `json:"endpoint"`
}

// ExecuteRequest is the payload for executing an intent.
type ExecuteRequest struct {
	Intent      string         `json:"intent"`
	Payload     map[string]any `json:"payload"`
	OptimizeFor string         `json:"optimize_for,omitempty"`
	Stream      bool           `json:"stream,omitempty"`
}

// ExecuteResponse is a generic response from execution.
type ExecuteResponse map[string]any

// DiscoverResponse contains available intents and services.
type DiscoverResponse struct {
	Intents  []IntentInfo  `json:"intents,omitempty"`
	Services []ServiceInfo `json:"services,omitempty"`
	Models   []ModelInfo   `json:"models,omitempty"`
}

// IntentInfo describes an available intent type.
type IntentInfo struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Category    string `json:"category"`
}

// ServiceInfo describes an available service.
type ServiceInfo struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	Actions     []string `json:"actions,omitempty"`
}

// ModelInfo describes an available model.
type ModelInfo struct {
	ID           string   `json:"id"`
	Provider     string   `json:"provider"`
	Name         string   `json:"name"`
	Features     []string `json:"features,omitempty"`
	PricePerToken float64 `json:"price_per_token,omitempty"`
}

// HealthResponse is the response from health check.
type HealthResponse struct {
	Status  string `json:"status"`
	Version string `json:"version"`
}

// ChatMessage represents a single message in a chat conversation.
type ChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatRequest is the payload for chat completions.
type ChatRequest struct {
	Model       string        `json:"model,omitempty"`
	Messages    []ChatMessage `json:"messages"`
	Stream      bool          `json:"stream,omitempty"`
	Temperature *float64      `json:"temperature,omitempty"`
	MaxTokens   *int          `json:"max_tokens,omitempty"`
	TopP        *float64      `json:"top_p,omitempty"`
}

// ChatResponse is the response from chat completions.
type ChatResponse struct {
	ID      string         `json:"id"`
	Object  string         `json:"object"`
	Choices []ChatChoice   `json:"choices"`
	Usage   *ChatUsage     `json:"usage,omitempty"`
}

// ChatChoice is a single choice in a chat response.
type ChatChoice struct {
	Index        int         `json:"index"`
	Message      ChatMessage `json:"message"`
	FinishReason string      `json:"finish_reason"`
}

// ChatUsage contains token usage info.
type ChatUsage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}
