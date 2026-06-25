package aip

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestNewClient(t *testing.T) {
	c := NewClient("test-key")
	if c.endpoint != DefaultEndpoint {
		t.Errorf("expected endpoint %s, got %s", DefaultEndpoint, c.endpoint)
	}
	if c.apiKey != "test-key" {
		t.Errorf("expected apiKey 'test-key', got %s", c.apiKey)
	}
}

func TestNewClientWithEndpoint(t *testing.T) {
	c := NewClient("key", WithEndpoint("https://custom.api"))
	if c.endpoint != "https://custom.api" {
		t.Errorf("expected custom endpoint, got %s", c.endpoint)
	}
}

func TestResolve(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/aip/resolve" {
			t.Errorf("unexpected path: %s", r.URL.Path)
		}
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if r.Header.Get("Authorization") != "Bearer test-key" {
			t.Errorf("missing auth header")
		}

		resp := ResolveResponse{
			Success: true,
			Intent:  "chat",
			BestMatch: &ProviderMatch{
				ProviderID:   "openai",
				ProviderName: "OpenAI",
				Model:        "gpt-4",
				Score:        0.95,
			},
			ResolveTimeMs: 12.5,
		}
		json.NewEncoder(w).Encode(resp)
	}))
	defer srv.Close()

	c := NewClient("test-key", WithEndpoint(srv.URL))
	resp, err := c.Resolve(context.Background(), &IntentRequest{
		Intent: "chat",
		Preferences: &Preferences{
			OptimizeFor: "quality",
		},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !resp.Success {
		t.Error("expected success=true")
	}
	if resp.BestMatch.Model != "gpt-4" {
		t.Errorf("expected model gpt-4, got %s", resp.BestMatch.Model)
	}
}

func TestExecute(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/aip/execute" {
			t.Errorf("unexpected path: %s", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"result": "hello world",
			"tokens": 42,
		})
	}))
	defer srv.Close()

	c := NewClient("key", WithEndpoint(srv.URL))
	resp, err := c.Execute(context.Background(), &ExecuteRequest{
		Intent:  "chat",
		Payload: map[string]any{"messages": []map[string]string{{"role": "user", "content": "hi"}}},
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp["result"] != "hello world" {
		t.Errorf("unexpected result: %v", resp["result"])
	}
}

func TestDiscover(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/aip/discover" {
			t.Errorf("unexpected path: %s", r.URL.Path)
		}
		if r.URL.Query().Get("category") != "ai" {
			t.Errorf("expected category=ai, got %s", r.URL.Query().Get("category"))
		}
		json.NewEncoder(w).Encode(DiscoverResponse{
			Models: []ModelInfo{
				{ID: "gpt-4", Provider: "openai", Name: "GPT-4"},
			},
		})
	}))
	defer srv.Close()

	c := NewClient("key", WithEndpoint(srv.URL))
	resp, err := c.Discover(context.Background(), "ai")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(resp.Models) != 1 || resp.Models[0].ID != "gpt-4" {
		t.Errorf("unexpected models: %+v", resp.Models)
	}
}

func TestHealth(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewEncoder(w).Encode(HealthResponse{
			Status:  "healthy",
			Version: "2.0.0",
		})
	}))
	defer srv.Close()

	c := NewClient("key", WithEndpoint(srv.URL))
	resp, err := c.Health(context.Background())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.Status != "healthy" {
		t.Errorf("expected healthy, got %s", resp.Status)
	}
}

func TestErrorHandling(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusTooManyRequests)
		json.NewEncoder(w).Encode(map[string]string{"error": "rate limited"})
	}))
	defer srv.Close()

	c := NewClient("key", WithEndpoint(srv.URL))
	_, err := c.Health(context.Background())
	if err == nil {
		t.Fatal("expected error")
	}
	apiErr, ok := err.(*Error)
	if !ok {
		t.Fatalf("expected *Error, got %T", err)
	}
	if !apiErr.IsRateLimit() {
		t.Errorf("expected rate limit error, got status %d", apiErr.StatusCode)
	}
	if apiErr.Message != "rate limited" {
		t.Errorf("expected 'rate limited', got %s", apiErr.Message)
	}
}
