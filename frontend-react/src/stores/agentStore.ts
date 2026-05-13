import { create } from 'zustand';

export interface AgentMessage {
  role: 'user' | 'ai' | 'action';
  text: string;
}

interface AgentState {
  messages: AgentMessage[];
  isThinking: boolean;
  thinkingText: string;
  suggestions: string[];
  selectedNodeIds: Set<string>;
  isSelecting: boolean;

  addMessage: (msg: AgentMessage) => void;
  setThinking: (thinking: boolean, text?: string) => void;
  updateThinkingText: (text: string) => void;
  setSuggestions: (suggestions: string[]) => void;
  toggleSelecting: () => void;
  toggleNodeSelection: (nodeId: string) => void;
  clearSelection: () => void;
}

const STORAGE_KEY = 'agentConvoHistory';

function loadMessages(): AgentMessage[] {
  try {
    return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]');
  } catch { return []; }
}

function persistMessages(msgs: AgentMessage[]) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(msgs.slice(-50)));
  } catch { /* ignore */ }
}

export const useAgentStore = create<AgentState>((set, get) => ({
  messages: loadMessages(),
  isThinking: false,
  thinkingText: '',
  suggestions: [],
  selectedNodeIds: new Set(),
  isSelecting: false,

  addMessage: (msg) => {
    const messages = [...get().messages, msg];
    persistMessages(messages);
    set({ messages });
  },

  setThinking: (thinking, text = '') => set({ isThinking: thinking, thinkingText: text }),
  updateThinkingText: (text) => set({ thinkingText: text }),
  setSuggestions: (suggestions) => set({ suggestions }),

  toggleSelecting: () => set({ isSelecting: !get().isSelecting }),

  toggleNodeSelection: (nodeId) => {
    const s = new Set(get().selectedNodeIds);
    if (s.has(nodeId)) s.delete(nodeId);
    else s.add(nodeId);
    set({ selectedNodeIds: s });
  },

  clearSelection: () => set({ selectedNodeIds: new Set(), isSelecting: false }),
}));