import { AIPClient } from '@jarvisclaw/agent-intent-protocol';

/**
 * AIP Quickstart — Resolve, Execute, and Discover intents.
 *
 * Usage:
 *   export AIP_API_KEY="sk-your-key"
 *   npx tsx quickstart.ts
 */
async function main() {
  const client = new AIPClient({ apiKey: process.env.AIP_API_KEY });

  // ── 1. Resolve: find the best provider ──────────────────────────
  console.log('─── Resolve: cheapest chat completion ───');
  const resolved = await client.resolve({
    intent: 'chat_completion',
    constraints: { maxPriceUsd: 0.01 },
    preferences: { optimizeFor: 'cost' },
  });
  if (resolved.success && resolved.bestMatch) {
    console.log(`  Provider : ${resolved.bestMatch.providerName}`);
    console.log(`  Model    : ${resolved.bestMatch.model}`);
    console.log(`  Price    : $${resolved.bestMatch.priceUsd}`);
    console.log(`  Latency  : ${resolved.bestMatch.latencyMs}ms`);
  }

  // ── 2. Execute: run a chat completion ───────────────────────────
  console.log('\n─── Execute: chat completion ───');
  const exec = await client.execute({
    intent: 'chat_completion',
    payload: {
      messages: [{ role: 'user', content: 'Explain AIP in one sentence.' }],
      max_tokens: 100,
    },
    preferences: { optimizeFor: 'quality' },
  });
  if (exec.success) {
    console.log(`  Provider : ${exec.provider}`);
    console.log(`  Response : ${exec.result.choices[0].message.content}`);
    console.log(`  Cost     : $${exec.costUsd}`);
  }

  // ── 3. Discover: list available intents ─────────────────────────
  console.log('\n─── Discover: available intents ───');
  const intents = await client.listIntents();
  for (const intent of intents) {
    const providers = await client.listProviders(intent);
    console.log(`  ${intent}: ${providers.length} providers`);
  }
}

main().catch(console.error);
