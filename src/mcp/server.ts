import { StdioServerTransport, Server } from '@modelcontextprotocol/sdk/server/index.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { generateAd } from '../services/agent.js';

const server = new Server({ name: 'ad-agent-mcp', version: '0.1.0' });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: 'generate_ad', description: 'Generate ad caption and optional image', inputSchema: { type: 'object', properties: { description: { type: 'string' }, tone: { type: 'string' }, audience: { type: 'string' } }, required: ['description'] } },
    { name: 'post_now', description: 'Generate and post an ad immediately', inputSchema: { type: 'object', properties: {} } }
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;
  if (name === 'generate_ad') {
    const ad = await generateAd({ description: String(args?.description || ''), tone: String(args?.tone || 'engaging'), audience: String(args?.audience || 'broad'), requestAIGeneratedImage: true });
    return { content: [{ type: 'text', text: JSON.stringify(ad) }] } as any;
  }
  if (name === 'post_now') {
    const mod = await import('../services/agent.js');
    const result = await mod.planAndPostNext();
    return { content: [{ type: 'text', text: JSON.stringify(result) }] } as any;
  }
  return { content: [{ type: 'text', text: 'unknown tool' }] } as any;
});

const transport = new StdioServerTransport();
server.connect(transport);
