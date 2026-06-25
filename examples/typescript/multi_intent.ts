import { AIPClient } from '@jarvisclaw/agent-intent-protocol';

/**
 * AIP Multi-Intent — Chain search → summarize → image → TTS.
 *
 * Usage:
 *   export AIP_API_KEY="sk-your-key"
 *   npx tsx multi_intent.ts
 */
async function main() {
  const client = new AIPClient({ apiKey: process.env.AIP_API_KEY });

  // Step 1: Web search
  console.log('─── Step 1: Web Search ───');
  const search = await client.execute({
    intent: 'web_search',
    payload: { query: 'Agent Intent Protocol specification' },
  });
  console.log(`  Found ${search.result.results?.length ?? 0} results`);

  // Step 2: Summarize
  console.log('\n─── Step 2: Summarize ───');
  const snippets = (search.result.results || [])
    .slice(0, 3)
    .map((r: any) => r.snippet)
    .join('\n');

  const summary = await client.execute({
    intent: 'chat_completion',
    payload: {
      messages: [
        { role: 'system', content: 'Summarize the following search results concisely.' },
        { role: 'user', content: snippets },
      ],
      max_tokens: 200,
    },
    preferences: { optimizeFor: 'quality' },
  });
  const text = summary.result.choices[0].message.content;
  console.log(`  Summary: ${text.slice(0, 120)}...`);

  // Step 3: Generate image
  console.log('\n─── Step 3: Image Generation ───');
  const image = await client.execute({
    intent: 'image_generation',
    payload: { prompt: `A conceptual diagram of: ${text.slice(0, 100)}`, size: '1024x1024' },
  });
  console.log(`  Image URL: ${image.result.url ?? 'N/A'}`);

  // Step 4: Text to speech
  console.log('\n─── Step 4: TTS ───');
  const tts = await client.execute({
    intent: 'text_to_speech',
    payload: { text, voice: 'alloy' },
  });
  console.log(`  Audio format: ${tts.result.format ?? 'mp3'}`);

  // Total cost
  const total = [search, summary, image, tts].reduce((s, r) => s + (r.costUsd || 0), 0);
  console.log(`\n─── Total cost: $${total.toFixed(6)} ───`);
}

main().catch(console.error);
