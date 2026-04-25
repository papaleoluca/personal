export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Max-Age': '86400',
        },
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    const GEMINI_KEY = env.GEMINI_API_KEY;
    if (!GEMINI_KEY) {
      return jsonResponse({ error: 'API key not configured' }, 500);
    }

    try {
      const body = await request.json();
      const text = body.text;
      if (!text || typeof text !== 'string') {
        return jsonResponse({ error: 'Missing "text" field' }, 400);
      }

      const prompt = `You are a flow diagram generator. Analyze the following text and extract its logical flow as a structured JSON object.

Rules:
- Identify sequential steps, decision points (yes/no questions), and branches.
- Respond in the SAME LANGUAGE as the input text.
- Keep node text concise (max ~15 words per node).
- Give the diagram a short descriptive title.
- Return ONLY valid JSON, no markdown fences, no explanation.

JSON schema:
{
  "title": "string",
  "nodes": [
    { "type": "start", "text": "string" },
    { "type": "step", "text": "string" },
    { "type": "decision", "text": "string", "yes_label": "string", "no_label": "string", "yes_branch": [ ...nodes ], "no_branch": [ ...nodes ] },
    { "type": "end", "text": "string" }
  ]
}

Text to analyze:
${text}`;

      const geminiRes = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_KEY}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
            generationConfig: {
              temperature: 0.3,
              responseMimeType: 'application/json',
            },
          }),
        }
      );

      if (!geminiRes.ok) {
        const err = await geminiRes.json().catch(() => ({}));
        return jsonResponse({ error: err?.error?.message || `Gemini API error ${geminiRes.status}` }, 502);
      }

      const data = await geminiRes.json();
      const raw = data?.candidates?.[0]?.content?.parts?.[0]?.text;
      if (!raw) {
        return jsonResponse({ error: 'Empty response from Gemini' }, 502);
      }

      return jsonResponse(JSON.parse(raw), 200);

    } catch (e) {
      return jsonResponse({ error: e.message }, 500);
    }
  },
};

function jsonResponse(data, status) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
  });
}
