import type { ModalityNodeState } from "@/lib/monitoring/modalityNodeState";
import type { TelemetryAvailability } from "@/lib/monitoring/telemetryAvailability";

/**
 * Prompt 3B §10 — the hexagonal inference-and-fault flow. Categorical only; no
 * probability, no invented model computation. Pure/JSX-free so the mapping
 * (including PPG/IMU/both-input fault propagation) is directly testable.
 */
export type HexNodeId = "source" | "ppgInput" | "imuInput" | "window" | "model" | "output";
export type HexNodeState = "confirmed" | "awaiting" | "blocked" | "fault" | "unavailable" | "disconnected" | "source_error";
export type HexEdgeState = "active" | "broken" | "idle";

export interface HexNode {
  id: HexNodeId;
  label: string;
  state: HexNodeState;
}
export interface HexEdge {
  id: string;
  from: HexNodeId;
  to: HexNodeId;
  state: HexEdgeState;
}

const EDGES: { id: string; from: HexNodeId; to: HexNodeId }[] = [
  { id: "src-ppg", from: "source", to: "ppgInput" },
  { id: "src-imu", from: "source", to: "imuInput" },
  { id: "ppg-win", from: "ppgInput", to: "window" },
  { id: "imu-win", from: "imuInput", to: "window" },
  { id: "win-model", from: "window", to: "model" },
  { id: "model-out", from: "model", to: "output" },
];

const LABELS: Record<HexNodeId, string> = {
  source: "Source",
  ppgInput: "PPG input",
  imuInput: "IMU input",
  window: "Window assembly",
  model: "HR model",
  output: "HR output",
};

function telToNode(t: Exclude<TelemetryAvailability, "active">): HexNodeState {
  return t === "disconnected" ? "disconnected" : t === "source_error" ? "source_error" : "awaiting";
}

function inputFromNode(s: ModalityNodeState): HexNodeState {
  switch (s) {
    case "confirmed":
      return "confirmed";
    case "fault":
      return "fault";
    case "warmup":
    case "awaiting_confirmation":
      return "awaiting";
    case "unavailable":
      return "unavailable";
    case "disconnected":
      return "disconnected";
    case "source_error":
      return "source_error";
  }
}

export function deriveHexFlow(params: {
  telemetry: TelemetryAvailability;
  ppgState: ModalityNodeState;
  imuState: ModalityNodeState;
  isReplay: boolean;
  predictionAvailable: boolean;
  inferenceWarmingUp: boolean;
}): { nodes: HexNode[]; edges: HexEdge[] } {
  const { telemetry, ppgState, imuState, isReplay, predictionAvailable, inferenceWarmingUp } = params;

  let states: Record<HexNodeId, HexNodeState>;

  if (telemetry !== "active") {
    const s = telToNode(telemetry);
    states = {
      source: s,
      ppgInput: s,
      imuInput: s,
      window: s === "awaiting" ? "awaiting" : "blocked",
      model: s === "awaiting" ? "awaiting" : "blocked",
      output: s === "awaiting" ? "awaiting" : "unavailable",
    };
  } else {
    const ppgInput = inputFromNode(ppgState);
    const imuInput = inputFromNode(imuState);
    const inputBlocked = (n: HexNodeState) => n === "fault" || n === "unavailable" || n === "disconnected" || n === "source_error";
    let window: HexNodeState;
    if (inputBlocked(ppgInput) || inputBlocked(imuInput)) window = "blocked";
    else if (ppgInput === "awaiting" || imuInput === "awaiting") window = "awaiting";
    else window = "confirmed";

    let model: HexNodeState;
    if (window === "blocked") model = "unavailable";
    else if (window === "awaiting") model = "awaiting";
    else if (!isReplay) model = "unavailable";
    else if (inferenceWarmingUp) model = "awaiting";
    else if (predictionAvailable) model = "confirmed";
    else model = "unavailable";

    const output: HexNodeState = model === "confirmed" ? "confirmed" : model === "awaiting" ? "awaiting" : "unavailable";
    states = { source: "confirmed", ppgInput, imuInput, window, model, output };
  }

  const nodes: HexNode[] = (Object.keys(LABELS) as HexNodeId[]).map((id) => ({ id, label: LABELS[id], state: states[id] }));

  const edges: HexEdge[] = EDGES.map((e) => {
    const from = states[e.from];
    const to = states[e.to];
    let state: HexEdgeState;
    if (to === "fault" || from === "fault") state = "broken";
    else if (to === "blocked" && (from === "confirmed" || from === "awaiting")) state = "broken";
    else if (from === "confirmed" && (to === "confirmed" || to === "awaiting")) state = "active";
    else state = "idle";
    return { ...e, state };
  });

  return { nodes, edges };
}
