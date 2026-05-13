import { useState, useEffect } from 'react';
import { useCanvasStore } from '../stores/canvasStore';
import { apiStream, apiJson, apiFetch } from '../api/client';

export default function NodePanel() {
  const selectedNodeId = useCanvasStore(s => s.selectedNodeId);
  const nodesMeta = useCanvasStore(s => s.nodesMeta);
  const selectNode = useCanvasStore(s => s.selectNode);

  const [content, setContent] = useState('');
  const [filename, setFilename] = useState('');
  const [tab, setTab] = useState<'content' | 'chat'>('content');
  const [chatMessages, setChatMessages] = useState<{ role: string; text: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);

  const meta = nodesMeta.find(n => n.node_id === selectedNodeId);

  useEffect(() => {
    if (!selectedNodeId) return;
    setContent('');
    setFilename(meta?.filename || '');
    setTab('content');
    // Stream content
    let text = '';
    apiStream(`/api/knowledge/${selectedNodeId}`, {}, (chunk) => {
      text += chunk;
      setContent(text);
    }).catch(() => setContent('❌ Failed to load'));
  }, [selectedNodeId]);

  const handleSave = async () => {
    if (!selectedNodeId) return;
    await apiJson(`/api/nodes/${selectedNodeId}`, {
      method: 'PUT',
      body: JSON.stringify({ filename: filename.trim(), content }),
    });
  };

  const sendChat = async () => {
    const q = chatInput.trim();
    if (!q || !selectedNodeId) return;
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', text: q }]);
    setChatSending(true);
    let reply = '';
    try {
      const res = await apiFetch('/api/agent/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_ids: [selectedNodeId], question: q }),
      });
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        reply += decoder.decode(value, { stream: true });
        setChatMessages(prev => {
          const msgs = [...prev];
          const last = msgs[msgs.length - 1];
          if (last && last.role === 'ai') { last.text = reply; return [...msgs]; }
          return [...msgs, { role: 'ai', text: reply }];
        });
      }
    } catch (err: any) {
      setChatMessages(prev => [...prev, { role: 'ai', text: '❌ ' + err.message }]);
    }
    setChatSending(false);
  };

  if (!selectedNodeId) return null;

  return (
    <div className="fixed top-[52px] right-0 bottom-0 w-[440px] max-w-[90vw] glass border-l border-white/5 z-[150] flex flex-col animate-[slideIn_0.3s_ease]">
      {/* Header */}
      <div className="flex items-center gap-2 p-4 border-b border-white/5">
        <input
          value={filename}
          onChange={e => setFilename(e.target.value)}
          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm font-semibold text-amber-500 outline-none focus:border-amber-500/30"
        />
        <button onClick={handleSave} className="w-8 h-8 flex items-center justify-center bg-white/5 border border-white/10 rounded-lg text-amber-500 hover:bg-amber-500/10 transition-all">💾</button>
        <button onClick={() => selectNode(null)} className="w-8 h-8 flex items-center justify-center bg-white/5 border border-white/10 rounded-lg text-white/40 hover:text-white transition-all">✕</button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/5">
        <button onClick={() => setTab('content')} className={`flex-1 py-2.5 text-xs font-semibold text-center border-b-2 transition-all ${tab === 'content' ? 'text-amber-500 border-amber-500' : 'text-white/40 border-transparent'}`}>📄 Content</button>
        <button onClick={() => setTab('chat')} className={`flex-1 py-2.5 text-xs font-semibold text-center border-b-2 transition-all ${tab === 'chat' ? 'text-amber-500 border-amber-500' : 'text-white/40 border-transparent'}`}>💬 Chat with Doc</button>
      </div>

      {/* Content Tab */}
      {tab === 'content' && (
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          className="flex-1 p-4 bg-transparent text-xs font-mono text-white/80 leading-relaxed resize-none outline-none overflow-y-auto"
          placeholder="Content…"
        />
      )}

      {/* Chat Tab */}
      {tab === 'chat' && (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
            {chatMessages.length === 0 && <div className="text-center text-white/30 text-xs py-8">Ask any question about this document</div>}
            {chatMessages.map((m, i) => (
              <div key={i} className={`text-xs font-mono px-3 py-2 rounded-xl max-w-[90%] break-words ${m.role === 'user' ? 'self-end bg-amber-500 text-black rounded-br-sm' : 'self-start bg-white/5 text-white/80 border border-white/5 rounded-bl-sm'}`}>
                {m.text}
              </div>
            ))}
          </div>
          <div className="flex gap-2 p-3 border-t border-white/5">
            <textarea
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } }}
              placeholder="Ask about this document…"
              rows={1}
              className="flex-1 bg-black/20 border border-white/10 rounded-lg px-3 py-2 text-xs font-mono text-white resize-none outline-none focus:border-amber-500/30"
            />
            <button onClick={sendChat} disabled={chatSending} className="px-3 py-2 bg-amber-500 text-black text-xs font-bold rounded-lg disabled:opacity-40">Ask ⏎</button>
          </div>
        </div>
      )}
    </div>
  );
}