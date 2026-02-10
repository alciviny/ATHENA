
import React, { useEffect, useState, useRef, useCallback, memo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { forceCollide } from 'd3-force';
import { studyService } from '../services/studyService';
import type { KnowledgeNode, RoiReport } from '../types/athena';

interface TooltipData {
  node: KnowledgeNode;
  x: number;
  y: number;
}

interface KnowledgeGraphProps {
  onNodeClick: (node: KnowledgeNode) => void;
}

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ onNodeClick }) => {
  const [graphData, setGraphData] = useState<RoiReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const fgRef = useRef<any>(null);

  useEffect(() => {
    studyService.getRoiReport()
      .then((data: RoiReport) => {
        // Ensure nodes have a default weight if not provided
        const sanitizedNodes = data.nodes.map(node => ({
          ...node,
          weight: node.weight ?? 1, 
        }));
        setGraphData({ ...data, nodes: sanitizedNodes });
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching ROI report:", error);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (graphData && fgRef.current) {
      const fg = fgRef.current;
      // Adjust collision force to prevent node overlap
      fg.d3Force('collide', forceCollide<any>(node => {
        const kNode = node as KnowledgeNode;
        // Use weight for collision radius
        return (kNode.weight || 1) * 1.5 + 5; 
      }));
    }
  }, [graphData]);

  const getNodeColor = (roi: number) => {
    if (roi > 0.7) return 'rgba(255, 99, 71, 1)';   // Tomato/Red for high ROI
    if (roi < 0.3) return 'rgba(60, 179, 113, 1)'; // MediumSeaGreen/Emerald for consolidated
    
    // Linear interpolation for colors between 0.3 and 0.7
    const r = 60 + (255 - 60) * ((roi - 0.3) / 0.4);
    const g = 179 + (99 - 179) * ((roi - 0.3) / 0.4);
    const b = 113 + (71 - 113) * ((roi - 0.3) / 0.4);
    return `rgba(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)}, 1)`;
  };
  
  const handleNodeHover = useCallback((node: any | null) => {
    if (node && node.x && node.y) {
      const screenCoords = fgRef.current?.graph2ScreenCoords(node.x, node.y);
      if (screenCoords) {
        setTooltip({
          node: node as KnowledgeNode,
          x: screenCoords.x,
          y: screenCoords.y
        });
      }
    } else {
      setTooltip(null);
    }
  }, []);

  const renderNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const kNode = node as KnowledgeNode;
    // Node size proportional to weight 
    const radius = 5 * (kNode.weight || 1);
    const color = getNodeColor(kNode.roi_score);

    // --- Glow effect based on stability ---
    // Lower stability = more glow
    const glowOpacity = Math.max(0, 1 - kNode.stability);
    if (glowOpacity > 0.1) {
      ctx.shadowBlur = 20 * glowOpacity;
      ctx.shadowColor = color.replace('1)', `${glowOpacity})`);
    } else {
      ctx.shadowBlur = 0;
    }
    
    // --- Pulsing effect for high ROI nodes ---
    if (kNode.roi_score > 0.7) {
      const pulseRadius = radius + (Math.sin(Date.now() / 300) * 2 + 2);
      ctx.beginPath();
      ctx.arc(kNode.x!, kNode.y!, pulseRadius, 0, 2 * Math.PI, false);
      ctx.fillStyle = color.replace('1)', '0.2)'); // Use node color with low opacity
      ctx.fill();
    }

    // --- Main Node Circle ---
    ctx.beginPath();
    ctx.arc(kNode.x!, kNode.y!, radius, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();

    // Reset shadow for other elements
    ctx.shadowBlur = 0;

    // --- Node Label (only drawn when zoomed in) ---
    const label = kNode.name;
    if (globalScale > 1.2) {
      const fontSize = 12 / globalScale;
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.fillText(label, kNode.x!, kNode.y!);
    }
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-[600px]"><span className="text-slate-400 font-mono">Loading Knowledge Graph...</span></div>;
  }

  if (!graphData) {
    return <div className="flex items-center justify-center h-[600px]"><span className="text-slate-400 font-mono">Could not load graph data.</span></div>;
  }

  return (
    <div className="relative w-full h-[600px] bg-slate-950 rounded-lg border border-slate-800">
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeCanvasObject={renderNode}
        onNodeHover={handleNodeHover}
        onNodeClick={(node) => onNodeClick(node as KnowledgeNode)}
        linkColor={() => 'rgba(100, 116, 139, 0.3)'}
        linkWidth={1}
        backgroundColor="rgba(0, 0, 0, 0)"
        cooldownTicks={100}
        d3VelocityDecay={0.3} // Adjusted as requested
        onEngineStop={() => fgRef.current?.zoomToFit(400, 100)}
      />
      {tooltip && (
         <div 
         className="absolute p-3 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300 font-mono z-20 pointer-events-none transition-opacity"
         style={{ 
           left: tooltip.x, 
           top: tooltip.y,
           transform: 'translate(-50%, -120%)' // Position tooltip above the node
          }}
       >
         <h4 className="font-bold text-emerald-400 mb-1">{tooltip.node.name}</h4>
         <div><span className="font-semibold">ROI Score:</span> {tooltip.node.roi_score.toFixed(2)}</div>
         <div><span className="font-semibold">Recommendation:</span> {tooltip.node.status || 'N/A'}</div>
         <div><span className="font-semibold">Difficulty:</span> {tooltip.node.difficulty.toFixed(1)}</div>
         <div><span className="font-semibold">Stability:</span> {tooltip.node.stability.toFixed(2)}</div>
       </div>
      )}
    </div>
  );
};

const KnowledgeGraphMemoized = memo(KnowledgeGraph);
export default KnowledgeGraphMemoized;
