import { useEffect, useRef } from "react";
import * as d3 from "d3";

const NODES = [
  { id: "self", label: "THIS NODE", x: 400, y: 250, r: 12, color: "#06b6d4", self: true },
  { id: "us-east", label: "US-EAST", x: 200, y: 150, r: 8, color: "#a855f7" },
  { id: "eu-west", label: "EU-WEST", x: 600, y: 120, r: 8, color: "#a855f7" },
  { id: "apac", label: "APAC", x: 680, y: 320, r: 8, color: "#a855f7" },
  { id: "us-west", label: "US-WEST", x: 100, y: 320, r: 8, color: "#a855f7" },
  { id: "eu-central", label: "EU-CENTRAL", x: 500, y: 400, r: 6, color: "#6b7280" },
];

const LINKS = [
  { source: "self", target: "us-east" },
  { source: "self", target: "eu-west" },
  { source: "self", target: "apac" },
  { source: "self", target: "us-west" },
  { source: "self", target: "eu-central" },
  { source: "us-east", target: "eu-west" },
  { source: "eu-west", target: "apac" },
];

export default function ThreatMap({ attacks = [], meshStatus }) {
  const svgRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth || 760;
    const height = svgRef.current.clientHeight || 280;
    const scaleX = width / 800;
    const scaleY = height / 500;

    const defs = svg.append("defs");

    const glowFilter = defs.append("filter").attr("id", "glow");
    glowFilter.append("feGaussianBlur").attr("stdDeviation", "4").attr("result", "coloredBlur");
    const feMerge = glowFilter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    const linkData = LINKS.map(l => ({
      ...l,
      x1: NODES.find(n => n.id === l.source).x * scaleX,
      y1: NODES.find(n => n.id === l.source).y * scaleY,
      x2: NODES.find(n => n.id === l.target).x * scaleX,
      y2: NODES.find(n => n.id === l.target).y * scaleY,
    }));

    svg.selectAll(".link")
      .data(linkData)
      .enter()
      .append("line")
      .attr("class", "link")
      .attr("x1", d => d.x1)
      .attr("y1", d => d.y1)
      .attr("x2", d => d.x2)
      .attr("y2", d => d.y2)
      .attr("stroke", "#1a2332")
      .attr("stroke-width", 1);

    const threatLinks = svg.selectAll(".threat-link")
      .data(linkData)
      .enter()
      .append("line")
      .attr("class", "threat-link")
      .attr("x1", d => d.x1)
      .attr("y1", d => d.y1)
      .attr("x2", d => d.x2)
      .attr("y2", d => d.y2)
      .attr("stroke", "#ef4444")
      .attr("stroke-width", 2)
      .attr("opacity", 0);

    let tick = 0;
    function animate() {
      tick++;
      threatLinks.each(function(d, i) {
        const phase = (tick / 60 + i * 0.3) % 1;
        const opacity = phase < 0.3 ? phase / 0.3 : phase < 0.7 ? 1 : (1 - phase) / 0.3;
        d3.select(this).attr("opacity", opacity * 0.6);
      });
      animationRef.current = requestAnimationFrame(animate);
    }
    animationRef.current = requestAnimationFrame(animate);

    const nodeGroups = svg.selectAll(".node")
      .data(NODES)
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("transform", d => `translate(${d.x * scaleX}, ${d.y * scaleY})`);

    nodeGroups.append("circle")
      .attr("r", d => d.r * 2.5)
      .attr("fill", d => d.color)
      .attr("opacity", 0.1);

    nodeGroups.append("circle")
      .attr("r", d => d.r)
      .attr("fill", d => d.color)
      .attr("filter", "url(#glow)")
      .attr("class", "node-pulse");

    nodeGroups.append("text")
      .attr("y", d => d.r + 14)
      .attr("text-anchor", "middle")
      .attr("fill", "#94a3b8")
      .attr("font-size", "9px")
      .attr("font-family", "monospace")
      .text(d => d.label);

    if (attacks.length > 0) {
      const recentAttack = attacks[0];
      const targetNode = NODES[Math.floor(Math.random() * (NODES.length - 1)) + 1];
      const selfNode = NODES[0];

      svg.append("circle")
        .attr("cx", targetNode.x * scaleX)
        .attr("cy", targetNode.y * scaleY)
        .attr("r", 20)
        .attr("fill", "none")
        .attr("stroke", "#ef4444")
        .attr("stroke-width", 2)
        .attr("opacity", 1)
        .transition()
        .duration(1500)
        .attr("r", 50)
        .attr("opacity", 0)
        .remove();
    }

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [attacks.length]);

  return (
    <div className="panel flex flex-col h-full">
      <div className="panel-header flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-xs font-semibold text-phantom-text uppercase tracking-wider">Global Threat Mesh</span>
        </div>
        <div className="flex items-center gap-3 text-xs text-phantom-text-dim">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyan-500" /> Self
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-purple-500" /> Peers
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500" /> Threat Flow
          </span>
        </div>
      </div>
      <div className="flex-1 relative bg-grid">
        <svg
          ref={svgRef}
          className="w-full h-full"
          style={{ minHeight: "200px" }}
        />
        <div className="absolute bottom-2 left-3 text-xs text-phantom-text-dim">
          {meshStatus?.connected_nodes || 4} nodes connected • Intel sharing ACTIVE
        </div>
      </div>
    </div>
  );
}
