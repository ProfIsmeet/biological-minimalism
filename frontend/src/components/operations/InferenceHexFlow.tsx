"use client";

import { deriveHexFlow, type HexEdge, type HexEdgeState, type HexNode, type HexNodeId, type HexNodeState } from "@/lib/monitoring/inferenceHexFlow";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

type Positions = Record<HexNodeId, { x: number; y: number }>;

// Wide horizontal flow — unchanged shape, just given more breathing room per
// node so the enlarged §14/§20 labels (>=10px) do not crowd the hexagons.
const DESKTOP_POS: Positions = {
  source: { x: 44, y: 100 },
  ppgInput: { x: 124, y: 50 },
  imuInput: { x: 124, y: 150 },
  window: { x: 208, y: 100 },
  model: { x: 288, y: 100 },
  output: { x: 366, y: 100 },
};
const DESKTOP_VIEWBOX = "0 0 404 200";
const DESKTOP_HEX_R = 27;

// §14 — the previous single SVG forced `min-width: 360px` inside an
// `overflow-x-auto` wrapper, which clipped the final `output` hexagon at the
// 390px mobile viewport (the wrapper's own horizontal scrollbar was the
// visible symptom). Below `sm` we swap to a purpose-built TALLER vertical
// layout — source at top, PPG/IMU fork side by side, then window/model/output
// stacked below — so all six nodes fit with no horizontal scroll at all.
const MOBILE_POS: Positions = {
  source: { x: 150, y: 40 },
  ppgInput: { x: 76, y: 132 },
  imuInput: { x: 224, y: 132 },
  window: { x: 150, y: 224 },
  model: { x: 150, y: 316 },
  output: { x: 150, y: 408 },
};
const MOBILE_VIEWBOX = "0 0 300 444";
const MOBILE_HEX_R = 30;

const NODE_STYLE: Record<HexNodeState, { fill: string; stroke: string; dash?: string; text: string }> = {
  confirmed: { fill: "rgba(69,214,229,0.12)", stroke: "#45D6E5", text: "#DCF6FA" },
  awaiting: { fill: "rgba(213,164,94,0.1)", stroke: "#D5A45E", dash: "4 3", text: "#F3E2C6" },
  blocked: { fill: "rgba(81,98,105,0.12)", stroke: "#516269", dash: "3 4", text: "#9DB0B6" },
  fault: { fill: "rgba(212,111,112,0.14)", stroke: "#D46F70", dash: "6 4", text: "#F6D8D8" },
  unavailable: { fill: "rgba(81,98,105,0.1)", stroke: "#516269", dash: "2 4", text: "#9DB0B6" },
  disconnected: { fill: "transparent", stroke: "#516269", text: "#758990" },
  source_error: { fill: "rgba(212,111,112,0.1)", stroke: "#D46F70", dash: "2 4", text: "#C98F8F" },
};

const EDGE_STYLE: Record<HexEdgeState, { stroke: string; dash?: string; opacity: number }> = {
  active: { stroke: "#45D6E5", opacity: 0.85 },
  broken: { stroke: "#D46F70", dash: "5 4", opacity: 0.9 },
  idle: { stroke: "#2a3b42", opacity: 0.7 },
};

const STATE_WORD: Record<HexNodeState, string> = {
  confirmed: "confirmed",
  awaiting: "awaiting",
  blocked: "blocked",
  fault: "simulated fault",
  unavailable: "unavailable",
  disconnected: "disconnected",
  source_error: "source error",
};

function hexPoints(cx: number, cy: number, r: number): string {
  const pts: string[] = [];
  for (let i = 0; i < 6; i++) {
    const a = (Math.PI / 180) * (60 * i);
    pts.push(`${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a)).toFixed(2)}`);
  }
  return pts.join(" ");
}

/** Trim a line's endpoint back by `r` so the arrowhead sits at the hex edge, not buried under it. */
function trimmedLine(a: { x: number; y: number }, b: { x: number; y: number }, r: number) {
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const len = Math.hypot(dx, dy) || 1;
  const ux = dx / len;
  const uy = dy / len;
  return { x1: a.x + ux * r, y1: a.y + uy * r, x2: b.x - ux * (r + 1), y2: b.y - uy * (r + 1) };
}

function HexFlowSvg({
  idPrefix,
  positions,
  viewBox,
  hexR,
  nodes,
  edges,
  primaryFontSize,
  secondaryFontSize,
  className,
}: {
  idPrefix: string;
  positions: Positions;
  viewBox: string;
  hexR: number;
  nodes: HexNode[];
  edges: HexEdge[];
  primaryFontSize: number;
  secondaryFontSize: number;
  className: string;
}) {
  const edgeStates: HexEdgeState[] = ["active", "broken", "idle"];
  return (
    <svg viewBox={viewBox} className={className} aria-hidden="true">
      <defs>
        {edgeStates.map((state) => (
          <marker
            key={state}
            id={`${idPrefix}-arrow-${state}`}
            viewBox="0 0 10 10"
            refX="8.5"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M0,0 L10,5 L0,10 z" fill={EDGE_STYLE[state].stroke} opacity={EDGE_STYLE[state].opacity} />
          </marker>
        ))}
      </defs>
      {edges.map((e) => {
        const a = positions[e.from];
        const b = positions[e.to];
        const st = EDGE_STYLE[e.state];
        const line = trimmedLine(a, b, hexR);
        return (
          <line
            key={e.id}
            x1={line.x1}
            y1={line.y1}
            x2={line.x2}
            y2={line.y2}
            stroke={st.stroke}
            strokeWidth={2}
            strokeDasharray={st.dash}
            opacity={st.opacity}
            markerEnd={`url(#${idPrefix}-arrow-${e.state})`}
          />
        );
      })}
      {nodes.map((n) => {
        const p = positions[n.id];
        const st = NODE_STYLE[n.state];
        const [first, ...rest] = n.label.split(" ");
        return (
          <g key={n.id}>
            <polygon points={hexPoints(p.x, p.y, hexR)} fill={st.fill} stroke={st.stroke} strokeWidth={1.8} strokeDasharray={st.dash} />
            <text x={p.x} y={p.y - 2} textAnchor="middle" fontSize={primaryFontSize} fontWeight={700} fill={st.text}>
              {first}
            </text>
            {rest.length ? (
              <text x={p.x} y={p.y + 11} textAnchor="middle" fontSize={secondaryFontSize} fill={st.text} opacity={0.85}>
                {rest.join(" ")}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}

/**
 * Prompt 3C §14 — Hexagonal inference & fault flow. Six categorical hex nodes
 * and six directed edges driven entirely by the operational view model. When
 * PPG faults, the PPG node breaks, its edge to the window breaks, the window
 * is blocked, and the model/output become unavailable even though IMU stays
 * confirmed — visually proving that one confirmed input is insufficient.
 * Renders two purpose-built layouts (wide horizontal on >=sm, tall vertical
 * below sm) rather than shrinking one fixed-width SVG, so no node clips and
 * no horizontal scrollbar appears at any viewport (§14 acceptance criteria).
 */
export function InferenceHexFlow() {
  const view = useOperationalViewModel();
  const ppg = view.modalities.find((m) => m.modality === "PPG")!;
  const imu = view.modalities.find((m) => m.modality === "IMU")!;
  const { nodes, edges } = deriveHexFlow({
    telemetry: view.telemetryAvailability,
    ppgState: ppg.nodeState,
    imuState: imu.nodeState,
    isReplay: view.isReplay,
    predictionAvailable: view.predictionAvailability === "available",
    inferenceWarmingUp: view.inference?.status === "warming_up",
  });
  const nodeById = (id: HexNodeId) => nodes.find((n) => n.id === id)!;

  return (
    <section aria-labelledby="hexflow-heading" className="flex flex-col gap-2 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="hexflow-heading" className="text-sm font-semibold text-ink-primary">
          Inference &amp; fault flow
        </h2>
        <span className="text-[10px] uppercase tracking-wide text-ink-muted">Source → HR output</span>
      </div>

      <div className="w-full">
        <HexFlowSvg
          idPrefix="hexflow-desktop"
          positions={DESKTOP_POS}
          viewBox={DESKTOP_VIEWBOX}
          hexR={DESKTOP_HEX_R}
          nodes={nodes}
          edges={edges}
          primaryFontSize={10.5}
          secondaryFontSize={8.5}
          className="hidden h-auto w-full sm:block"
        />
        <HexFlowSvg
          idPrefix="hexflow-mobile"
          positions={MOBILE_POS}
          viewBox={MOBILE_VIEWBOX}
          hexR={MOBILE_HEX_R}
          nodes={nodes}
          edges={edges}
          primaryFontSize={11}
          secondaryFontSize={9}
          className="mx-auto block h-auto max-w-[280px] sm:hidden"
        />
      </div>

      {/* §18 — accessible node names + states without requiring the SVG. */}
      <ul className="grid grid-cols-2 gap-x-3 gap-y-0.5 text-[10px] text-ink-secondary sm:grid-cols-3">
        {nodes.map((n) => (
          <li key={n.id} className="flex items-center gap-1.5">
            <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ backgroundColor: NODE_STYLE[n.state].stroke }} />
            <span className="font-semibold text-ink-primary">{n.label}:</span> {STATE_WORD[n.state]}
          </li>
        ))}
      </ul>
      <p className="text-[10px] leading-snug text-ink-muted">
        {nodeById("window").state === "blocked"
          ? "Window assembly requires both PPG and IMU — one confirmed input alone is insufficient."
          : "PPG + IMU assemble the model input window; the model produces the HR output."}
      </p>
    </section>
  );
}
