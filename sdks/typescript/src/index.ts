/**
 * Agent Intent Protocol — TypeScript SDK
 *
 * Default platform: https://api.jarvisclaw.ai
 *
 * @example
 * ```ts
 * import { AIPClient } from '@jarvisclaw/agent-intent-protocol';
 *
 * const client = new AIPClient(); // defaults to api.jarvisclaw.ai
 * const result = await client.resolve({
 *   intent: 'chat_completion',
 *   constraints: { maxPriceUsd: 0.01 },
 *   preferences: { optimizeFor: 'cost' },
 * });
 * ```
 */

export const DEFAULT_ENDPOINT = 'https://api.jarvisclaw.ai';
export const VERSION = '0.1.0';

// ─── Types ───────────────────────────────────────────────────────────────────

export type IntentType =
  | 'chat_completion'
  | 'image_generation'
  | 'text_to_speech'
  | 'speech_to_text'
  | 'embedding'
  | 'code_generation'
  | 'web_search'
  | 'moderation'
  | 'translation';

export type OptimizeFor = 'balanced' | 'quality' | 'speed' | 'cost';
export type Priority = 'low' | 'normal' | 'high' | 'critical';

export interface Constraints {
  maxPriceUsd?: number;
  maxLatencyMs?: number;
  minQualityScore?: number;
  minContextTokens?: number;
  features?: string[];
  excludeProviders?: string[];
  region?: string;
}

export interface Preferences {
  optimizeFor?: OptimizeFor;
  preferredProviders?: string[];
}

export interface Context {
  taskDescription?: string;
  estimatedTokens?: number;
  priority?: Priority;
}

export interface IntentRequest {
  intent: IntentType;
  constraints?: Constraints;
  preferences?: Preferences;
  context?: Context;
}

export interface ProviderMatch {
  providerId: string;
  providerName: string;
  model: string;
  priceUsd: number;
  latencyMs: number;
  qualityScore: number;
  features: string[];
  score: number;
  endpoint?: string;
}

export interface IntentResponse {
  success: boolean;
  intent: IntentType;
  bestMatch?: ProviderMatch;
  alternatives: ProviderMatch[];
  resolveTimeMs: number;
  message?: string;
}

// ─── Client Options ──────────────────────────────────────────────────────────

export interface AIPClientOptions {
  /** API endpoint. Defaults to https://api.jarvisclaw.ai */
  endpoint?: string;
  /** API key for authentication */
  apiKey?: string;
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Custom fetch implementation (for Node.js < 18) */
  fetch?: typeof fetch;
}

// ─── Client ──────────────────────────────────────────────────────────────────

export class AIPClient {
  private endpoint: string;
  private apiKey?: string;
  private timeout: number;
  private fetchFn: typeof fetch;

  constructor(options: AIPClientOptions = {}) {
    this.endpoint = (options.endpoint || DEFAULT_ENDPOINT).replace(/\/$/, '');
    this.apiKey = options.apiKey;
    this.timeout = options.timeout || 30000;
    this.fetchFn = options.fetch || globalThis.fetch;
  }

  /**
   * Resolve an intent to the best matching provider.
   */
  async resolve(request: IntentRequest): Promise<IntentResponse> {
    const body = this.toSnakeCase(request);
    const response = await this.request('POST', '/v1/intent/resolve', body);
    return this.toCamelCase(response) as IntentResponse;
  }

  /**
   * List all supported intent types.
   */
  async listIntents(): Promise<IntentType[]> {
    const response = await this.request('GET', '/v1/intents');
    return response.intents;
  }

  /**
   * List available providers, optionally filtered by intent type.
   */
  async listProviders(intent?: IntentType): Promise<ProviderMatch[]> {
    const url = intent ? `/v1/providers?intent=${intent}` : '/v1/providers';
    const response = await this.request('GET', url);
    return (response.providers || []).map((p: any) => this.toCamelCase(p));
  }

  /**
   * Health check.
   */
  async health(): Promise<{ status: string; version: string }> {
    return this.request('GET', '/v1/health');
  }

  // ─── Private ─────────────────────────────────────────────────────────────

  private async request(method: string, path: string, body?: any): Promise<any> {
    const url = `${this.endpoint}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'User-Agent': `aip-typescript/${VERSION}`,
    };
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await this.fetchFn(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        const text = await response.text();
        throw new AIPError(
          `Server returned ${response.status}: ${text}`,
          response.status
        );
      }

      return response.json();
    } finally {
      clearTimeout(timer);
    }
  }

  private toSnakeCase(obj: any): any {
    if (obj === null || obj === undefined) return obj;
    if (Array.isArray(obj)) return obj.map(v => this.toSnakeCase(v));
    if (typeof obj !== 'object') return obj;
    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      const snakeKey = key.replace(/([A-Z])/g, '_$1').toLowerCase();
      result[snakeKey] = this.toSnakeCase(value);
    }
    return result;
  }

  private toCamelCase(obj: any): any {
    if (obj === null || obj === undefined) return obj;
    if (Array.isArray(obj)) return obj.map(v => this.toCamelCase(v));
    if (typeof obj !== 'object') return obj;
    const result: any = {};
    for (const [key, value] of Object.entries(obj)) {
      const camelKey = key.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
      result[camelKey] = this.toCamelCase(value);
    }
    return result;
  }
}

// ─── Errors ──────────────────────────────────────────────────────────────────

export class AIPError extends Error {
  constructor(message: string, public statusCode?: number) {
    super(message);
    this.name = 'AIPError';
  }
}
