// ═══════════════════════════════════════════════════════════════
// Draw.io-style Drawing Engine
// ═══════════════════════════════════════════════════════════════

(function () {
  'use strict';

  // ── State ──
  let currentTool = 'select';
  let drawingShapes = JSON.parse(localStorage.getItem('drawShapes') || '[]');
  let drawingConnectors = JSON.parse(localStorage.getItem('drawConnectors') || '[]');
  let selectedShapes = new Set();
  let undoStack = [];
  let redoStack = [];
  let shapeIdCounter = parseInt(localStorage.getItem('drawShapeId') || '1');
  let connectorIdCounter = parseInt(localStorage.getItem('drawConnId') || '1');

  // Drawing state
  let isDrawing = false;
  let drawStart = null;
  let drawCurrent = null;
  let activeShape = null; // shape being created
  let dragState = null;
  let resizeState = null;
  let rubberBand = null;
  let lineDrawState = null;
  let freehandPoints = [];
  let textEditEl = null;

  // ── DOM Setup ──
  const canvas = document.getElementById('canvas');
  const transformLayer = document.getElementById('transform-layer');

  // Create drawing SVG layer
  const drawSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  drawSvg.id = 'draw-svg';
  drawSvg.classList.add('draw-svg');
  drawSvg.style.position = 'absolute';
  drawSvg.style.left = '-10000px';
  drawSvg.style.top = '-10000px';
  drawSvg.setAttribute('width', '20000');
  drawSvg.setAttribute('height', '20000');
  drawSvg.style.pointerEvents = 'none';
  drawSvg.style.overflow = 'visible';
  drawSvg.style.zIndex = '0';
  transformLayer.insertBefore(drawSvg, document.getElementById('connectors-svg'));

  // Selection overlay SVG (for handles)
  const selSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  selSvg.id = 'sel-svg';
  selSvg.classList.add('draw-svg');
  selSvg.style.position = 'absolute';
  selSvg.style.left = '-10000px';
  selSvg.style.top = '-10000px';
  selSvg.setAttribute('width', '20000');
  selSvg.setAttribute('height', '20000');
  selSvg.style.pointerEvents = 'none';
  selSvg.style.overflow = 'visible';
  selSvg.style.zIndex = '0';
  transformLayer.insertBefore(selSvg, document.getElementById('connectors-svg'));

  // ── Toolbar ──
  const toolbar = document.createElement('div');
  toolbar.className = 'draw-toolbar';
  toolbar.innerHTML = `
    <button data-tool="select" class="draw-tool-btn draw-tool-btn--active" title="Select (V)">⊹</button>
    <button data-tool="rect" class="draw-tool-btn" title="Rectangle (R)">▭</button>
    <button data-tool="ellipse" class="draw-tool-btn" title="Ellipse (E)">◯</button>
    <button data-tool="diamond" class="draw-tool-btn" title="Diamond (D)">◇</button>
    <button data-tool="triangle" class="draw-tool-btn" title="Triangle (T)">△</button>
    <button data-tool="cylinder" class="draw-tool-btn" title="Cylinder (C)">⊖</button>
    <button data-tool="line" class="draw-tool-btn" title="Line (L)">╱</button>
    <button data-tool="arrow" class="draw-tool-btn" title="Arrow (A)">→</button>
    <button data-tool="pencil" class="draw-tool-btn" title="Pencil (P)">✎</button>
    <button data-tool="text" class="draw-tool-btn" title="Text (X)">T</button>
    <div class="draw-tool-sep"></div>
    <button id="draw-undo" class="draw-tool-btn" title="Undo (Ctrl+Z)">↶</button>
    <button id="draw-redo" class="draw-tool-btn" title="Redo (Ctrl+Y)">↷</button>
    <button id="draw-delete" class="draw-tool-btn" title="Delete (Del)">🗑</button>
    <button id="draw-export" class="draw-tool-btn" title="Export PNG">⤓</button>
    <div class="draw-tool-sep"></div>
    <label class="draw-color-label" title="Fill">
      <input type="color" id="draw-fill" value="#4fc3f7" />
      <span>Fill</span>
    </label>
    <label class="draw-color-label" title="Stroke">
      <input type="color" id="draw-stroke" value="#ffffff" />
      <span>Line</span>
    </label>
    <select id="draw-stroke-width" class="draw-select" title="Stroke width">
      <option value="1">1px</option>
      <option value="2" selected>2px</option>
      <option value="3">3px</option>
      <option value="4">4px</option>
      <option value="6">6px</option>
    </select>
    <select id="draw-line-style" class="draw-select" title="Line style">
      <option value="solid">Solid</option>
      <option value="dashed">Dashed</option>
      <option value="dotted">Dotted</option>
    </select>
    <select id="draw-font-size" class="draw-select" title="Font size">
      <option value="12">12px</option>
      <option value="14" selected>14px</option>
      <option value="16">16px</option>
      <option value="20">20px</option>
      <option value="24">24px</option>
      <option value="32">32px</option>
      <option value="48">48px</option>
    </select>
  `;
  document.body.appendChild(toolbar);

  // Tool selection
  toolbar.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-tool]');
    if (!btn) return;
    setTool(btn.dataset.tool);
  });

  function setTool(tool) {
    currentTool = tool;
    toolbar.querySelectorAll('[data-tool]').forEach(b => b.classList.toggle('draw-tool-btn--active', b.dataset.tool === tool));
    drawSvg.style.pointerEvents = (tool === 'select') ? 'none' : 'all';
    canvas.style.cursor = tool === 'select' ? '' : 'crosshair';
    if (tool !== 'select') clearSelection();
  }

  // Keyboard shortcuts — only active when a drawing tool is selected or shapes are selected
  document.addEventListener('keydown', (e) => {
    if (e.target.closest('textarea, input, [contenteditable]')) return;
    const key = e.key.toLowerCase();
    // Tool switching shortcuts always work
    const toolMap = { v: 'select', r: 'rect', e: 'ellipse', d: 'diamond', t: 'triangle', c: 'cylinder', l: 'line', a: 'arrow', p: 'pencil', x: 'text' };
    if (toolMap[key] && !e.ctrlKey && !e.altKey && !e.shiftKey) { setTool(toolMap[key]); return; }
    // Only handle edit shortcuts when draw shapes are selected or a draw tool is active
    if (currentTool === 'select' && selectedShapes.size === 0) return;
    if (e.ctrlKey && key === 'z') { e.preventDefault(); undo(); return; }
    if (e.ctrlKey && key === 'y') { e.preventDefault(); redo(); return; }
    if (key === 'delete' || key === 'backspace') { if (selectedShapes.size > 0) deleteSelected(); return; }
    if (e.ctrlKey && key === 'a') { e.preventDefault(); selectAll(); return; }
    if (e.ctrlKey && key === 'c') { copySelected(); return; }
    if (e.ctrlKey && key === 'v') { pasteClipboard(); return; }
  });

  // Button actions
  document.getElementById('draw-undo').addEventListener('click', undo);
  document.getElementById('draw-redo').addEventListener('click', redo);
  document.getElementById('draw-delete').addEventListener('click', deleteSelected);
  document.getElementById('draw-export').addEventListener('click', exportPNG);

  // ── Properties ──
  function getProps() {
    return {
      fill: document.getElementById('draw-fill').value,
      stroke: document.getElementById('draw-stroke').value,
      strokeWidth: parseInt(document.getElementById('draw-stroke-width').value),
      lineStyle: document.getElementById('draw-line-style').value,
      fontSize: parseInt(document.getElementById('draw-font-size').value),
    };
  }

  function getDashArray(style, width) {
    if (style === 'dashed') return `${width * 4} ${width * 2}`;
    if (style === 'dotted') return `${width} ${width * 2}`;
    return '';
  }

  // ── World coordinates ──
  function screenToWorld2(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: (clientX - rect.left - panX) / zoom,
      y: (clientY - rect.top - panY) / zoom,
    };
  }

  // ── Save / Load ──
  function save() {
    localStorage.setItem('drawShapes', JSON.stringify(drawingShapes));
    localStorage.setItem('drawConnectors', JSON.stringify(drawingConnectors));
    localStorage.setItem('drawShapeId', shapeIdCounter);
    localStorage.setItem('drawConnId', connectorIdCounter);
  }

  function pushUndo() {
    undoStack.push({ shapes: JSON.stringify(drawingShapes), connectors: JSON.stringify(drawingConnectors) });
    if (undoStack.length > 50) undoStack.shift();
    redoStack = [];
  }

  function undo() {
    if (!undoStack.length) return;
    redoStack.push({ shapes: JSON.stringify(drawingShapes), connectors: JSON.stringify(drawingConnectors) });
    const state = undoStack.pop();
    drawingShapes = JSON.parse(state.shapes);
    drawingConnectors = JSON.parse(state.connectors);
    save();
    renderAll();
  }

  function redo() {
    if (!redoStack.length) return;
    undoStack.push({ shapes: JSON.stringify(drawingShapes), connectors: JSON.stringify(drawingConnectors) });
    const state = redoStack.pop();
    drawingShapes = JSON.parse(state.shapes);
    drawingConnectors = JSON.parse(state.connectors);
    save();
    renderAll();
  }

  // ── Render ──
  function renderAll() {
    drawSvg.innerHTML = '';
    drawingShapes.forEach(s => renderShape(s));
    drawingConnectors.forEach(c => renderConnector(c));
    renderSelection();
  }

  function renderShape(s) {
    let el;
    const dash = getDashArray(s.lineStyle, s.strokeWidth);

    switch (s.type) {
      case 'rect':
        el = svgEl('rect', { x: s.x, y: s.y, width: s.w, height: s.h, fill: s.fill, stroke: s.stroke, 'stroke-width': s.strokeWidth, rx: 4 });
        if (dash) el.setAttribute('stroke-dasharray', dash);
        break;
      case 'ellipse':
        el = svgEl('ellipse', { cx: s.x + s.w / 2, cy: s.y + s.h / 2, rx: s.w / 2, ry: s.h / 2, fill: s.fill, stroke: s.stroke, 'stroke-width': s.strokeWidth });
        if (dash) el.setAttribute('stroke-dasharray', dash);
        break;
      case 'diamond': {
        const cx = s.x + s.w / 2, cy = s.y + s.h / 2;
        const pts = `${cx},${s.y} ${s.x + s.w},${cy} ${cx},${s.y + s.h} ${s.x},${cy}`;
        el = svgEl('polygon', { points: pts, fill: s.fill, stroke: s.stroke, 'stroke-width': s.strokeWidth });
        if (dash) el.setAttribute('stroke-dasharray', dash);
        break;
      }
      case 'triangle': {
        const pts = `${s.x + s.w / 2},${s.y} ${s.x + s.w},${s.y + s.h} ${s.x},${s.y + s.h}`;
        el = svgEl('polygon', { points: pts, fill: s.fill, stroke: s.stroke, 'stroke-width': s.strokeWidth });
        if (dash) el.setAttribute('stroke-dasharray', dash);
        break;
      }
      case 'cylinder': {
        const ry = Math.min(s.h * 0.15, 20);
        const g = svgEl('g');
        const body = svgEl('path', {
          d: `M ${s.x} ${s.y + ry} L ${s.x} ${s.y + s.h - ry} A ${s.w / 2} ${ry} 0 0 0 ${s.x + s.w} ${s.y + s.h - ry} L ${s.x + s.w} ${s.y + ry}`,
          fill: s.fill, stroke: s.stroke, 'stroke-width': s.strokeWidth
        });
        const topEll = svgEl('ellipse', { cx: s.x + s.w / 2, cy: s.y + ry, rx: s.w / 2, ry: ry, fill: s.fill, stroke: s.stroke, 'stroke-width': s.strokeWidth });
        const botArc = svgEl('path', {
          d: `M ${s.x} ${s.y + s.h - ry} A ${s.w / 2} ${ry} 0 0 0 ${s.x + s.w} ${s.y + s.h - ry}`,
          fill: 'none', stroke: s.stroke, 'stroke-width': s.strokeWidth
        });
        g.appendChild(body);
        g.appendChild(botArc);
        g.appendChild(topEll);
        if (dash) { body.setAttribute('stroke-dasharray', dash); topEll.setAttribute('stroke-dasharray', dash); botArc.setAttribute('stroke-dasharray', dash); }
        el = g;
        break;
      }
      case 'pencil': {
        el = svgEl('path', { d: s.path, fill: 'none', stroke: s.stroke, 'stroke-width': s.strokeWidth, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
        if (dash) el.setAttribute('stroke-dasharray', dash);
        break;
      }
      case 'text': {
        el = svgEl('text', { x: s.x, y: s.y + (s.fontSize || 14), fill: s.stroke, 'font-size': s.fontSize || 14, 'font-family': 'Outfit, sans-serif' });
        el.textContent = s.text || '';
        break;
      }
      default: return;
    }

    if (el) {
      el.dataset.shapeId = s.id;
      el.style.pointerEvents = 'all';
      el.style.cursor = currentTool === 'select' ? 'move' : 'crosshair';
      drawSvg.appendChild(el);
    }

    // Text label on shapes (except text and pencil)
    if (s.text && s.type !== 'text' && s.type !== 'pencil') {
      const txt = svgEl('text', {
        x: s.x + s.w / 2, y: s.y + s.h / 2 + (s.fontSize || 14) / 3,
        fill: s.stroke, 'font-size': s.fontSize || 14, 'text-anchor': 'middle', 'font-family': 'Outfit, sans-serif'
      });
      txt.textContent = s.text;
      txt.style.pointerEvents = 'none';
      drawSvg.appendChild(txt);
    }
  }

  function renderConnector(c) {
    const g = svgEl('g');
    const dash = getDashArray(c.lineStyle, c.strokeWidth);
    const path = svgEl('path', {
      d: `M ${c.x1} ${c.y1} L ${c.x2} ${c.y2}`,
      fill: 'none', stroke: c.stroke, 'stroke-width': c.strokeWidth
    });
    if (dash) path.setAttribute('stroke-dasharray', dash);
    g.appendChild(path);

    if (c.arrow) {
      const angle = Math.atan2(c.y2 - c.y1, c.x2 - c.x1);
      const size = 10 + c.strokeWidth;
      const ax = c.x2 - size * Math.cos(angle - 0.4);
      const ay = c.y2 - size * Math.sin(angle - 0.4);
      const bx = c.x2 - size * Math.cos(angle + 0.4);
      const by = c.y2 - size * Math.sin(angle + 0.4);
      const arrow = svgEl('polygon', { points: `${c.x2},${c.y2} ${ax},${ay} ${bx},${by}`, fill: c.stroke });
      g.appendChild(arrow);
    }

    g.dataset.connId = c.id;
    g.style.pointerEvents = 'all';
    g.style.cursor = currentTool === 'select' ? 'pointer' : 'crosshair';
    drawSvg.appendChild(g);
  }

  function renderSelection() {
    selSvg.innerHTML = '';
    selectedShapes.forEach(id => {
      const s = drawingShapes.find(sh => sh.id === id);
      if (!s) return;
      const bounds = getShapeBounds(s);
      if (!bounds) return;
      // Selection rectangle
      const r = svgEl('rect', { x: bounds.x - 4, y: bounds.y - 4, width: bounds.w + 8, height: bounds.h + 8, fill: 'none', stroke: '#4fc3f7', 'stroke-width': 1.5, 'stroke-dasharray': '4 2' });
      selSvg.appendChild(r);
      // Resize handles
      const handles = getHandlePositions(bounds);
      handles.forEach((h, i) => {
        const handle = svgEl('rect', { x: h.x - 4, y: h.y - 4, width: 8, height: 8, fill: '#fff', stroke: '#4fc3f7', 'stroke-width': 1.5, rx: 1 });
        handle.style.pointerEvents = 'all';
        handle.style.cursor = getHandleCursor(i);
        handle.dataset.handleIdx = i;
        handle.dataset.shapeId = id;
        selSvg.appendChild(handle);
      });
    });
  }

  function getShapeBounds(s) {
    if (s.type === 'pencil') {
      // Parse path to get bounds
      if (!s.path) return null;
      const nums = s.path.match(/-?\d+(\.\d+)?/g);
      if (!nums || nums.length < 2) return null;
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (let i = 0; i < nums.length; i += 2) {
        const px = parseFloat(nums[i]), py = parseFloat(nums[i + 1]);
        minX = Math.min(minX, px); minY = Math.min(minY, py);
        maxX = Math.max(maxX, px); maxY = Math.max(maxY, py);
      }
      return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
    }
    if (s.type === 'text') {
      return { x: s.x, y: s.y, w: (s.text || '').length * (s.fontSize || 14) * 0.6, h: (s.fontSize || 14) * 1.4 };
    }
    return { x: s.x, y: s.y, w: s.w, h: s.h };
  }

  function getHandlePositions(b) {
    return [
      { x: b.x, y: b.y }, { x: b.x + b.w / 2, y: b.y }, { x: b.x + b.w, y: b.y },
      { x: b.x + b.w, y: b.y + b.h / 2 },
      { x: b.x + b.w, y: b.y + b.h }, { x: b.x + b.w / 2, y: b.y + b.h }, { x: b.x, y: b.y + b.h },
      { x: b.x, y: b.y + b.h / 2 },
    ];
  }

  function getHandleCursor(idx) {
    return ['nw-resize', 'n-resize', 'ne-resize', 'e-resize', 'se-resize', 's-resize', 'sw-resize', 'w-resize'][idx];
  }

  // ── SVG Helper ──
  function svgEl(tag, attrs) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    if (attrs) Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
    return el;
  }

  // ── Mouse Handlers on draw layer ──
  drawSvg.addEventListener('mousedown', onDrawMouseDown);
  selSvg.addEventListener('mousedown', onSelMouseDown);
  // Also handle select tool clicks on drawSvg
  drawSvg.addEventListener('mousedown', onSelectClick, true);

  function onSelectClick(e) {
    if (currentTool !== 'select') return;
    const shapeEl = e.target.closest('[data-shape-id]');
    const connEl = e.target.closest('[data-conn-id]');
    if (shapeEl) {
      e.preventDefault(); e.stopPropagation();
      const id = parseInt(shapeEl.dataset.shapeId);
      if (e.shiftKey) {
        if (selectedShapes.has(id)) selectedShapes.delete(id);
        else selectedShapes.add(id);
      } else {
        selectedShapes = new Set([id]);
      }
      renderSelection();
      // Start drag
      const s = drawingShapes.find(sh => sh.id === id);
      if (s) {
        dragState = { startWorld: screenToWorld2(e.clientX, e.clientY), shapes: [...selectedShapes].map(sid => { const sh = drawingShapes.find(x => x.id === sid); return { id: sid, ox: sh.x, oy: sh.y }; }) };
      }
    } else if (connEl) {
      e.preventDefault(); e.stopPropagation();
      // Select connector (for delete)
      const id = parseInt(connEl.dataset.connId);
      selectedShapes = new Set(); // deselect shapes
      // Store connector selection differently - just highlight
      connEl.querySelector('path').setAttribute('stroke', '#ff5252');
      // On delete, remove connector
      const handler = (ev) => {
        if (ev.key === 'Delete' || ev.key === 'Backspace') {
          pushUndo();
          drawingConnectors = drawingConnectors.filter(c => c.id !== id);
          save(); renderAll();
          document.removeEventListener('keydown', handler);
        }
      };
      document.addEventListener('keydown', handler);
    } else {
      // Start rubber band
      if (!e.shiftKey) clearSelection();
      const world = screenToWorld2(e.clientX, e.clientY);
      rubberBand = { x: world.x, y: world.y, active: true };
      e.preventDefault();
    }
  }

  function onSelMouseDown(e) {
    const handle = e.target.closest('[data-handle-idx]');
    if (!handle) return;
    e.preventDefault(); e.stopPropagation();
    const idx = parseInt(handle.dataset.handleIdx);
    const shapeId = parseInt(handle.dataset.shapeId);
    const s = drawingShapes.find(sh => sh.id === shapeId);
    if (!s) return;
    resizeState = { shapeId, idx, ox: s.x, oy: s.y, ow: s.w || 0, oh: s.h || 0, startWorld: screenToWorld2(e.clientX, e.clientY) };
    pushUndo();
  }

  document.addEventListener('mousemove', (e) => {
    // Only handle if a draw operation is in progress
    if (!resizeState && !dragState && !(rubberBand && rubberBand.active) && !isDrawing && !lineDrawState) return;
    if (resizeState) {
      const world = screenToWorld2(e.clientX, e.clientY);
      const dx = world.x - resizeState.startWorld.x;
      const dy = world.y - resizeState.startWorld.y;
      const s = drawingShapes.find(sh => sh.id === resizeState.shapeId);
      if (!s) return;
      const idx = resizeState.idx;
      // Resize logic based on handle index
      let nx = resizeState.ox, ny = resizeState.oy, nw = resizeState.ow, nh = resizeState.oh;
      if (idx === 0) { nx += dx; ny += dy; nw -= dx; nh -= dy; }
      else if (idx === 1) { ny += dy; nh -= dy; }
      else if (idx === 2) { ny += dy; nw += dx; nh -= dy; }
      else if (idx === 3) { nw += dx; }
      else if (idx === 4) { nw += dx; nh += dy; }
      else if (idx === 5) { nh += dy; }
      else if (idx === 6) { nx += dx; nw -= dx; nh += dy; }
      else if (idx === 7) { nx += dx; nw -= dx; }
      if (nw < 10) nw = 10;
      if (nh < 10) nh = 10;
      s.x = nx; s.y = ny; s.w = nw; s.h = nh;
      save(); renderAll();
      return;
    }

    if (dragState) {
      const world = screenToWorld2(e.clientX, e.clientY);
      const dx = world.x - dragState.startWorld.x;
      const dy = world.y - dragState.startWorld.y;
      dragState.shapes.forEach(({ id, ox, oy }) => {
        const s = drawingShapes.find(sh => sh.id === id);
        if (s) { s.x = ox + dx; s.y = oy + dy; }
      });
      save(); renderAll();
      return;
    }

    if (rubberBand && rubberBand.active) {
      const world = screenToWorld2(e.clientX, e.clientY);
      rubberBand.x2 = world.x; rubberBand.y2 = world.y;
      // Draw rubber band rect
      selSvg.innerHTML = '';
      const rx = Math.min(rubberBand.x, rubberBand.x2);
      const ry = Math.min(rubberBand.y, rubberBand.y2);
      const rw = Math.abs(rubberBand.x2 - rubberBand.x);
      const rh = Math.abs(rubberBand.y2 - rubberBand.y);
      const r = svgEl('rect', { x: rx, y: ry, width: rw, height: rh, fill: 'rgba(79,195,247,0.1)', stroke: '#4fc3f7', 'stroke-width': 1, 'stroke-dasharray': '4 2' });
      selSvg.appendChild(r);
      return;
    }

    if (isDrawing && currentTool === 'pencil') {
      const world = screenToWorld2(e.clientX, e.clientY);
      freehandPoints.push(world);
      // Update preview
      const existing = drawSvg.querySelector('.draw-preview');
      if (existing) existing.remove();
      const path = svgEl('path', { d: pointsToPath(freehandPoints), fill: 'none', stroke: getProps().stroke, 'stroke-width': getProps().strokeWidth, 'stroke-linecap': 'round' });
      path.classList.add('draw-preview');
      drawSvg.appendChild(path);
      return;
    }

    if (isDrawing && drawStart) {
      drawCurrent = screenToWorld2(e.clientX, e.clientY);
      // Update preview
      const existing = drawSvg.querySelector('.draw-preview');
      if (existing) existing.remove();
      renderPreview();
    }

    if (lineDrawState) {
      const world = screenToWorld2(e.clientX, e.clientY);
      const existing = drawSvg.querySelector('.draw-preview');
      if (existing) existing.remove();
      const line = svgEl('line', { x1: lineDrawState.x1, y1: lineDrawState.y1, x2: world.x, y2: world.y, stroke: getProps().stroke, 'stroke-width': getProps().strokeWidth });
      line.classList.add('draw-preview');
      drawSvg.appendChild(line);
    }
  });

  document.addEventListener('mouseup', (e) => {
    // Only handle if a draw operation is in progress
    if (!resizeState && !dragState && !(rubberBand && rubberBand.active) && !isDrawing && !lineDrawState) return;
    if (resizeState) { resizeState = null; save(); renderAll(); return; }

    if (dragState) {
      if (dragState.shapes.some(({ id, ox, oy }) => { const s = drawingShapes.find(sh => sh.id === id); return s && (s.x !== ox || s.y !== oy); })) {
        // Position changed - already saved during drag
      }
      dragState = null;
      renderAll();
      return;
    }

    if (rubberBand && rubberBand.active) {
      rubberBand.active = false;
      if (rubberBand.x2 !== undefined) {
        const rx = Math.min(rubberBand.x, rubberBand.x2);
        const ry = Math.min(rubberBand.y, rubberBand.y2);
        const rw = Math.abs(rubberBand.x2 - rubberBand.x);
        const rh = Math.abs(rubberBand.y2 - rubberBand.y);
        // Select shapes within rubber band
        drawingShapes.forEach(s => {
          const b = getShapeBounds(s);
          if (b && b.x >= rx && b.y >= ry && b.x + b.w <= rx + rw && b.y + b.h <= ry + rh) {
            selectedShapes.add(s.id);
          }
        });
      }
      rubberBand = null;
      renderSelection();
      return;
    }

    if (lineDrawState) {
      const world = screenToWorld2(e.clientX, e.clientY);
      const dist = Math.hypot(world.x - lineDrawState.x1, world.y - lineDrawState.y1);
      if (dist > 5) {
        pushUndo();
        const props = getProps();
        drawingConnectors.push({
          id: connectorIdCounter++,
          x1: lineDrawState.x1, y1: lineDrawState.y1, x2: world.x, y2: world.y,
          stroke: props.stroke, strokeWidth: props.strokeWidth, lineStyle: props.lineStyle,
          arrow: currentTool === 'arrow'
        });
        save();
      }
      lineDrawState = null;
      drawSvg.querySelector('.draw-preview')?.remove();
      renderAll();
      return;
    }

    if (isDrawing && currentTool === 'pencil') {
      isDrawing = false;
      drawSvg.querySelector('.draw-preview')?.remove();
      if (freehandPoints.length > 2) {
        pushUndo();
        const props = getProps();
        drawingShapes.push({
          id: shapeIdCounter++, type: 'pencil',
          path: pointsToPath(freehandPoints),
          stroke: props.stroke, strokeWidth: props.strokeWidth, lineStyle: props.lineStyle,
          x: 0, y: 0
        });
        save();
      }
      freehandPoints = [];
      renderAll();
      return;
    }

    if (isDrawing && drawStart && drawCurrent) {
      isDrawing = false;
      drawSvg.querySelector('.draw-preview')?.remove();
      const x = Math.min(drawStart.x, drawCurrent.x);
      const y = Math.min(drawStart.y, drawCurrent.y);
      const w = Math.abs(drawCurrent.x - drawStart.x);
      const h = Math.abs(drawCurrent.y - drawStart.y);
      if (w > 5 || h > 5) {
        pushUndo();
        const props = getProps();
        drawingShapes.push({
          id: shapeIdCounter++, type: currentTool,
          x, y, w, h,
          fill: props.fill, stroke: props.stroke, strokeWidth: props.strokeWidth,
          lineStyle: props.lineStyle, fontSize: props.fontSize, text: ''
        });
        save();
      }
      drawStart = null; drawCurrent = null;
      renderAll();
    }
  });

  function onDrawMouseDown(e) {
    if (currentTool === 'select') return;
    if (e.button !== 0) return;
    e.preventDefault(); e.stopPropagation();

    const world = screenToWorld2(e.clientX, e.clientY);

    if (currentTool === 'line' || currentTool === 'arrow') {
      lineDrawState = { x1: world.x, y1: world.y };
      return;
    }

    if (currentTool === 'pencil') {
      isDrawing = true;
      freehandPoints = [world];
      return;
    }

    if (currentTool === 'text') {
      pushUndo();
      const props = getProps();
      const s = {
        id: shapeIdCounter++, type: 'text',
        x: world.x, y: world.y, w: 100, h: props.fontSize * 1.5,
        fill: 'transparent', stroke: props.stroke, strokeWidth: 0,
        lineStyle: 'solid', fontSize: props.fontSize, text: 'Text'
      };
      drawingShapes.push(s);
      save(); renderAll();
      // Start editing immediately
      startTextEdit(s);
      return;
    }

    // Shape drawing
    isDrawing = true;
    drawStart = world;
    drawCurrent = world;
  }

  function renderPreview() {
    if (!drawStart || !drawCurrent) return;
    const props = getProps();
    const x = Math.min(drawStart.x, drawCurrent.x);
    const y = Math.min(drawStart.y, drawCurrent.y);
    const w = Math.abs(drawCurrent.x - drawStart.x);
    const h = Math.abs(drawCurrent.y - drawStart.y);
    let el;
    switch (currentTool) {
      case 'rect':
        el = svgEl('rect', { x, y, width: w, height: h, fill: props.fill + '66', stroke: props.stroke, 'stroke-width': props.strokeWidth, rx: 4 });
        break;
      case 'ellipse':
        el = svgEl('ellipse', { cx: x + w / 2, cy: y + h / 2, rx: w / 2, ry: h / 2, fill: props.fill + '66', stroke: props.stroke, 'stroke-width': props.strokeWidth });
        break;
      case 'diamond': {
        const cx = x + w / 2, cy = y + h / 2;
        el = svgEl('polygon', { points: `${cx},${y} ${x + w},${cy} ${cx},${y + h} ${x},${cy}`, fill: props.fill + '66', stroke: props.stroke, 'stroke-width': props.strokeWidth });
        break;
      }
      case 'triangle':
        el = svgEl('polygon', { points: `${x + w / 2},${y} ${x + w},${y + h} ${x},${y + h}`, fill: props.fill + '66', stroke: props.stroke, 'stroke-width': props.strokeWidth });
        break;
      case 'cylinder':
      default:
        el = svgEl('rect', { x, y, width: w, height: h, fill: props.fill + '66', stroke: props.stroke, 'stroke-width': props.strokeWidth, rx: 4 });
    }
    if (el) { el.classList.add('draw-preview'); drawSvg.appendChild(el); }
  }

  function pointsToPath(pts) {
    if (pts.length < 2) return '';
    let d = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) d += ` L ${pts[i].x} ${pts[i].y}`;
    return d;
  }

  // ── Text Editing ──
  function startTextEdit(s) {
    if (textEditEl) textEditEl.remove();
    const div = document.createElement('div');
    div.contentEditable = 'true';
    div.className = 'draw-text-edit';
    div.style.position = 'absolute';
    div.style.left = `${s.x}px`;
    div.style.top = `${s.y}px`;
    div.style.fontSize = `${s.fontSize || 14}px`;
    div.style.color = s.stroke;
    div.style.minWidth = '50px';
    div.style.outline = '1px solid #4fc3f7';
    div.style.padding = '2px 4px';
    div.style.background = 'rgba(0,0,0,0.7)';
    div.style.zIndex = '9999';
    div.textContent = s.text || '';
    transformLayer.appendChild(div);
    div.focus();
    document.execCommand('selectAll');
    textEditEl = div;

    const finish = () => {
      s.text = div.textContent;
      save(); renderAll();
      div.remove(); textEditEl = null;
    };
    div.addEventListener('blur', finish);
    div.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); finish(); } });
  }

  // Double click to edit text
  drawSvg.addEventListener('dblclick', (e) => {
    const el = e.target.closest('[data-shape-id]');
    if (!el) return;
    const s = drawingShapes.find(sh => sh.id === parseInt(el.dataset.shapeId));
    if (s) startTextEdit(s);
  });

  // ── Selection ──
  function clearSelection() { selectedShapes = new Set(); renderSelection(); }
  function selectAll() { drawingShapes.forEach(s => selectedShapes.add(s.id)); renderSelection(); }

  function deleteSelected() {
    if (!selectedShapes.size) return;
    pushUndo();
    drawingShapes = drawingShapes.filter(s => !selectedShapes.has(s.id));
    selectedShapes = new Set();
    save(); renderAll();
  }

  // ── Copy/Paste ──
  let clipboard = [];
  function copySelected() {
    clipboard = drawingShapes.filter(s => selectedShapes.has(s.id)).map(s => ({ ...s }));
  }
  function pasteClipboard() {
    if (!clipboard.length) return;
    pushUndo();
    clearSelection();
    clipboard.forEach(s => {
      const ns = { ...s, id: shapeIdCounter++, x: (s.x || 0) + 20, y: (s.y || 0) + 20 };
      drawingShapes.push(ns);
      selectedShapes.add(ns.id);
    });
    save(); renderAll();
  }

  // ── Export ──
  function exportPNG() {
    const svgClone = drawSvg.cloneNode(true);
    svgClone.querySelectorAll('.draw-preview').forEach(e => e.remove());
    // Get bounds
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    drawingShapes.forEach(s => {
      const b = getShapeBounds(s);
      if (!b) return;
      minX = Math.min(minX, b.x); minY = Math.min(minY, b.y);
      maxX = Math.max(maxX, b.x + b.w); maxY = Math.max(maxY, b.y + b.h);
    });
    if (minX === Infinity) return;
    const pad = 20;
    const w = maxX - minX + pad * 2, h = maxY - minY + pad * 2;
    svgClone.setAttribute('viewBox', `${minX - pad} ${minY - pad} ${w} ${h}`);
    svgClone.setAttribute('width', w);
    svgClone.setAttribute('height', h);
    const svgData = new XMLSerializer().serializeToString(svgClone);
    const img = new Image();
    img.onload = () => {
      const cvs = document.createElement('canvas');
      cvs.width = w * 2; cvs.height = h * 2;
      const ctx = cvs.getContext('2d');
      ctx.scale(2, 2);
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(0, 0, w, h);
      ctx.drawImage(img, 0, 0, w, h);
      const a = document.createElement('a');
      a.download = 'canvas-export.png';
      a.href = cvs.toDataURL('image/png');
      a.click();
    };
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  }

  // ── Initial Render ──
  renderAll();

  // Make drawSvg pointer events dynamic based on tool
  const origSetTool = setTool;

  // Expose for debugging
  window._drawState = { drawingShapes, drawingConnectors };
})();