# AI Canvas — Complete Functionality Inventory

This document lists every feature in the current vanilla JS canvas dashboard that must be replicated in the React + ReactFlow rewrite.

---

## 1. Authentication & User

- Firebase Google Sign-In (handled on login page)
- Auth token stored in `localStorage` (`auth_token`)
- Token auto-injected into all `/api/*` fetch requests via `Authorization: Bearer` header
- Token auto-refresh every 50 minutes via Firebase SDK
- 401/403 responses redirect to `/login`
- User name & photo displayed in toolbar
- Logout button (clears token + Firebase sign-out)

---

## 2. Canvas (Infinite Workspace)

### Pan & Zoom
- Mouse wheel = zoom in/out (range 0.2x – 3x)
- Space + drag = pan canvas
- Middle-click drag = pan
- Touch: single finger pan, two-finger pinch zoom
- Zoom controls (bottom-right): +/− buttons with percentage display

### Grid Background
- Dot-pattern grid that moves with pan/zoom
- Dark/light theme aware

### Nodes on Canvas
- Positioned absolutely on a 20000×20000 virtual canvas
- Draggable (mouse + touch with long-press detection)
- Position saved to backend after drag (`PATCH /api/nodes/:id/position`)
- Node types: `knowledge`, `conversation`, `system`
- Node appearance: glass-morphism card with icon, filename, character count
- Hover preview tooltip (shows first 250 chars of content)
- Delete button (appears on hover, calls `DELETE /api/nodes/:id`)
- Click to open side panel
- Loading state animation (spinner icon)
- Error state (red border + error message)
- Appear animation on creation

### Connectors (Edges)
- Bezier curve connectors between parent/child nodes
- SVG-based, dashed style
- Hover highlight (thicker, more opaque)
- Click connector to show "Disconnect" button
- Disconnect calls `POST /api/nodes/disconnect`

### Port-based Connection
- 4 ports per node (top, bottom, left, right)
- Ports appear on hover
- Drag from port = rubber-band line
- Drop on another node = show connect menu
- Connect menu options: "Set as Parent", "Set as Child", "Group Together"
- Calls `POST /api/nodes/connect`

### Groups
- Nodes with same `group_id` get a colored dashed rectangle around them
- 5 rotating group colors
- Group label shows "📦 Group (N)"
- Click label to ungroup all nodes
- Drag group handle = moves all grouped nodes together
- Group positions saved to backend

### Right-Click Context Menu
- "Remove from Group" (if grouped)
- "Disconnect from Parent" (if has non-system parent)
- "Delete Node"

---

## 3. Toolbar (Top Bar)

- App title "◈ AI Canvas"
- **Research button** → opens Research Modal
- **Organize button** → calls `/api/agent/organize`, shows loading state
- Hint text: "Scroll=zoom · Space+drag=pan · Dbl-click=note · Ctrl+K=search"
- **AI Provider Settings button** → opens Provider Modal
- **Theme toggle** (dark/light) — persisted to localStorage
- User name + photo
- Logout button

---

## 4. AI Agent Panel (System Node on Canvas)

### Conversation Log
- Scrollable chat history (user messages + AI responses + action indicators)
- Messages persisted to `sessionStorage` (survives canvas reload)
- Empty state placeholder text
- AI responses have "💾 Save as Node" button (appears on hover)

### Input
- Text input (textarea, Enter to send, Shift+Enter for newline)
- 🎙 Mic button for voice input (Web Speech API)
- Voice auto-sends after recognition

### Node Selection
- "🎯 Select" toggle button
- When active, clicking nodes selects/deselects them (purple glow)
- Selected node IDs sent with agent requests

### Agent Communication
- Streams NDJSON from `POST /api/agent/converse`
- Message types handled:
  - `thinking` → updates thinking overlay subtitle
  - `pipeline_start` → shows first step label
  - `step` → updates thinking subtitle
  - `pipeline_done` → (handled by stream end)
  - `action` → shows action indicator in chat; if `action === 'reload'`, refreshes canvas
  - `reply` → shows AI response in chat
  - `nodes_created` → adds nodes directly to canvas, shows count
  - `error` → shows error in chat
  - `suggestions` → shows clickable suggestion chips below input

### Canvas Thinking Overlay
- Purple radial gradient pulse on entire canvas
- Centered headline (shimmer gradient animation)
- Subtitle text (updates with agent progress)
- Bouncing dots animation
- Fade-out when done

### Suggestion Chips
- Displayed below input after AI response
- Click = auto-fill input and send

---

## 5. Side Panel (Right Drawer)

### Header
- Editable filename input
- Save button (💾) → `PUT /api/nodes/:id`
- Close button (✕)

### Tabs
- **📄 Content** — Textarea showing full node content (streamed from `GET /api/knowledge/:id`)
- **💬 Chat with Doc** — Chat interface for asking questions about the document

### Content Tab
- Full text content, editable
- Streamed loading (chunks appear progressively)

### Chat with Doc Tab
- Message history per node (in-memory, keyed by nodeId)
- User sends question → `POST /api/agent/ask` with `node_ids` + `question`
- Response streamed and displayed progressively
- "streaming" opacity state while loading

---

## 6. Create Notes (Bottom Bar)

- "📝 Create Notes" button opens modal
- Modal has:
  - Title input (optional, AI generates if empty)
  - Large textarea for pasting notes/text
  - File drop zone (PDF/TXT/MD)
  - File input (click to browse)
  - "🧠 Generate Mind Map" button
- Calls `POST /api/notes/generate` (multipart form: file + text + title)
- Shows progress status
- On success: refreshes canvas to show new nodes

---

## 7. Research Modal

- Input for research topic
- "Research" button
- Calls `POST /api/agent/research`
- Shows loading status
- On success: refreshes canvas

---

## 8. Provider Settings Modal

- Lists all available AI providers (from `GET /api/providers`)
- Each provider shows:
  - Name, description, active indicator
  - API key input (password field, shows "(saved)" if key exists)
  - Model dropdown (from provider's model list)
  - "Activate" button → `POST /api/providers/active`
  - "Test" button → `POST /api/providers/test`
- Status text shows test results or activation confirmation

---

## 9. Command Palette (Ctrl+K)

- Backdrop overlay
- Search input with placeholder "Search nodes, actions…"
- Results list:
  - Actions: Research, Auto-organize, Create Notes
  - All non-system nodes (filterable by name)
- Keyboard navigation (↑/↓/Enter/Escape)
- Click action = executes it
- Click node = pans canvas to node + opens side panel

---

## 10. Double-Click Quick Note

- Double-click on empty canvas area
- Creates a "New note" node at click position via `POST /api/chat`
- Positions it at click coordinates
- Opens side panel for immediate editing

---

## 11. Drag & Drop File Upload

- Drag files over canvas → shows overlay "Release to upload"
- Drop PDF files → uploads each via `POST /api/upload?x=...&y=...`
- Creates loading node at drop position
- On success: updates node with ID and character count
- On error: shows error state on node

---

## 12. Theme System

- Dark/Light mode toggle
- CSS custom properties for all colors
- Glass-morphism (backdrop-filter blur + semi-transparent backgrounds)
- Accent color: amber/gold
- Font: Outfit (display) + IBM Plex Mono (code/status)
- Persisted to localStorage

---

## 13. Responsive / Touch Support

- Touch pan (single finger on canvas)
- Touch pinch-to-zoom (two fingers)
- Touch drag nodes (with 200ms long-press or immediate on movement)
- Touch tap = open node panel
- Mobile-friendly panel width (max 90vw)

---

## 14. Data Flow Summary

```
User Action → API Call → Backend processes → Response
                                              ↓
                              Canvas state updated (nodes array)
                                              ↓
                              DOM re-rendered (nodes/edges/groups)
```

In React version, this becomes:
```
User Action → API Call → Response → Zustand store updated → React re-renders affected components
```

No more manual DOM manipulation or full-page reloads.