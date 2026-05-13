import { useState } from 'react';
import { useCanvasStore } from '../stores/canvasStore';
import { apiJson, logout, getAuthUser } from '../api/client';

export default function Toolbar() {
  const [organizing, setOrganizing] = useState(false);
  const [showResearch, setShowResearch] = useState(false);
  const [researchTopic, setResearchTopic] = useState('');
  const [researchStatus, setResearchStatus] = useState('');
  const loadNodes = useCanvasStore(s => s.loadNodes);
  const user = getAuthUser();

  const handleOrganize = async () => {
    setOrganizing(true);
    try {
      await apiJson('/api/agent/organize', {
        method: 'POST',
        body: JSON.stringify({ pattern: 'categories', custom_instruction: '' }),
      });
      await loadNodes();
    } catch (err: any) {
      alert('Organize failed: ' + err.message);
    }
    setOrganizing(false);
  };

  const handleResearch = async () => {
    if (!researchTopic.trim()) return;
    setResearchStatus('Researching…');
    try {
      await apiJson('/api/agent/research', {
        method: 'POST',
        body: JSON.stringify({ topic: researchTopic.trim() }),
      });
      setResearchStatus('Done!');
      await loadNodes();
      setTimeout(() => { setShowResearch(false); setResearchStatus(''); setResearchTopic(''); }, 800);
    } catch (err: any) {
      setResearchStatus('❌ ' + err.message);
    }
  };

  return (
    <>
      <div className="fixed top-0 left-0 right-0 z-[200] h-[52px] glass border-b border-white/5 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <span className="font-extrabold text-amber-500 text-sm tracking-tight">◈ AI Canvas</span>
          <button onClick={() => setShowResearch(true)} className="h-8 px-3 text-xs font-semibold bg-white/5 border border-white/10 rounded-md text-white/80 hover:text-amber-500 hover:border-amber-500/30 transition-all">
            🔬 Research
          </button>
          <button onClick={handleOrganize} disabled={organizing} className="h-8 px-3 text-xs font-semibold bg-white/5 border border-white/10 rounded-md text-white/80 hover:text-amber-500 hover:border-amber-500/30 transition-all disabled:opacity-40">
            {organizing ? '⏳ Organizing…' : '✨ Organize'}
          </button>
          <span className="text-[0.6rem] font-mono text-white/30 ml-2">Scroll=zoom · Drag=pan · Ctrl+K=search</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[0.7rem] text-white/40 truncate max-w-[100px]">{user.name}</span>
          {user.photo && <img src={user.photo} className="w-7 h-7 rounded-full border border-white/10" />}
          <button onClick={logout} className="h-8 px-3 text-xs font-semibold bg-white/5 border border-white/10 rounded-md text-white/80 hover:text-red-400 transition-all">
            🚪
          </button>
        </div>
      </div>

      {/* Research Modal */}
      {showResearch && (
        <div className="fixed inset-0 z-[350] bg-black/40 flex items-center justify-center" onClick={() => setShowResearch(false)}>
          <div className="glass rounded-xl p-6 w-[420px] max-w-[90vw] shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-base font-bold text-white mb-3">🔬 Research a Topic</h3>
            <input
              value={researchTopic}
              onChange={e => setResearchTopic(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleResearch(); }}
              placeholder="e.g. Quantum computing applications"
              className="w-full px-3 py-2.5 bg-black/20 border border-white/10 rounded-lg text-sm font-mono text-white outline-none focus:border-amber-500/30 mb-3"
              autoFocus
            />
            <div className="flex gap-2 justify-end">
              <button onClick={() => setShowResearch(false)} className="px-4 py-2 text-xs font-bold text-white/50 border border-white/10 rounded-lg hover:text-white transition-all">Cancel</button>
              <button onClick={handleResearch} className="px-4 py-2 text-xs font-bold bg-amber-500 text-black rounded-lg hover:brightness-110 transition-all">Research</button>
            </div>
            {researchStatus && <div className="text-xs font-mono text-white/40 mt-3">{researchStatus}</div>}
          </div>
        </div>
      )}
    </>
  );
}