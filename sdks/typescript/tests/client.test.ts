import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AIPClient, AIPError } from '../src/index';

const mockResponse = {
  success: true,
  intent: 'chat_completion',
  best_match: {
    provider_id: 'openai-gpt4o-mini',
    provider_name: 'OpenAI GPT-4o Mini',
    model: 'gpt-4o-mini',
    price_usd: 0.003,
    latency_ms: 800,
    quality_score: 0.88,
    features: ['function_calling', 'streaming'],
    score: 0.9234,
  },
  alternatives: [],
  resolve_time_ms: 0.42,
};

describe('AIPClient', () => {
  let mockFetch: ReturnType<typeof vi.fn>;
  let client: AIPClient;

  beforeEach(() => {
    mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
      text: () => Promise.resolve(JSON.stringify(mockResponse)),
    });
    client = new AIPClient({
      endpoint: 'https://test.jarvisclaw.ai',
      apiKey: 'test-key',
      fetch: mockFetch as any,
    });
  });

  it('should resolve intent successfully', async () => {
    const result = await client.resolve({
      intent: 'chat_completion',
      constraints: { maxPriceUsd: 0.01 },
      preferences: { optimizeFor: 'cost' },
    });

    expect(result.success).toBe(true);
    expect(result.bestMatch?.providerName).toBe('OpenAI GPT-4o Mini');
    expect(result.bestMatch?.score).toBe(0.9234);
  });

  it('should send correct request format', async () => {
    await client.resolve({
      intent: 'chat_completion',
      constraints: { maxPriceUsd: 0.01, features: ['streaming'] },
    });

    expect(mockFetch).toHaveBeenCalledWith(
      'https://test.jarvisclaw.ai/v1/intent/resolve',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Authorization': 'Bearer test-key',
          'Content-Type': 'application/json',
        }),
      })
    );

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.intent).toBe('chat_completion');
    expect(body.constraints.max_price_usd).toBe(0.01);
    expect(body.constraints.features).toEqual(['streaming']);
  });

  it('should handle errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      text: () => Promise.resolve('Rate limited'),
    });

    await expect(
      client.resolve({ intent: 'chat_completion' })
    ).rejects.toThrow(AIPError);
  });

  it('should use default endpoint', () => {
    const defaultClient = new AIPClient({ fetch: mockFetch as any });
    defaultClient.resolve({ intent: 'chat_completion' });

    expect(mockFetch).toHaveBeenCalledWith(
      'https://api.jarvisclaw.ai/v1/intent/resolve',
      expect.anything()
    );
  });

  it('should convert camelCase to snake_case in requests', async () => {
    await client.resolve({
      intent: 'chat_completion',
      constraints: {
        maxPriceUsd: 0.05,
        maxLatencyMs: 2000,
        minQualityScore: 0.8,
        excludeProviders: ['bad-provider'],
      },
      preferences: {
        optimizeFor: 'quality',
        preferredProviders: ['openai'],
      },
    });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body);
    expect(body.constraints.max_price_usd).toBe(0.05);
    expect(body.constraints.max_latency_ms).toBe(2000);
    expect(body.constraints.min_quality_score).toBe(0.8);
    expect(body.constraints.exclude_providers).toEqual(['bad-provider']);
    expect(body.preferences.optimize_for).toBe('quality');
  });

  it('should convert snake_case to camelCase in responses', async () => {
    const result = await client.resolve({ intent: 'chat_completion' });
    expect(result.bestMatch?.providerId).toBe('openai-gpt4o-mini');
    expect(result.bestMatch?.qualityScore).toBe(0.88);
    expect(result.resolveTimeMs).toBe(0.42);
  });

  it('should list intents', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ intents: ['chat_completion', 'embedding'] }),
    });

    const intents = await client.listIntents();
    expect(intents).toContain('chat_completion');
  });

  it('should list providers with filter', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ providers: [mockResponse.best_match] }),
    });

    const providers = await client.listProviders('chat_completion');
    expect(mockFetch).toHaveBeenCalledWith(
      'https://test.jarvisclaw.ai/v1/providers?intent=chat_completion',
      expect.anything()
    );
    expect(providers[0].providerName).toBe('OpenAI GPT-4o Mini');
  });
});
