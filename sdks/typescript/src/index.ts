/**
 * Agent Intent Protocol — TypeScript SDK v2.1
 *
 * Thin HTTP client for the AIP platform.
 * Declares intents, the platform handles provider selection + execution.
 *
 * @example
 * ```ts
 * import { AIPClient } from '@jarvisclaw/agent-intent-protocol';
 *
 * const client = new AIPClient({ apiKey: 'sk-...' });
 *
 * // One call does everything
 * const result = await client.execute('chat_completion', {
 *   messages: [{ role: 'user', content: 'Hello' }],
 * });
 *
 * // Streaming
 * for await (const chunk of client.stream('chat_completion', {
 *   messages: [{ role: 'user', content: 'Tell me a story' }],
 * })) {
 *   process.stdout.write(chunk.choices[0]?.delta?.content ?? '');
 * }
 * ```
 */

// ─── Types ───────────────────────────────────────────────────────────────────

export type OptimizeStrategy = 'balanced' | 'cost' | 'speed' | 'quality';

export interface AIPClientOptions {
  /** API key (Bearer token). Falls back to AIP_API_KEY env var. */
  apiKey?: string;
  /** Base URL. Default: https://api.jarvisclaw.ai */
  endpoint?: string;
  /** Default optimization strategy. Default: 'balanced' */
  optimize?: OptimizeStrategy;
  /** Request timeout in ms. Default: 30000 */
  timeout?: number;
  /** Max retry attempts for transient errors. Default: 2 */
  maxRetries?: number;
  /** Custom headers merged into every request. */
  headers?: Record<string, string>;
}

export interface AIPConstraints {
  max_price_per_token?: number;
  max_price_usd?: number;
  features?: string[];
  exclude_models?: string[];
  prefer_models?: string[];
  [key: string]: unknown;
}

export interface ExecuteRequest {
  intent: string;
  payload: Record<string, unknown>;
  optimize_for?: OptimizeStrategy;
  constraints?: AIPConstraints;
  stream?: boolean;
}

export interface AIPMeta {
  model: string;
  provider: string;
  cost_usd: number;
  latency_ms: number;
  resolve_time_ms: number;
}

export interface AIPResponse<T = unknown> {
  success: true;
  data: T;
  meta: AIPMeta;
}

export interface AIPErrorBody {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ResolveResult {
  success: true;
  intent: string;
  resolution: {
    model: string;
    provider: string;
    endpoint: string;
    score: number;
    reason: string;
    price: Record<string, number>;
    latency_ms: number;
  };
  alternatives: Array<{ model: string; provider: string; score: number }>;
}

export interface DiscoverResult {
  intents: Array<{
    name: string;
    description: string;
    category: string;
    payload_schema?: Record<string, unknown>;
  }>;
  models: Array<{
    id: string;
    provider: string;
    capabilities: string[];
    pricing: { input: number; output: number };
  }>;
  services: Array<{
    name: string;
    description: string;
    actions: string[];
  }>;
}

export interface HealthResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  providers_online: number;
  uptime_seconds: number;
}

// ─── Streaming types ─────────────────────────────────────────────────────────

export interface StreamDelta {
  choices: Array<{
    index: number;
    delta: { role?: string; content?: string };
    finish_reason: string | null;
  }>;
  /** Present only on the final chunk */
  meta?: AIPMeta;
}

// ─── Error class ─────────────────────────────────────────────────────────────

export class AIPError extends Error {
  public readonly statusCode: number;
  public readonly code: string;
  public readonly details?: Record<string, unknown>;
  public readonly requestId?: string;

  constructor(statusCode: number, body: AIPErrorBody, requestId?: string) {
    super(`[${body.code}] ${body.message}`);
    this.name = 'AIPError';
    this.statusCode = statusCode;
    this.code = body.code;
    this.details = body.details;
    this.requestId = requestId;
  }

  get retryable(): boolean {
    return [429, 500, 502, 503, 504].includes(this.statusCode);
  }
}

// ─── Client ──────────────────────────────────────────────────────────────────

const DEFAULT_ENDPOINT = 'https://api.jarvisclaw.ai';
const DEFAULT_TIMEOUT = 30_000;
const DEFAULT_MAX_RETRIES = 2;
const RETRYABLE_STATUS = new Set([429, 500, 502, 503, 504]);

export class AIPClient {
  private readonly apiKey: string;
  private readonly endpoint: string;
  private readonly optimize: OptimizeStrategy;
  private readonly timeout: number;
  private readonly maxRetries: number;
  private readonly headers: Record<string, string>;

  constructor(options: AIPClientOptions = {}) {
    this.apiKey = options.apiKey ?? this.envVar('AIP_API_KEY') ?? '';
    if (!this.apiKey) {
      throw new Error('AIP API key is required. Pass apiKey option or set AIP_API_KEY env var.');
    }
    this.endpoint = (options.endpoint ?? this.envVar('AIP_ENDPOINT') ?? DEFAULT_ENDPOINT).replace(/\/$/, '');
    this.optimize = options.optimize ?? 'balanced';
    this.timeout = options.timeout ?? DEFAULT_TIMEOUT;
    this.maxRetries = options.maxRetries ?? DEFAULT_MAX_RETRIES;
    this.headers = options.headers ?? {};
  }

  // ─── Core API ────────────────────────────────────────────────────────────

  /**
   * Execute an intent. The platform resolves the best provider and executes.
   */
  async execute<T = unknown>(
    intent: string,
    payload: Record<string, unknown>,
    options: {
      optimize_for?: OptimizeStrategy;
      constraints?: AIPConstraints;
    } = {}
  ): Promise<AIPResponse<T>> {
    const body: ExecuteRequest = {
      intent,
      payload,
      optimize_for: options.optimize_for ?? this.optimize,
      constraints: options.constraints,
    };
    return this.post<AIPResponse<T>>('/v1/aip/execute', body);
  }

  /**
   * Stream an intent response. Returns an async iterator of SSE chunks.
   */
  async *stream(
    intent: string,
    payload: Record<string, unknown>,
    options: {
      optimize_for?: OptimizeStrategy;
      constraints?: AIPConstraints;
    } = {}
  ): AsyncGenerator<StreamDelta, void, unknown> {
    const body: ExecuteRequest = {
      intent,
      payload,
      optimize_for: options.optimize_for ?? this.optimize,
      constraints: options.constraints,
      stream: true,
    };

    const response = await this.rawFetch('/v1/aip/execute', {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
    });

    if (!response.ok) {
      await this.handleError(response);
    }

    if (!response.body) {
      throw new AIPError(500, { code: 'STREAM_NOT_SUPPORTED', message: 'Response has no body' });
    }

    yield* this.parseSSE(response.body);
  }

  /**
   * Resolve an intent to the best provider without executing.
   */
  async resolve(
    intent: string,
    options: {
      optimize_for?: OptimizeStrategy;
      constraints?: AIPConstraints;
      context?: Record<string, unknown>;
    } = {}
  ): Promise<ResolveResult> {
    return this.post<ResolveResult>('/v1/aip/resolve', {
      intent,
      optimize_for: options.optimize_for ?? this.optimize,
      constraints: options.constraints,
      context: options.context,
    });
  }

  /**
   * Discover available intents, models, and services.
   */
  async discover(category?: string): Promise<DiscoverResult> {
    const params = category ? `?category=${encodeURIComponent(category)}` : '';
    return this.get<DiscoverResult>(`/v1/aip/discover${params}`);
  }

  /**
   * Platform health check.
   */
  async health(): Promise<HealthResult> {
    return this.get<HealthResult>('/v1/aip/health');
  }

  // ─── Convenience Methods ─────────────────────────────────────────────────

  /** Chat completion shorthand. */
  async chat(
    messages: Array<{ role: string; content: string }>,
    options: { model?: string; temperature?: number; max_tokens?: number; [k: string]: unknown } = {}
  ): Promise<AIPResponse> {
    const { model, ...rest } = options;
    return this.execute('chat_completion', { messages, ...rest }, {
      constraints: model ? { prefer_models: [model] } : undefined,
    });
  }

  /** Image generation shorthand. */
  async imageGenerate(prompt: string, options: Record<string, unknown> = {}): Promise<AIPResponse> {
    return this.execute('image_generation', { prompt, ...options });
  }

  /** Embedding shorthand. */
  async embed(input: string | string[], options: Record<string, unknown> = {}): Promise<AIPResponse> {
    return this.execute('embedding', { input, ...options });
  }

  /** Web search shorthand. */
  async search(query: string, options: Record<string, unknown> = {}): Promise<AIPResponse> {
    return this.execute('web_search', { query, ...options });
  }

  /** Text to speech shorthand. */
  async tts(text: string, voice: string = 'alloy', options: Record<string, unknown> = {}): Promise<AIPResponse> {
    return this.execute('text_to_speech', { input: text, voice, ...options });
  }

  /** Speech to text shorthand. */
  async stt(audio: Blob | ArrayBuffer, options: Record<string, unknown> = {}): Promise<AIPResponse> {
    return this.execute('speech_to_text', { audio, ...options });
  }

  /** Code generation shorthand. */
  async code(prompt: string, language?: string, options: Record<string, unknown> = {}): Promise<AIPResponse> {
    return this.execute('code_generation', { prompt, language, ...options });
  }

  /** Translation shorthand. */
  async translate(text: string, targetLang: string, options: Record<string, unknown> = {}): Promise<AIPResponse> {
    return this.execute('translation', { text, target_language: targetLang, ...options });
  }

  // ─── HTTP Layer with Retry ───────────────────────────────────────────────

  private async post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'Content-Type': 'application/json' },
    });
  }

  private async get<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'GET' });
  }

  private async request<T>(path: string, init: RequestInit): Promise<T> {
    let lastError: AIPError | Error | undefined;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      if (attempt > 0 && lastError) {
        const delay = this.retryDelay(attempt, lastError);
        await this.sleep(delay);
      }

      try {
        const response = await this.rawFetch(path, init);

        if (response.ok) {
          return (await response.json()) as T;
        }

        const error = await this.buildError(response);

        if (!RETRYABLE_STATUS.has(response.status) || attempt === this.maxRetries) {
          throw error;
        }

        lastError = error;
      } catch (err) {
        if (err instanceof AIPError) {
          if (!err.retryable || attempt === this.maxRetries) throw err;
          lastError = err;
        } else if (err instanceof Error && err.name === 'AbortError') {
          // Timeout — retryable
          lastError = err;
          if (attempt === this.maxRetries) {
            throw new AIPError(504, { code: 'PROVIDER_TIMEOUT', message: 'Request timed out' });
          }
        } else {
          throw err;
        }
      }
    }

    throw lastError ?? new AIPError(500, { code: 'INTERNAL_ERROR', message: 'Unexpected retry exhaustion' });
  }

  private async rawFetch(path: string, init: RequestInit): Promise<Response> {
    const url = `${this.endpoint}${path}`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      return await fetch(url, {
        ...init,
        signal: controller.signal,
        headers: {
          ...this.headers,
          ...(init.headers as Record<string, string>),
          'Authorization': `Bearer ${this.apiKey}`,
          'User-Agent': 'aip-sdk-ts/2.1.0',
        },
      });
    } finally {
      clearTimeout(timer);
    }
  }

  private async buildError(response: Response): Promise<AIPError> {
    const requestId = response.headers.get('x-request-id') ?? undefined;
    try {
      const json = await response.json();
      const errorBody = json.error ?? { code: 'UNKNOWN', message: response.statusText };
      return new AIPError(response.status, errorBody, requestId);
    } catch {
      return new AIPError(response.status, { code: 'UNKNOWN', message: response.statusText }, requestId);
    }
  }

  private async handleError(response: Response): Promise<never> {
    throw await this.buildError(response);
  }

  // ─── SSE Parser ──────────────────────────────────────────────────────────

  private async *parseSSE(body: ReadableStream<Uint8Array>): AsyncGenerator<StreamDelta, void, unknown> {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') return;
            try {
              yield JSON.parse(data) as StreamDelta;
            } catch {
              // Skip malformed JSON lines
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  // ─── Helpers ─────────────────────────────────────────────────────────────

  private retryDelay(attempt: number, error: AIPError | Error): number {
    // Respect Retry-After if available (stored in AIPError)
    const base = Math.min(1000 * 2 ** (attempt - 1), 10_000);
    const jitter = Math.random() * 500;
    return base + jitter;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private envVar(key: string): string | undefined {
    if (typeof process !== 'undefined' && process.env) {
      return process.env[key];
    }
    return undefined;
  }
}

export default AIPClient;
