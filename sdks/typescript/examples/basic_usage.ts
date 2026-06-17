import { AIPClient } from '../src/index';

/**
 * Example: Basic intent resolution
 */
async function main() {
  // Create client (defaults to https://api.jarvisclaw.ai)
  const client = new AIPClient();

  // Example 1: Find cheapest chat completion
  console.log('=== Cheapest Chat Completion ===');
  const costResult = await client.resolve({
    intent: 'chat_completion',
    constraints: { maxPriceUsd: 0.01 },
    preferences: { optimizeFor: 'cost' },
  });
  if (costResult.success && costResult.bestMatch) {
    console.log(`Provider: ${costResult.bestMatch.providerName}`);
    console.log(`Model: ${costResult.bestMatch.model}`);
    console.log(`Price: $${costResult.bestMatch.priceUsd}`);
  }

  // Example 2: Highest quality with function calling
  console.log('\n=== Highest Quality with Function Calling ===');
  const qualityResult = await client.resolve({
    intent: 'chat_completion',
    constraints: { features: ['function_calling'] },
    preferences: { optimizeFor: 'quality' },
  });
  if (qualityResult.success && qualityResult.bestMatch) {
    console.log(`Provider: ${qualityResult.bestMatch.providerName}`);
    console.log(`Score: ${qualityResult.bestMatch.score}`);
  }

  // Example 3: List available providers
  console.log('\n=== Available Providers ===');
  const providers = await client.listProviders('chat_completion');
  providers.forEach(p => {
    console.log(`  ${p.providerName} — ${p.model} ($${p.priceUsd})`);
  });
}

main().catch(console.error);
