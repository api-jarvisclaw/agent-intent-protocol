# AIP (Agent Intent Protocol) — 使用场景完整指南

> 本文档列出 AIP 协议支持的**全部使用场景**，并提供 Python、Go、TypeScript、curl 四种语言的完整示例。

---

## 目录

1. [安装与初始化](#1-安装与初始化)
2. [Resolve — 智能路由选择最优 Provider](#2-resolve--智能路由选择最优-provider)
3. [Execute — 一步执行 Intent](#3-execute--一步执行-intent)
4. [Subscribe / Streaming — 流式响应](#4-subscribe--streaming--流式响应)
5. [Discover — 发现可用 Intent 和 Provider](#5-discover--发现可用-intent-和-provider)
6. [Multi-Intent Chaining — 多 Intent 工作流编排](#6-multi-intent-chaining--多-intent-工作流编排)
7. [Execute with Budget — 预算控制执行](#7-execute-with-budget--预算控制执行)
8. [Audit — 审计日志](#8-audit--审计日志)
9. [支持的 Intent 类型总览](#9-支持的-intent-类型总览)
10. [SDK 与独立协议包的关系](#10-sdk-与独立协议包的关系)

---

## 1. 安装与初始化

### Python

```bash
pip install jarvisclaw          # 主 SDK，已内置 AIP
# 或独立轻量包:
pip install agent-intent-protocol
```

```python
import os
from agent_intent_protocol import AIPClient

client = AIPClient(api_key=os.environ.get("AIP_API_KEY"))
```

### Go

```bash
go get github.com/api-jarvisclaw/agent-intent-protocol/sdks/go
```

```go
import aip "github.com/api-jarvisclaw/agent-intent-protocol/sdks/go"

client := aip.NewClient(os.Getenv("AIP_API_KEY"))
ctx := context.Background()
```

### TypeScript

```bash
npm install @jarvisclaw/agent-intent-protocol
```

```typescript
import { AIPClient } from '@jarvisclaw/agent-intent-protocol';

const client = new AIPClient({ apiKey: process.env.AIP_API_KEY });
```

### curl

```bash
export AIP_API_KEY="sk-your-key"
export AIP_ENDPOINT="${AIP_ENDPOINT:-https://api.jarvisclaw.ai}"
```

---

## 2. Resolve — 智能路由选择最优 Provider

**场景**: 不执行操作，只查询满足约束条件的最优 Provider（按成本/质量/速度优化）。

### Python

```python
result = client.resolve(
    intent="chat_completion",
    max_price_usd=0.01,
    optimize_for="cost",  # "cost" | "quality" | "speed"
)
if result.success:
    m = result.best_match
    print(f"Provider: {m.provider_name}, Model: {m.model}, Price: ${m.price_usd}, Latency: {m.latency_ms}ms")
```

### Go

```go
res, err := client.Resolve(ctx, &aip.IntentRequest{
    Intent:      "chat_completion",
    Preferences: &aip.Preferences{OptimizeFor: "cost", MaxPriceUSD: floatPtr(0.01)},
})
if err == nil {
    fmt.Printf("Provider: %s, Model: %s, Price: $%.6f\n",
        res.BestMatch.ProviderName, res.BestMatch.Model, res.BestMatch.PriceUSD)
}
```

### TypeScript

```typescript
const resolved = await client.resolve({
    intent: 'chat_completion',
    constraints: { maxPriceUsd: 0.01 },
    preferences: { optimizeFor: 'cost' },
});
if (resolved.success && resolved.bestMatch) {
    console.log(`Provider: ${resolved.bestMatch.providerName}, Model: ${resolved.bestMatch.model}`);
}
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/resolve" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "chat_completion",
    "constraints": { "max_price_usd": 0.01 },
    "preferences": { "optimize_for": "cost" }
  }'
```

---

## 3. Execute — 一步执行 Intent

**场景**: 自动 Resolve + 执行，返回结果和费用。适用于不需要手动选择 Provider 的场景。

### Python

```python
response = client.execute(
    intent="chat_completion",
    payload={
        "messages": [{"role": "user", "content": "Explain AIP in one sentence."}],
        "max_tokens": 100,
    },
    optimize_for="quality",
)
if response.success:
    print(f"Provider: {response.provider}")
    print(f"Response: {response.result['choices'][0]['message']['content']}")
    print(f"Cost: ${response.cost_usd}")
```

### Go

```go
exec, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "chat_completion",
    Payload: map[string]any{
        "messages":   []map[string]string{{"role": "user", "content": "Explain AIP in one sentence."}},
        "max_tokens": 100,
    },
    Preferences: &aip.Preferences{OptimizeFor: "quality"},
})
if err == nil {
    fmt.Printf("Provider: %s, Cost: $%.6f\n", exec.Provider, exec.CostUSD)
}
```

### TypeScript

```typescript
const exec = await client.execute({
    intent: 'chat_completion',
    payload: {
        messages: [{ role: 'user', content: 'Explain AIP in one sentence.' }],
        max_tokens: 100,
    },
    preferences: { optimizeFor: 'quality' },
});
if (exec.success) {
    console.log(`Provider: ${exec.provider}, Cost: $${exec.costUsd}`);
    console.log(`Response: ${exec.result.choices[0].message.content}`);
}
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "chat_completion",
    "payload": {
      "messages": [{"role": "user", "content": "Explain AIP in one sentence."}],
      "max_tokens": 100
    },
    "preferences": { "optimize_for": "quality" }
  }'
```

---

## 4. Subscribe / Streaming — 流式响应

**场景**: 通过 SSE（Server-Sent Events）流式接收生成内容，适用于实时输出的聊天、长文生成等。

### Python

```python
stream = client.subscribe(
    intent="chat_completion",
    payload={
        "messages": [{"role": "user", "content": "Write a haiku about distributed systems."}],
        "stream": True,
    },
    optimize_for="speed",
)

for chunk in stream:
    if chunk.delta:
        print(chunk.delta, end="", flush=True)

print(f"\nTotal tokens: {stream.usage.total_tokens}")
print(f"Cost: ${stream.cost_usd}")
```

### Go

```go
stream, err := client.Subscribe(ctx, &aip.SubscribeRequest{
    Intent: "chat_completion",
    Payload: map[string]any{
        "messages": []map[string]string{
            {"role": "user", "content": "Write a haiku about distributed systems."},
        },
        "stream": true,
    },
    Preferences: &aip.Preferences{OptimizeFor: "speed"},
})
if err != nil {
    log.Fatal(err)
}
defer stream.Close()

for stream.Next() {
    chunk := stream.Current()
    if chunk.Delta != "" {
        fmt.Print(chunk.Delta)
    }
}
fmt.Printf("\nTotal tokens: %d\n", stream.Usage().TotalTokens)
fmt.Printf("Cost: $%.6f\n", stream.CostUSD())
```

### TypeScript

```typescript
const stream = await client.subscribe({
    intent: 'chat_completion',
    payload: {
        messages: [{ role: 'user', content: 'Write a haiku about distributed systems.' }],
        stream: true,
    },
    preferences: { optimizeFor: 'speed' },
});

for await (const chunk of stream) {
    if (chunk.delta) {
        process.stdout.write(chunk.delta);
    }
}
console.log(`\nTotal tokens: ${stream.usage.totalTokens}`);
console.log(`Cost: $${stream.costUsd}`);
```

---

## 5. Discover — 发现可用 Intent 和 Provider

**场景**: 查询平台当前支持的所有 Intent 类型以及每种 Intent 可用的 Provider 列表。

### Python

```python
# 列出所有可用 intent 类型
for intent in client.list_intents():
    providers = client.list_providers(intent)
    print(f"{intent}: {len(providers)} providers")
```

### Go

```go
intents, err := client.ListIntents(ctx)
if err == nil {
    for _, intent := range intents {
        fmt.Printf("  %s\n", intent)
    }
}
```

### TypeScript

```typescript
const intents = await client.listIntents();
for (const intent of intents) {
    const providers = await client.listProviders(intent);
    console.log(`${intent}: ${providers.length} providers`);
}
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/discover" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json"
```

---

## 6. Multi-Intent Chaining — 多 Intent 工作流编排

**场景**: 在单个工作流中串联多种 Intent（如搜索→摘要→图片生成→语音），AIP 作为统一路由器，一个 client 完成所有能力调用。

### Python

```python
# Step 1: Web Search
search = client.execute(intent="web_search", payload={"query": "Agent Intent Protocol"})
print(f"Found {len(search.result.get('results', []))} results")

# Step 2: Summarize with Chat
snippets = "\n".join(r.get("snippet", "") for r in search.result.get("results", [])[:3])
summary = client.execute(
    intent="chat_completion",
    payload={
        "messages": [
            {"role": "system", "content": "Summarize the following search results concisely."},
            {"role": "user", "content": snippets},
        ],
        "max_tokens": 200,
    },
    optimize_for="quality",
)
print(f"Summary: {summary.result['choices'][0]['message']['content']}")

# Step 3: Image Generation
image = client.execute(
    intent="image_generation",
    payload={"prompt": "A conceptual diagram of AIP", "size": "1024x1024"},
)
print(f"Image URL: {image.result.get('url')}")

# Step 4: Text to Speech
tts = client.execute(
    intent="text_to_speech",
    payload={"text": summary.result["choices"][0]["message"]["content"], "voice": "alloy"},
)
print(f"Audio format: {tts.result.get('format')}, size: {tts.result.get('size_bytes')} bytes")

# 汇总成本
total = sum(r.cost_usd for r in [search, summary, image, tts] if r.cost_usd)
print(f"Total cost: ${total:.6f}")
```

### Go

```go
// Step 1: Web Search
search, _ := client.Execute(ctx, &aip.ExecuteRequest{
    Intent:  "web_search",
    Payload: map[string]any{"query": "Agent Intent Protocol"},
})

// Step 2: Chat Completion (summarize)
summary, _ := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "chat_completion",
    Payload: map[string]any{
        "messages": []map[string]string{
            {"role": "user", "content": "Summarize these results..."},
        },
    },
    Preferences: &aip.Preferences{OptimizeFor: "quality"},
})

// Step 3: Image Generation
image, _ := client.Execute(ctx, &aip.ExecuteRequest{
    Intent:  "image_generation",
    Payload: map[string]any{"prompt": "AIP diagram", "size": "1024x1024"},
})

// Step 4: Text to Speech
tts, _ := client.Execute(ctx, &aip.ExecuteRequest{
    Intent:  "text_to_speech",
    Payload: map[string]any{"text": "Summary text here", "voice": "alloy"},
})
```

### TypeScript

```typescript
// Step 1: Web Search
const search = await client.execute({ intent: 'web_search', payload: { query: 'AIP' } });

// Step 2: Summarize
const summary = await client.execute({
    intent: 'chat_completion',
    payload: { messages: [{ role: 'user', content: 'Summarize...' }] },
    preferences: { optimizeFor: 'quality' },
});

// Step 3: Image
const image = await client.execute({
    intent: 'image_generation',
    payload: { prompt: 'AIP diagram', size: '1024x1024' },
});

// Step 4: TTS
const tts = await client.execute({
    intent: 'text_to_speech',
    payload: { text: 'Summary content', voice: 'alloy' },
});
```

---

## 7. Execute with Budget — 预算控制执行

**场景**: 设定预算上限，执行过程中自动跟踪花费，超出预算时自动停止。适用于批量任务或自主 Agent 的成本控制。

### Python (主 SDK: jarvisclaw)

```python
from jarvisclaw import IntentClient

client = IntentClient(api_key="sk-...")

# 设定最大预算 $0.50
response = client.execute_budget(
    intent="chat_completion",
    payload={"messages": [{"role": "user", "content": "Write a long essay."}]},
    budget_usd=0.50,
)
print(f"Spent: ${response.cost_usd}, Budget remaining: ${0.50 - response.cost_usd}")
```

> **注意**: `execute_budget()` 目前仅在 Python 主 SDK (`jarvisclaw`) 的 IntentClient 中提供。

---

## 8. Audit — 审计日志

**场景**: 查询历史调用的审计记录，用于合规、费用追踪和调试。

### Python (主 SDK: jarvisclaw)

```python
from jarvisclaw import IntentClient

client = IntentClient(api_key="sk-...")

# 获取最近的审计日志
audit_logs = client.audit(limit=10)
for log in audit_logs:
    print(f"[{log.timestamp}] {log.intent} → {log.provider} | ${log.cost_usd}")
```

> **注意**: `audit()` 目前仅在 Python 主 SDK (`jarvisclaw`) 的 IntentClient 中提供。

---

## 9. Video Generation — 视频生成

**场景**: 根据文本 prompt 生成短视频。

### Python

```python
response = client.execute(
    intent="video_generation",
    payload={
        "prompt": "A serene lake at sunrise with birds flying overhead",
        "duration_seconds": 5,
        "resolution": "1080p",
    },
    optimize_for="quality",
)
if response.success:
    print(f"Video URL: {response.result['video_url']}")
    print(f"Duration: {response.result['duration_seconds']}s")
    print(f"Cost: ${response.cost_usd}")
```

### Go

```go
video, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "video_generation",
    Payload: map[string]any{
        "prompt":           "A serene lake at sunrise with birds flying overhead",
        "duration_seconds": 5,
        "resolution":       "1080p",
    },
    Preferences: &aip.Preferences{OptimizeFor: "quality"},
})
if err == nil {
    fmt.Printf("Video URL: %s\n", video.Result["video_url"])
}
```

### TypeScript

```typescript
const video = await client.execute({
    intent: 'video_generation',
    payload: {
        prompt: 'A serene lake at sunrise with birds flying overhead',
        durationSeconds: 5,
        resolution: '1080p',
    },
    preferences: { optimizeFor: 'quality' },
});
console.log(`Video URL: ${video.result.videoUrl}`);
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "video_generation",
    "payload": {
      "prompt": "A serene lake at sunrise with birds flying overhead",
      "duration_seconds": 5,
      "resolution": "1080p"
    },
    "preferences": { "optimize_for": "quality" }
  }'
```

---

## 10. Moderation — 内容审核

**场景**: 对用户输入进行内容安全审核，检测违规类别。

### Python

```python
response = client.execute(
    intent="moderation",
    payload={
        "input": "Some user-generated text content to check",
        "categories": ["hate", "violence", "sexual", "self-harm"],
    },
)
if response.success:
    results = response.result
    print(f"Flagged: {results['flagged']}")
    for cat, score in results['category_scores'].items():
        if score > 0.5:
            print(f"  ⚠️ {cat}: {score:.3f}")
```

### Go

```go
mod, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "moderation",
    Payload: map[string]any{
        "input":      "Some user-generated text content to check",
        "categories": []string{"hate", "violence", "sexual", "self-harm"},
    },
})
if err == nil {
    fmt.Printf("Flagged: %v\n", mod.Result["flagged"])
}
```

### TypeScript

```typescript
const mod = await client.execute({
    intent: 'moderation',
    payload: {
        input: 'Some user-generated text content to check',
        categories: ['hate', 'violence', 'sexual', 'self-harm'],
    },
});
console.log(`Flagged: ${mod.result.flagged}`);
for (const [cat, score] of Object.entries(mod.result.categoryScores)) {
    if ((score as number) > 0.5) console.log(`  ⚠️ ${cat}: ${score}`);
}
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "moderation",
    "payload": {
      "input": "Some user-generated text content to check",
      "categories": ["hate", "violence", "sexual", "self-harm"]
    }
  }'
```

---

## 11. Translation — 文本翻译

**场景**: 将文本从一种语言翻译为另一种语言。

### Python

```python
response = client.execute(
    intent="translation",
    payload={
        "text": "The agent intent protocol enables seamless AI service routing.",
        "source_lang": "en",
        "target_lang": "zh",
    },
    optimize_for="quality",
)
if response.success:
    print(f"Translation: {response.result['translated_text']}")
    print(f"Provider: {response.provider}, Cost: ${response.cost_usd}")
```

### Go

```go
tr, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "translation",
    Payload: map[string]any{
        "text":        "The agent intent protocol enables seamless AI service routing.",
        "source_lang": "en",
        "target_lang": "zh",
    },
    Preferences: &aip.Preferences{OptimizeFor: "quality"},
})
if err == nil {
    fmt.Printf("Translation: %s\n", tr.Result["translated_text"])
}
```

### TypeScript

```typescript
const tr = await client.execute({
    intent: 'translation',
    payload: {
        text: 'The agent intent protocol enables seamless AI service routing.',
        sourceLang: 'en',
        targetLang: 'zh',
    },
    preferences: { optimizeFor: 'quality' },
});
console.log(`Translation: ${tr.result.translatedText}`);
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "translation",
    "payload": {
      "text": "The agent intent protocol enables seamless AI service routing.",
      "source_lang": "en",
      "target_lang": "zh"
    },
    "preferences": { "optimize_for": "quality" }
  }'
```

---

## 12. Image Generation — 图片生成

**场景**: 根据文本 prompt 生成图片，支持指定尺寸、风格等参数。

### Python

```python
response = client.execute(
    intent="image_generation",
    payload={
        "prompt": "A futuristic city skyline at sunset, cyberpunk style",
        "size": "1024x1024",
        "style": "vivid",
        "n": 1,
    },
    optimize_for="quality",
)
if response.success:
    print(f"Image URL: {response.result['url']}")
    print(f"Revised prompt: {response.result.get('revised_prompt', 'N/A')}")
    print(f"Provider: {response.provider}, Cost: ${response.cost_usd}")
```

### Go

```go
img, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "image_generation",
    Payload: map[string]any{
        "prompt": "A futuristic city skyline at sunset, cyberpunk style",
        "size":   "1024x1024",
        "style":  "vivid",
        "n":      1,
    },
    Preferences: &aip.Preferences{OptimizeFor: "quality"},
})
if err == nil {
    fmt.Printf("Image URL: %s\n", img.Result["url"])
    fmt.Printf("Cost: $%f\n", img.CostUSD)
}
```

### TypeScript

```typescript
const img = await client.execute({
    intent: 'image_generation',
    payload: {
        prompt: 'A futuristic city skyline at sunset, cyberpunk style',
        size: '1024x1024',
        style: 'vivid',
        n: 1,
    },
    preferences: { optimizeFor: 'quality' },
});
console.log(`Image URL: ${img.result.url}`);
console.log(`Cost: $${img.costUsd}`);
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "image_generation",
    "payload": {
      "prompt": "A futuristic city skyline at sunset, cyberpunk style",
      "size": "1024x1024",
      "style": "vivid",
      "n": 1
    },
    "preferences": { "optimize_for": "quality" }
  }'
```


### 预期输出

```json
{
  "success": true,
  "intent": "image_generation",
  "result": {
    "url": "https://cdn.aip-provider.com/img/abc123.png",
    "revised_prompt": "A futuristic cyberpunk city skyline bathed in golden sunset light, with neon signs and flying vehicles",
    "width": 1024,
    "height": 1024
  },
  "provider": "openai/dall-e-3",
  "cost_usd": 0.040,
  "latency_ms": 8200
}
```

### 好处

- **统一接口，自动路由**：无需分别对接 DALL·E、Midjourney、Stable Diffusion 等不同 API，AIP 根据 preferences 自动选最优 provider
- **成本透明**：每次请求返回实际 `cost_usd`，可直接用于计费和预算控制
- **prompt 优化**：provider 返回 `revised_prompt`，让你知道模型实际理解的内容，方便迭代
- **自动重试与降级**：某 provider 超时或报错时，AIP 网关自动切换到备选 provider，调用方无感知
- **参数标准化**：`size`、`style`、`n` 等参数跨 provider 统一，不用记各家私有字段名

---

## 13. Text to Speech — 文字转语音

**场景**: 将文本转化为自然语音音频，支持多种音色和语速设置。

### Python

```python
response = client.execute(
    intent="text_to_speech",
    payload={
        "text": "Welcome to the Agent Intent Protocol. Let's build the future together.",
        "voice": "alloy",
        "speed": 1.0,
        "format": "mp3",
    },
)
if response.success:
    print(f"Audio format: {response.result['format']}")
    print(f"Size: {response.result['size_bytes']} bytes")
    print(f"Duration: {response.result.get('duration_seconds', 'N/A')}s")
    # Save audio
    import base64
    audio_data = base64.b64decode(response.result["audio_base64"])
    with open("output.mp3", "wb") as f:
        f.write(audio_data)
```

### Go

```go
tts, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "text_to_speech",
    Payload: map[string]any{
        "text":   "Welcome to the Agent Intent Protocol.",
        "voice":  "alloy",
        "speed":  1.0,
        "format": "mp3",
    },
})
if err == nil {
    fmt.Printf("Format: %s, Size: %v bytes\n",
        tts.Result["format"], tts.Result["size_bytes"])
}
```

### TypeScript

```typescript
const tts = await client.execute({
    intent: 'text_to_speech',
    payload: {
        text: 'Welcome to the Agent Intent Protocol.',
        voice: 'alloy',
        speed: 1.0,
        format: 'mp3',
    },
});
console.log(`Format: ${tts.result.format}, Size: ${tts.result.sizeBytes} bytes`);
// Decode and save
const buffer = Buffer.from(tts.result.audioBase64, 'base64');
await fs.writeFile('output.mp3', buffer);
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "text_to_speech",
    "payload": {
      "text": "Welcome to the Agent Intent Protocol.",
      "voice": "alloy",
      "speed": 1.0,
      "format": "mp3"
    }
  }'
```


### 预期输出

```json
{
  "success": true,
  "intent": "text_to_speech",
  "result": {
    "audioBase64": "SUQzBAAAAAAAI1RTU0UAAAA...(base64 编码的 MP3 数据)...",
    "format": "mp3",
    "sizeBytes": 48256,
    "durationMs": 3200
  },
  "provider": "openai/tts-1",
  "cost_usd": 0.0045,
  "latency_ms": 1800
}
```

### 好处

- **多音色一键切换**：`voice` 参数统一枚举（alloy/echo/nova/shimmer 等），跨 provider 映射，不用学各家 SDK
- **格式灵活**：支持 mp3/opus/aac/flac，一个参数搞定，无需额外转码
- **base64 内联返回**：小音频直接拿 base64 解码使用，无需额外下载步骤；大音频也可请求返回 URL
- **实时计费**：`cost_usd` 按实际字符数计费，精确到请求级别
- **低延迟自动选路**：设置 `optimize_for: "latency"` 时自动选响应最快的 TTS provider

---

## 14. Speech to Text — 语音转文字

**场景**: 将音频文件或 URL 转录为文本，支持多语言识别和时间戳输出。

### Python

```python
response = client.execute(
    intent="speech_to_text",
    payload={
        "audio_url": "https://example.com/meeting-recording.mp3",
        "language": "en",
        "timestamps": True,
    },
    optimize_for="quality",
)
if response.success:
    print(f"Transcript: {response.result['text']}")
    print(f"Language: {response.result['language']}")
    print(f"Duration: {response.result['duration_seconds']}s")
    if response.result.get("segments"):
        for seg in response.result["segments"][:3]:
            print(f"  [{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['text']}")
```

### Go

```go
stt, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "speech_to_text",
    Payload: map[string]any{
        "audio_url":  "https://example.com/meeting-recording.mp3",
        "language":   "en",
        "timestamps": true,
    },
    Preferences: &aip.Preferences{OptimizeFor: "quality"},
})
if err == nil {
    fmt.Printf("Transcript: %s\n", stt.Result["text"])
    fmt.Printf("Duration: %vs\n", stt.Result["duration_seconds"])
}
```

### TypeScript

```typescript
const stt = await client.execute({
    intent: 'speech_to_text',
    payload: {
        audioUrl: 'https://example.com/meeting-recording.mp3',
        language: 'en',
        timestamps: true,
    },
    preferences: { optimizeFor: 'quality' },
});
console.log(`Transcript: ${stt.result.text}`);
console.log(`Duration: ${stt.result.durationSeconds}s`);
for (const seg of stt.result.segments?.slice(0, 3) ?? []) {
    console.log(`  [${seg.start}s-${seg.end}s] ${seg.text}`);
}
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "speech_to_text",
    "payload": {
      "audio_url": "https://example.com/meeting-recording.mp3",
      "language": "en",
      "timestamps": true
    },
    "preferences": { "optimize_for": "quality" }
  }'
```


### 预期输出

```json
{
  "success": true,
  "intent": "speech_to_text",
  "result": {
    "text": "Welcome to the Agent Intent Protocol. Let's build the future together.",
    "language": "en",
    "confidence": 0.97,
    "segments": [
      {"start": 0.0, "end": 1.8, "text": "Welcome to the Agent Intent Protocol."},
      {"start": 2.0, "end": 3.2, "text": "Let's build the future together."}
    ],
    "durationMs": 3200
  },
  "provider": "openai/whisper-1",
  "cost_usd": 0.0019,
  "latency_ms": 2400
}
```

### 好处

- **多格式支持**：直接接收 mp3/wav/webm/m4a 等格式，无需预处理
- **自动语言检测**：不传 `language` 时自动识别语种，返回检测结果
- **时间戳对齐**：`segments` 数组提供逐句时间戳，可直接用于字幕生成
- **置信度评分**：`confidence` 字段让你判断识别质量，低于阈值可要求用户重录
- **大文件友好**：支持 base64 和 URL 两种输入方式，大文件直接传 URL 避免请求体过大

---

## 15. Embedding — 文本向量化

**场景**: 将文本转换为高维向量，用于语义搜索、聚类和推荐系统。

### Python

```python
response = client.execute(
    intent="embedding",
    payload={
        "input": [
            "Agent Intent Protocol enables seamless AI routing.",
            "The quick brown fox jumps over the lazy dog.",
        ],
        "model": "text-embedding-3-small",
        "dimensions": 1536,
    },
    optimize_for="cost",
)
if response.success:
    embeddings = response.result["embeddings"]
    print(f"Generated {len(embeddings)} embeddings")
    print(f"Dimensions: {len(embeddings[0])}")
    print(f"Provider: {response.provider}, Cost: ${response.cost_usd}")
```

### Go

```go
emb, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "embedding",
    Payload: map[string]any{
        "input": []string{
            "Agent Intent Protocol enables seamless AI routing.",
            "The quick brown fox jumps over the lazy dog.",
        },
        "model":      "text-embedding-3-small",
        "dimensions": 1536,
    },
    Preferences: &aip.Preferences{OptimizeFor: "cost"},
})
if err == nil {
    embeddings := emb.Result["embeddings"].([]any)
    fmt.Printf("Generated %d embeddings\n", len(embeddings))
}
```

### TypeScript

```typescript
const emb = await client.execute({
    intent: 'embedding',
    payload: {
        input: [
            'Agent Intent Protocol enables seamless AI routing.',
            'The quick brown fox jumps over the lazy dog.',
        ],
        model: 'text-embedding-3-small',
        dimensions: 1536,
    },
    preferences: { optimizeFor: 'cost' },
});
console.log(`Generated ${emb.result.embeddings.length} embeddings`);
console.log(`Dimensions: ${emb.result.embeddings[0].length}`);
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "embedding",
    "payload": {
      "input": ["Agent Intent Protocol enables seamless AI routing.", "The quick brown fox jumps over the lazy dog."],
      "model": "text-embedding-3-small",
      "dimensions": 1536
    },
    "preferences": { "optimize_for": "cost" }
  }'
```


### 预期输出

```json
{
  "success": true,
  "intent": "embedding",
  "result": {
    "embeddings": [
      [0.0023, -0.0134, 0.0271, "...(共 1536 维)"],
      [-0.0089, 0.0412, -0.0055, "...(共 1536 维)"]
    ],
    "model": "text-embedding-3-small",
    "dimensions": 1536,
    "tokensUsed": 18
  },
  "provider": "openai/embedding",
  "cost_usd": 0.000004,
  "latency_ms": 320
}
```

### 好处

- **批量处理**：一次请求传多条文本，减少网络往返，吞吐量提升 5-10 倍
- **维度可选**：通过 `dimensions` 参数控制向量维度，低维节省存储、高维保精度
- **成本极低**：embedding 是所有 intent 中成本最低的，适合大规模索引构建
- **provider 透明切换**：今天用 OpenAI，明天换 Cohere 或本地模型，代码零改动
- **token 用量反馈**：返回 `tokensUsed`，精确追踪配额消耗

---

## 16. Web Search — 网页搜索

**场景**: 执行网页搜索并返回结构化结果，支持结果数量和区域设置。

### Python

```python
response = client.execute(
    intent="web_search",
    payload={
        "query": "Agent Intent Protocol open source",
        "num_results": 5,
        "language": "en",
        "region": "us",
    },
    optimize_for="speed",
)
if response.success:
    results = response.result["results"]
    print(f"Found {len(results)} results:")
    for r in results:
        print(f"  - {r['title']}")
        print(f"    {r['url']}")
        print(f"    {r['snippet'][:80]}...")
```

### Go

```go
search, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "web_search",
    Payload: map[string]any{
        "query":       "Agent Intent Protocol open source",
        "num_results": 5,
        "language":    "en",
    },
    Preferences: &aip.Preferences{OptimizeFor: "speed"},
})
if err == nil {
    results := search.Result["results"].([]any)
    fmt.Printf("Found %d results\n", len(results))
    for _, r := range results {
        item := r.(map[string]any)
        fmt.Printf("  - %s\n    %s\n", item["title"], item["url"])
    }
}
```

### TypeScript

```typescript
const search = await client.execute({
    intent: 'web_search',
    payload: {
        query: 'Agent Intent Protocol open source',
        numResults: 5,
        language: 'en',
        region: 'us',
    },
    preferences: { optimizeFor: 'speed' },
});
for (const r of search.result.results) {
    console.log(`- ${r.title}\n  ${r.url}\n  ${r.snippet.slice(0, 80)}...`);
}
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "web_search",
    "payload": {
      "query": "Agent Intent Protocol open source",
      "num_results": 5,
      "language": "en",
      "region": "us"
    },
    "preferences": { "optimize_for": "speed" }
  }'
```


### 预期输出

```json
{
  "success": true,
  "intent": "web_search",
  "result": {
    "results": [
      {
        "title": "Agent Intent Protocol - GitHub",
        "url": "https://github.com/anthropic/agent-intent-protocol",
        "snippet": "AIP is a unified protocol for AI agent capabilities including LLM, image generation, TTS, STT, and more.",
        "score": 0.95
      },
      {
        "title": "AIP Documentation",
        "url": "https://docs.aip.dev/getting-started",
        "snippet": "Get started with AIP in 5 minutes. Install the SDK, configure your API key, and make your first intent call.",
        "score": 0.89
      }
    ],
    "totalResults": 2,
    "searchEngine": "google"
  },
  "provider": "serper/google",
  "cost_usd": 0.005,
  "latency_ms": 1100
}
```

### 好处

- **Agent 实时信息获取**：让 AI Agent 能访问最新网页内容，不再局限于训练数据截止日期
- **结构化结果**：返回 title/url/snippet/score 标准化结构，直接可用于 RAG pipeline
- **搜索引擎抽象**：底层可能是 Google/Bing/Brave，调用方无需关心具体引擎
- **相关性评分**：`score` 字段帮助你过滤低质量结果，提升下游 LLM 的上下文质量
- **限定条数**：`max_results` 控制返回数量，避免浪费 token 在无关结果上

---

## 17. Code Generation — 代码生成

**场景**: 根据自然语言描述生成代码，支持指定编程语言和上下文。

### Python

```python
response = client.execute(
    intent="code_generation",
    payload={
        "prompt": "Write a Python function that calculates the Fibonacci sequence using memoization",
        "language": "python",
        "max_tokens": 500,
        "context": "This will be used in a performance-critical application",
    },
    optimize_for="quality",
)
if response.success:
    print(f"Generated code:\n{response.result['code']}")
    print(f"Language: {response.result['language']}")
    print(f"Tokens used: {response.result.get('usage', {}).get('total_tokens', 'N/A')}")
    print(f"Provider: {response.provider}, Cost: ${response.cost_usd}")
```

### Go

```go
code, err := client.Execute(ctx, &aip.ExecuteRequest{
    Intent: "code_generation",
    Payload: map[string]any{
        "prompt":     "Write a Go function that calculates Fibonacci using memoization",
        "language":   "go",
        "max_tokens": 500,
    },
    Preferences: &aip.Preferences{OptimizeFor: "quality"},
})
if err == nil {
    fmt.Printf("Generated code:\n%s\n", code.Result["code"])
    fmt.Printf("Language: %s\n", code.Result["language"])
}
```

### TypeScript

```typescript
const code = await client.execute({
    intent: 'code_generation',
    payload: {
        prompt: 'Write a TypeScript function that calculates Fibonacci using memoization',
        language: 'typescript',
        maxTokens: 500,
        context: 'Performance-critical application',
    },
    preferences: { optimizeFor: 'quality' },
});
console.log(`Generated code:\n${code.result.code}`);
console.log(`Language: ${code.result.language}`);
```

### curl

```bash
curl -s "${AIP_ENDPOINT}/v1/intent/execute" \
  -H "Authorization: Bearer ${AIP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "code_generation",
    "payload": {
      "prompt": "Write a function that calculates Fibonacci using memoization",
      "language": "python",
      "max_tokens": 500
    },
    "preferences": { "optimize_for": "quality" }
  }'
```


### 预期输出

```json
{
  "success": true,
  "intent": "code_generation",
  "result": {
    "code": "def fibonacci(n: int) -> list[int]:\n    if n <= 0:\n        return []\n    fib = [0, 1]\n    for i in range(2, n):\n        fib.append(fib[-1] + fib[-2])\n    return fib[:n]",
    "language": "python",
    "explanation": "迭代方式生成斐波那契数列前 n 项。使用列表存储中间结果，时间复杂度 O(n)，空间复杂度 O(n)。",
    "tokensUsed": 156
  },
  "provider": "anthropic/claude-sonnet",
  "cost_usd": 0.003,
  "latency_ms": 2800
}
```

### 好处

- **代码与解释分离**：`code` 字段是纯可执行代码，`explanation` 是自然语言说明，方便自动化流水线直接提取代码
- **语言指定**：通过 `language` 参数确保生成目标语言代码，不会混入其他语言
- **专业模型路由**：AIP 可将代码任务路由到代码专长模型（如 Claude/GPT-4/CodeLlama），比通用模型质量更高
- **可直接集成 CI**：返回的 `code` 可直接写文件、跑测试，适合 Agent 自动化开发流程
- **成本可控**：相比直接用 chat intent 生成代码，code_generation intent 可优化 prompt 模板降低 token 消耗

---

## 18. 支持的 Intent 类型总览

| Intent 类型 | 说明 | 典型 Payload |
|------------|------|-------------|
| `chat_completion` | LLM 对话补全 | `messages`, `max_tokens`, `temperature` |
| `web_search` | 网页搜索 | `query`, `num_results` |
| `image_generation` | 图片生成 | `prompt`, `size`, `style` |
| `video_generation` | 视频生成 | `prompt`, `duration_seconds`, `resolution` |
| `text_to_speech` | 文字转语音 | `text`, `voice`, `speed` |
| `speech_to_text` | 语音转文字 | `audio_url`, `language` |
| `embedding` | 文本向量化 | `input`, `model` |
| `code_generation` | 代码生成 | `prompt`, `language`, `max_tokens` |
| `moderation` | 内容审核 | `input`, `categories` |
| `translation` | 文本翻译 | `text`, `source_lang`, `target_lang` |

> 使用 `client.list_intents()` 可实时获取最新支持列表。

---

## 19. SDK 与独立协议包的关系

| 包名 | 定位 | AIP 方法 |
|------|------|----------|
| **jarvisclaw** (Python) | 主 SDK (superset) | resolve, execute, execute_budget, subscribe, audit, list_intents, list_providers |
| **agent-intent-protocol** (Python) | 轻量独立包 | resolve, execute, subscribe, discover |
| **sdks/go** | Go SDK | Resolve, Execute, ExecuteBudget, Subscribe, ListIntents |
| **@jarvisclaw/agent-intent-protocol** (TS) | TypeScript SDK | resolve, execute, subscribe, listIntents, listProviders |

**普通用户只需安装一个主 SDK**，AIP 能力已全部内置。独立 `agent-intent-protocol` 包适合只需轻量 AIP 调用的场景。

---

## API 端点参考

| 操作 | HTTP 方法 | 端点 |
|------|-----------|------|
| Resolve | POST | `/v1/intent/resolve` |
| Execute | POST | `/v1/intent/execute` |
| Subscribe (SSE) | POST | `/v1/intent/subscribe` |
| Discover | GET | `/v1/intent/discover` |
| Health | GET | `/v1/intent/health` |
| Audit | GET | `/v1/intent/audit` |

---

## Preferences 参数

所有 Resolve / Execute / Subscribe 操作都支持 `preferences` 参数：

| 字段 | 类型 | 说明 |
|------|------|------|
| `optimize_for` | `"cost"` \| `"quality"` \| `"speed"` | 优化目标 |
| `max_price_usd` | float | 单次调用最大价格 |
| `preferred_provider` | string | 指定优先使用的 Provider |
| `fallback` | boolean | 是否允许降级到其他 Provider |

---

*文档版本: 2026-06-25 | 基于 agent-intent-protocol 仓库源码生成*
