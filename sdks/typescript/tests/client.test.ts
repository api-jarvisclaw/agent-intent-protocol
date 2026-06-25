import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AIPClient, AIPError } from '../src/index';

describe('AIPClient', () => {
  let client: AIPClient;

  beforeEach(() => {
    client = new AIPClient({ apiKey: 'test-key', endpoint: 'https://test.api.local' });
  });

  describe('constructor', () => {
    it('should create client with api key', () => {
      const c = new AIPClient({ apiKey: 'sk-123' });
      expect(c).toBeInstanceOf(AIPClient);
    });

    it('should use default endpoint', () => {
      const c = new AIPClient({ apiKey: 'sk-123' });
      // Internal endpoint defaults to api.jarvisclaw.ai
      expect(c).toBeDefined();
    });

    it('should accept custom endpoint', () => {
      const c = new AIPClient({ apiKey: 'sk-123', endpoint: 'https://custom.api' });
      expect(c).toBeDefined();
    });
  });

  describe('execute', () => {
    it('should call fetch with correct parameters', async () => {
      const mockResponse = {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ success: true, result: { text: 'hello' } }),
      };
      global.fetch = vi.fn().mockResolvedValue(mockResponse);

      const result = await client.execute('chat_completion', {
        messages: [{ role: 'user', content: 'hi' }],
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'https://test.api.local/v1/aip/execute',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-key',
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result).toEqual({ success: true, result: { text: 'hello' } });
    });

    it('should throw AIPError on non-ok response', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ error: { code: 'AUTH_INVALID', message: 'Bad key' } }),
      };
      global.fetch = vi.fn().mockResolvedValue(mockResponse);

      await expect(client.execute('chat_completion', { messages: [] }))
        .rejects.toThrow(AIPError);
    });

    it('should retry on 429', async () => {
      const failResponse = {
        ok: false,
        status: 429,
        headers: new Headers({ 'content-type': 'application/json', 'retry-after': '0' }),
        json: () => Promise.resolve({ error: { code: 'RATE_LIMITED', message: 'slow down' } }),
      };
      const okResponse = {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ success: true, result: {} }),
      };
      global.fetch = vi.fn()
        .mockResolvedValueOnce(failResponse)
        .mockResolvedValueOnce(okResponse);

      const retryClient = new AIPClient({
        apiKey: 'test-key',
        endpoint: 'https://test.api.local',
        maxRetries: 2,
      });
      const result = await retryClient.execute('chat_completion', { messages: [] });
      expect(result.success).toBe(true);
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('resolve', () => {
    it('should call resolve endpoint', async () => {
      const mockResponse = {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ success: true, resolution: { model: 'gpt-4o' } }),
      };
      global.fetch = vi.fn().mockResolvedValue(mockResponse);

      const result = await client.resolve('chat_completion');
      expect(global.fetch).toHaveBeenCalledWith(
        'https://test.api.local/v1/aip/resolve',
        expect.anything()
      );
      expect(result.resolution.model).toBe('gpt-4o');
    });
  });

  describe('discover', () => {
    it('should call discover endpoint', async () => {
      const mockResponse = {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ intents: ['chat_completion', 'image_generation'] }),
      };
      global.fetch = vi.fn().mockResolvedValue(mockResponse);

      const result = await client.discover();
      expect(global.fetch).toHaveBeenCalledWith(
        'https://test.api.local/v1/aip/discover',
        expect.anything()
      );
      expect(result.intents).toContain('chat_completion');
    });
  });

  describe('health', () => {
    it('should call health endpoint with GET', async () => {
      const mockResponse = {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ status: 'healthy' }),
      };
      global.fetch = vi.fn().mockResolvedValue(mockResponse);

      const result = await client.health();
      expect(global.fetch).toHaveBeenCalledWith(
        'https://test.api.local/v1/aip/health',
        expect.objectContaining({ method: 'GET' })
      );
      expect(result.status).toBe('healthy');
    });
  });

  describe('convenience methods', () => {
    beforeEach(() => {
      const mockResponse = {
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ success: true, result: {} }),
      };
      global.fetch = vi.fn().mockResolvedValue(mockResponse);
    });

    it('chat() should execute chat_completion intent', async () => {
      await client.chat([{ role: 'user', content: 'hello' }]);
      const body = JSON.parse((global.fetch as any).mock.calls[0][1].body);
      expect(body.intent).toBe('chat_completion');
      expect(body.payload.messages[0].content).toBe('hello');
    });

    it('embed() should execute embedding intent', async () => {
      await client.embed('test text');
      const body = JSON.parse((global.fetch as any).mock.calls[0][1].body);
      expect(body.intent).toBe('embedding');
      expect(body.payload.input).toBe('test text');
    });

    it('generateImage() should execute image_generation intent', async () => {
      await client.generateImage('a cat');
      const body = JSON.parse((global.fetch as any).mock.calls[0][1].body);
      expect(body.intent).toBe('image_generation');
      expect(body.payload.prompt).toBe('a cat');
    });
  });
});

describe('AIPError', () => {
  it('should have proper name and properties', () => {
    const err = new AIPError('test error', 400, { code: 'BAD_REQUEST' });
    expect(err.name).toBe('AIPError');
    expect(err.message).toBe('test error');
    expect(err.statusCode).toBe(400);
    expect(err.body).toEqual({ code: 'BAD_REQUEST' });
  });
});
