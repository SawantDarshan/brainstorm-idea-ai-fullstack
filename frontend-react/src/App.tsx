import Canvas from './components/Canvas';
import Toolbar from './components/Toolbar';
import AgentPanel from './components/AgentPanel';
import NodePanel from './components/NodePanel';

export default function App() {
  return (
    <div className="h-screen w-screen overflow-hidden bg-[#0a0a0f]">
      <Toolbar />
      <div className="pt-[52px] h-full">
        <Canvas />
      </div>
      <AgentPanel />
      <NodePanel />
    </div>
  );
}