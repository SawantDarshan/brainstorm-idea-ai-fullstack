import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useCanvasStore } from '../stores/canvasStore';
import { useAgentStore } from '../stores/agentStore';

function KnowledgeNode({ id, data, selected }: NodeProps) {
  const selectNode = useCanvasStore(s => s.selectNode);
  const removeNode = useCanvasStore(s => s.removeNode);
  const isSelecting = useAgentStore(s => s.isSelecting);
  const selectedNodeIds = useAgentStore(s => s.selectedNodeIds);
  const toggleNodeSelection = useAgentStore(s => s.toggleNodeSelection);
  const isAgentSelected = selectedNodeIds.has(id);

  const handleClick = () => {
    if (isSelecting) {
      toggleNodeSelection(id);
    } else {
      selectNode(id);
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`
        group glass rounded-xl px-4 py-3 w-[240px] cursor-grab
        transition-all duration-200 hover:border-amber-500/30 hover:shadow-[0_0_20px_rgba(240,160,48,0.1)]
        ${selected ? 'border-amber-500/50 shadow-[0_0_20px_rgba(240,160,48,0.15)]' : ''}
        ${isAgentSelected ? 'border-purple-500/60 shadow-[0_0_20px_rgba(168,85,247,0.2)] ring-1 ring-purple-500/30' : ''}
        ${isSelecting ? 'cursor-pointer' : ''}
      `}
    >
      <Handle type="target" position={Position.Top} className="!bg-amber-500 !w-2.5 !h-2.5 !border-2 !border-[#12121a] opacity-0 group-hover:opacity-100 transition-opacity" />
      <Handle type="source" position={Position.Bottom} className="!bg-amber-500 !w-2.5 !h-2.5 !border-2 !border-[#12121a] opacity-0 group-hover:opacity-100 transition-opacity" />

      <div className="flex items-start gap-3">
        <span className="text-xl flex-shrink-0 mt-0.5 text-amber-500">⬡</span>
        <div className="flex-1 min-w-0">
          <div className="text-[0.8rem] font-semibold text-white/90 truncate">{data.label}</div>
          <div className="text-[0.62rem] font-mono text-purple-400/50 mt-1">
            {(data.characters || 0).toLocaleString()} chars
          </div>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); removeNode(id); }}
          className="opacity-0 group-hover:opacity-60 hover:!opacity-100 text-[0.6rem] text-red-400 hover:bg-red-500/10 w-5 h-5 flex items-center justify-center rounded transition-all"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

export default memo(KnowledgeNode);