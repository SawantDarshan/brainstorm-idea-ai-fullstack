import { useState, useRef, useEffect } from 'react';
import { useAgentStore } from '../stores/agentStore';
import { useCanvasStore } from '../stores/canvasStore';
import { apiNDJSON } from '../api/client';

export default function AgentPanel() {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const logRef = useRef<HTMLDivElement>(null);

  const { messages, addMessage, setThinking, updateThinkingText, setSuggestions, isSelecting, toggleSelecting, selectedNodeIds, isThinking } = useAgentStore();
  const { loadNodes, addNodeMeta } = useCanvasStore();

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [messages]);

  const send = async () => {
    const q = input.trim();
    if (!q || sending) return;
    setInput('');
    setSending(true);
    setSuggestions([]);
    addMessage({ role: 'user', text: q });
    setThinking(true, q.length > 40 ? q.slice(0, 40) + '…' : q);

    let lastReply = '';
    try {
      await apiNDJSON('/api/agent/converse', {
        message: q,
        conversation_history: messages.slice(-10),
        selected_node_ids: [...selectedNodeIds],
      }, (msg) => {
        if (msg.type === 'thinking') updateThinkingText(msg.text as string);
        else if (msg.type === 'step' && msg.status === 'running') updateThinkingText((msg.text || msg.step) as string);
        else if (msg.type === 'action') {
          addMessage({ role: 'action', text: msg.text as string });
          if (msg.action === 'reload') loadNodes();
        }
        else if (msg.type === 'reply') { lastReply = msg.text as string; }
        else if (msg.type === 'nodes_created') {
          addMessage({ role: 'action', text: `✅ Created ${msg.count} node(s)` });
          if (msg.nodes && Array.isArray(msg.nodes)) {
            (msg.nodes as Array<Record<string, unknown>>).forEach((n) => addNodeMeta(n as any));
          }
          if ((msg.count as number) > 2) loadNodes();
        }
        else if (msg.type === 'error') addMessage({ role: 'action', text: '❌ ' + msg.text });
        else if (msg.type === 'suggestions') setSuggestions(msg.suggestions as string[]);
      });
      if (lastReply) addMessage({ role: 'ai', text: lastReply });
    } catch (err: any) {
      addMessage({ role: 'ai', text: '❌ ' + (err.message || 'Failed') });
    }
    setThinking(false);
    setSending(false);
  };

  const suggestions = useAgentStore(s => s.suggestions);

  return (
    <div className="fixed bottom-4 left-4 w-[400px] max-w-[90vw] glass rounded-xl overflow-hidden shadow-2xl z-50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5">
        <span className="text-sm font-bold text-amber-500">🤖 AI Agent</span>
        <button
          onClick={toggleSelecting}
          className={`text-[0.6rem] px-2 py-1 rounded border transition-all ${isSelecting ? 'bg-amber-500 text-black border-amber-500 font-bold' : 'border-white/10 text-white/50 hover:text-amber-500'}`}
        >
          {isSelecting ? `✓ Done (${selectedNodeIds.size})` : `🎯 Select (${selectedNodeIds.size})`}
        </button>
      </div>

      {/* Messages */}
      <div ref={logRef} className="max-h-[300px] min-h-[100px] overflow-y-auto p-3 flex flex-col gap-1.5">
        {messages.length === 0 && (
          <div className="text-center text-white/30 text-xs font-mono py-8">
            Talk naturally — research topics, create notes, ask questions…
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`text-xs font-mono px-2 py-1.5 rounded max-w-[90%] break-words ${
            m.role === 'user' ? 'self-end bg-amber-500 text-black rounded-br-sm' :
            m.role === 'ai' ? 'self-start bg-white/5 text-white/80 border border-white/5 rounded-bl-sm' :
            'self-center bg-amber-500/10 text-amber-500 border border-amber-500/20 italic text-[0.6rem]'
          }`}>
            {m.text}
          </div>
        ))}
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="flex gap-1 flex-wrap px-3 pb-2">
          {suggestions.map((s, i) => (
            <button key={i} onClick={() => { setInput(s); }} className="text-[0.68rem] font-semibold px-3 py-1.5 rounded-full bg-amber-500/10 text-amber-500 border border-amber-500/20 hover:bg-amber-500 hover:text-black transition-all">
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="flex gap-2 p-3 border-t border-white/5">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Talk naturally…"
          rows={1}
          className="flex-1 bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono text-white resize-none outline-none focus:border-amber-500/30"
        />
        <button
          onClick={send}
          disabled={sending}
          className="px-4 py-2 bg-amber-500 text-black text-xs font-bold rounded-lg hover:brightness-110 disabled:opacity-40 transition-all"
        >
          {sending ? '…' : 'Send ⏎'}
        </button>
      </div>

      {/* Thinking overlay indicator */}
      {isThinking && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm rounded-xl pointer-events-none">
          <div className="text-center">
            <div className="text-sm font-bold text-amber-500 animate-pulse">Thinking…</div>
            <div className="text-[0.6rem] text-white/40 mt-1">{useAgentStore.getState().thinkingText}</div>
          </div>
        </div>
      )}
    </div>
  );
}