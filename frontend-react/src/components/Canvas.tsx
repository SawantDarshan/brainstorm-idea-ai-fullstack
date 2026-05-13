import { useEffect, useCallback } from 'react';
import ReactFlow, { Background, Controls, MiniMap, NodeDragHandler } from 'reactflow';
import 'reactflow/dist/style.css';
import { useCanvasStore } from '../stores/canvasStore';
import KnowledgeNode from './KnowledgeNode';

const nodeTypes = {
  knowledge: KnowledgeNode,
  conversation: KnowledgeNode, // Same visual, could differentiate later
};

export default function Canvas() {
  const { rfNodes, rfEdges, onNodesChange, onEdgesChange, loadNodes, updatePosition, selectNode } = useCanvasStore();

  useEffect(() => { loadNodes(); }, [loadNodes]);

  const onNodeDragStop: NodeDragHandler = useCallback((_event, node) => {
    updatePosition(node.id, node.position.x, node.position.y);
  }, [updatePosition]);

  const onPaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeDragStop={onNodeDragStop}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.2}
        maxZoom={3}
        defaultEdgeOptions={{ type: 'smoothstep' }}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="rgba(255,255,255,0.03)" gap={28} size={1} />
        <Controls position="bottom-right" />
        <MiniMap
          position="bottom-right"
          style={{ marginBottom: 60 }}
          nodeColor="#f0a030"
          maskColor="rgba(0,0,0,0.7)"
        />
      </ReactFlow>
    </div>
  );
}