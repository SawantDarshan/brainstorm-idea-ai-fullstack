import { create } from 'zustand';
import { Node, Edge, NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges } from 'reactflow';
import { apiJson, apiFetch } from '../api/client';

export interface NodeMeta {
  node_id: string;
  filename: string;
  characters: number;
  x: number;
  y: number;
  parent_id: string | null;
  node_type: string;
  group_id?: string | null;
  session_id?: string;
  source?: string;
}

interface CanvasState {
  nodesMeta: NodeMeta[];
  rfNodes: Node[];
  rfEdges: Edge[];
  selectedNodeId: string | null;
  isLoading: boolean;

  // Actions
  loadNodes: () => Promise<void>;
  addNodeMeta: (meta: NodeMeta) => void;
  removeNode: (nodeId: string) => Promise<void>;
  updatePosition: (nodeId: string, x: number, y: number) => void;
  selectNode: (nodeId: string | null) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  connectNodes: (sourceId: string, targetId: string, action: string) => Promise<void>;
  disconnectNodes: (sourceId: string, targetId: string) => Promise<void>;
  ungroupNode: (nodeId: string) => Promise<void>;
}

function metaToRFNodes(metas: NodeMeta[]): Node[] {
  return metas
    .filter(m => m.node_type !== 'system')
    .map(m => ({
      id: m.node_id,
      type: m.node_type === 'conversation' ? 'conversation' : 'knowledge',
      position: { x: m.x - 10000, y: m.y - 10000 }, // Convert from canvas coords
      data: { label: m.filename, characters: m.characters, meta: m },
    }));
}

function metaToRFEdges(metas: NodeMeta[]): Edge[] {
  return metas
    .filter(m => m.parent_id && m.node_type !== 'system')
    .map(m => ({
      id: `e-${m.parent_id}-${m.node_id}`,
      source: m.parent_id!,
      target: m.node_id,
      type: 'smoothstep',
      animated: false,
      style: { stroke: '#f0a030', strokeDasharray: '8 6', opacity: 0.3 },
    }));
}

export const useCanvasStore = create<CanvasState>((set, get) => ({
  nodesMeta: [],
  rfNodes: [],
  rfEdges: [],
  selectedNodeId: null,
  isLoading: false,

  loadNodes: async () => {
    set({ isLoading: true });
    try {
      const metas = await apiJson<NodeMeta[]>('/api/nodes');
      set({
        nodesMeta: metas,
        rfNodes: metaToRFNodes(metas),
        rfEdges: metaToRFEdges(metas),
        isLoading: false,
      });
    } catch (e) {
      console.error('Failed to load nodes:', e);
      set({ isLoading: false });
    }
  },

  addNodeMeta: (meta) => {
    const metas = [...get().nodesMeta, meta];
    set({
      nodesMeta: metas,
      rfNodes: metaToRFNodes(metas),
      rfEdges: metaToRFEdges(metas),
    });
  },

  removeNode: async (nodeId) => {
    await apiFetch(`/api/nodes/${nodeId}`, { method: 'DELETE' });
    const metas = get().nodesMeta.filter(m => m.node_id !== nodeId);
    set({
      nodesMeta: metas,
      rfNodes: metaToRFNodes(metas),
      rfEdges: metaToRFEdges(metas),
      selectedNodeId: get().selectedNodeId === nodeId ? null : get().selectedNodeId,
    });
  },

  updatePosition: (nodeId, x, y) => {
    // Debounced save to backend
    const canvasX = x + 10000;
    const canvasY = y + 10000;
    apiFetch(`/api/nodes/${nodeId}/position`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ x: canvasX, y: canvasY }),
    }).catch(() => {});
    // Update local
    const metas = get().nodesMeta.map(m =>
      m.node_id === nodeId ? { ...m, x: canvasX, y: canvasY } : m
    );
    set({ nodesMeta: metas });
  },

  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),

  onNodesChange: (changes) => {
    set({ rfNodes: applyNodeChanges(changes, get().rfNodes) });
  },

  onEdgesChange: (changes) => {
    set({ rfEdges: applyEdgeChanges(changes, get().rfEdges) });
  },

  connectNodes: async (sourceId, targetId, action) => {
    await apiJson('/api/nodes/connect', {
      method: 'POST',
      body: JSON.stringify({ source_id: sourceId, target_id: targetId, action }),
    });
    await get().loadNodes();
  },

  disconnectNodes: async (sourceId, targetId) => {
    await apiJson('/api/nodes/disconnect', {
      method: 'POST',
      body: JSON.stringify({ source_id: sourceId, target_id: targetId }),
    });
    await get().loadNodes();
  },

  ungroupNode: async (nodeId) => {
    await apiJson('/api/nodes/ungroup', {
      method: 'POST',
      body: JSON.stringify({ node_id: nodeId }),
    });
    await get().loadNodes();
  },
}));