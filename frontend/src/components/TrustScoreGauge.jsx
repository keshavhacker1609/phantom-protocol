import { useEffect, useRef } from "react";
import * as d3 from "d3";

export default function TrustScoreGauge({ score = 0.97, label = "Deception Rate" }) {
  const svgRef = useRef(null);

  useEffect(() => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const w = 120, h = 70;
    const cx = w / 2, cy = h - 10;
    const r = 50;

    const arc = d3.arc()
      .innerRadius(r - 12)
      .outerRadius(r)
      .startAngle(-Math.PI / 2)
      .endAngle(Math.PI / 2);

    const valueArc = d3.arc()
      .innerRadius(r - 12)
      .outerRadius(r)
      .startAngle(-Math.PI / 2)
      .endAngle(-Math.PI / 2 + Math.PI * score);

    const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);

    g.append("path")
      .datum({})
      .attr("d", arc)
      .attr("fill", "#1a2332");

    const color = score > 0.85 ? "#22c55e" : score > 0.7 ? "#eab308" : "#ef4444";

    g.append("path")
      .datum({})
      .attr("d", valueArc)
      .attr("fill", color)
      .attr("filter", "drop-shadow(0 0 6px " + color + ")");

    g.append("text")
      .attr("y", -8)
      .attr("text-anchor", "middle")
      .attr("fill", color)
      .attr("font-size", "16px")
      .attr("font-weight", "bold")
      .attr("font-family", "monospace")
      .text(`${(score * 100).toFixed(1)}%`);

    g.append("text")
      .attr("y", 6)
      .attr("text-anchor", "middle")
      .attr("fill", "#6b7280")
      .attr("font-size", "8px")
      .attr("font-family", "monospace")
      .text(label.toUpperCase());
  }, [score, label]);

  return (
    <svg ref={svgRef} width={120} height={70} />
  );
}
