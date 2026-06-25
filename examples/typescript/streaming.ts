import { AIPClient } from '@jarvisclaw/agent-intent-protocol';

/**
 * AIP Streaming — SSE stream for chat completion.
 *
 * Usage:
 *   export AIP_API_KEY="sk-your-key"
 *   npx tsx streaming.ts
 */
async function main() {
  const client = new AIPClient({ apiKey: process.env.AIP_API_KEY });

  console.log('─── Streaming chat completion ───');
  const stream = await client.subscribe({
    intent: 'chat_completion',
    payload: {
      messages: [{ role: 'user', content: 'Write a haiku about distributed systems.' }],
      stream: true,
    },
    preferences: { optimizeFor: 'speed' },
  });

  process.stdout.write('  Response: ');
  for await (const chunk of stream) {
    if (chunk.delta) {
      process.stdout.write(chunk.delta);
    }
  }
  console.log(`\n  Total tokens: ${stream.usage.totalTokens}`);
  console.log(`  Cost: $${stream.costUsd}`);
}

main().catch(console.error);
