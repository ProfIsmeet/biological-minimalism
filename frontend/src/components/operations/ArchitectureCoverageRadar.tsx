"use client";

import { deriveCoverageRadar, radarPoint, radarPolygonPoints } from "@/lib/visualization/coverageRadar";
import { PLOT_COLOR } from "@/lib/visualization/operationalVisualTokens";
import { useOperationalViewModel } from "@/lib/monitoring/operationalViewModel";

/**
 * Mission Overview §11.2 — binary architecture-coverage radar.
 *
 * STRICT SEMANTICS (see lib/visualization/coverageRadar.ts for the enforced
 * contract): two BINARY series on a fixed 0–1 scale. Series A is static
 * CORE_PLUS_CONTEXT membership; series B is whether the authoritative
 * current-source contract provides that channel. Current usability remains
 * exact categorical table text, so a fault cannot be mistaken for source
 * absence. This encodes coverage and nothing else — not performance, quality, reliability,
 * sensitivity, accuracy or confidence — and no percentage is ever printed.
 *
 * Fail-closed: when the source is unconfirmed or erroring, the observation
 * polygon is WITHHELD rather than drawn as an all-zero shape, because an
 * all-zero polygon would falsely claim "we looked and found nothing".
 */
const DESKTOP_SIZE = 320;
const MOBILE_SIZE = 280;
const GRID_LEVELS = [0.25, 0.5, 0.75, 1];

function RadarSvg({ size, model }: { size: number; model: ReturnType<typeof deriveCoverageRadar> }) {
  const cx = size / 2;
  const cy = size / 2 + 6;
  const radius = size / 2 - 46;
  const axes = model.axes;
  const count = axes.length;

  const selectedPoints = radarPolygonPoints({ cx, cy, radius, values: axes.map((a) => a.selected) });
  const observedPoints = model.observationSeriesAvailable
    ? radarPolygonPoints({ cx, cy, radius, values: axes.map((a) => a.provided ?? 0) })
    : null;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true" focusable="false" className="mx-auto">
      {/* Grid rings at fixed 0.25 intervals of the 0–1 scale. */}
      {GRID_LEVELS.map((level) => (
        <polygon
          key={level}
          points={radarPolygonPoints({ cx, cy, radius, values: new Array(count).fill(level) })}
          fill="none"
          stroke="#A8BAC0"
          strokeOpacity={0.2}
          strokeWidth={1}
        />
      ))}
      {/* Spokes. */}
      {axes.map((axis, index) => {
        const outer = radarPoint({ cx, cy, radius, index, count, value: 1 });
        return <line key={axis.modality} x1={cx} y1={cy} x2={outer.x} y2={outer.y} stroke="#A8BAC0" strokeOpacity={0.2} strokeWidth={1} />;
      })}

      {/* Series A — static architecture membership (lime). */}
      <polygon points={selectedPoints} fill={PLOT_COLOR.architectureSeries} fillOpacity={0.08} stroke={PLOT_COLOR.architectureSeries} strokeWidth={2.25} />
      {axes.map((axis, index) => {
        const p = radarPoint({ cx, cy, radius, index, count, value: axis.selected });
        return <circle key={`sel-${axis.modality}`} cx={p.x} cy={p.y} r={5} fill={PLOT_COLOR.architectureSeries} />;
      })}

      {/* Series B — current-source channel provision (cyan). Withheld entirely when
          the source cannot currently be spoken for. */}
      {observedPoints ? (
        <>
          <polygon points={observedPoints} fill={PLOT_COLOR.observationSeries} fillOpacity={0.12} stroke={PLOT_COLOR.observationSeries} strokeWidth={2.5} />
          {axes.map((axis, index) => {
            if (axis.provided !== 1) return null;
            const p = radarPoint({ cx, cy, radius, index, count, value: 1 });
            return <circle key={`obs-${axis.modality}`} cx={p.x} cy={p.y} r={5} fill={PLOT_COLOR.observationSeries} />;
          })}
        </>
      ) : null}

      {/* Axis labels at 12px minimum. */}
      {axes.map((axis, index) => {
        const p = radarPoint({ cx, cy, radius: radius + 24, index, count, value: 1 });
        return (
          <text key={`label-${axis.modality}`} x={p.x} y={p.y} textAnchor="middle" dominantBaseline="middle" fontSize={13} fontWeight={600} fill="#A8BAC0">
            {axis.modality}
          </text>
        );
      })}
    </svg>
  );
}

export function ArchitectureCoverageRadar() {
  const view = useOperationalViewModel();
  const model = deriveCoverageRadar({
    telemetry: view.telemetryAvailability,
    modalityStates: view.modalities.map((m) => ({
      modality: m.modality,
      nodeState: m.nodeState,
      unavailableReason: m.observation.unavailableReason,
      providedBySource: m.providedBySource,
    })),
    isReplay: view.isReplay,
    initialSourceEstablishment: view.sourceStateStatus === "loading" && view.confirmedTimestampSeconds === null,
  });

  const accessibleSummary = model.axes
    .map((a) => `${a.modality}: architecture ${a.selected === 1 ? "member" : "not a member"}, ${a.provided === null ? "source coverage withheld" : a.provided === 1 ? "provided by current source" : "not provided by current source"}`)
    .join(". ");

  return (
    <section
      aria-labelledby="coverage-radar-heading"
      aria-describedby="coverage-radar-desc"
      className="flex h-full flex-col gap-3 rounded-[10px] border border-jury-border-subtle bg-surface-1 p-[18px]"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="coverage-radar-heading" className="text-[17px] font-semibold leading-tight text-ink-primary">
          Architecture coverage
        </h2>
        <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Binary 0–1</span>
      </div>
      <p id="coverage-radar-desc" className="sr-only">
        Binary coverage radar on a fixed zero-to-one scale. {accessibleSummary}. Current usability is stated in the exact table and
        never encoded as a fractional value. This encodes channel coverage only, never model performance.
      </p>

      <div className="relative">
        <div className="hidden sm:block">
          <RadarSvg size={DESKTOP_SIZE} model={model} />
        </div>
        <div className="block sm:hidden">
          <RadarSvg size={MOBILE_SIZE} model={model} />
        </div>
        {!model.observationSeriesAvailable ? (
          <p className="mt-1 rounded-[6px] border border-jury-warning/40 bg-jury-warning-soft px-3 py-2 text-center text-[12px] font-semibold uppercase tracking-wide text-jury-warning">
            {model.withheldReason}
          </p>
        ) : null}
      </div>

      <ul className="flex flex-col gap-1.5">
        <li className="flex items-center gap-2.5">
          <svg width={20} height={10} aria-hidden="true" focusable="false" className="shrink-0">
            <line x1={1} y1={5} x2={19} y2={5} stroke={PLOT_COLOR.architectureSeries} strokeWidth={3} />
          </svg>
          <span className="text-[12px] text-ink-secondary">Static architecture membership</span>
        </li>
        <li className="flex items-center gap-2.5">
          <svg width={20} height={10} aria-hidden="true" focusable="false" className="shrink-0">
            <line x1={1} y1={5} x2={19} y2={5} stroke={PLOT_COLOR.observationSeries} strokeWidth={3} />
          </svg>
          <span className="text-[12px] text-ink-secondary">Channel provided by confirmed source</span>
        </li>
      </ul>

      {/* The radar never replaces exact state text (§11.2). */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[260px] text-left text-[12px]">
          <caption className="sr-only">Exact binary coverage and observation reason per modality</caption>
          <thead className="border-b border-jury-border-subtle text-xs uppercase tracking-wide text-ink-muted">
            <tr>
              <th scope="col" className="py-1.5 pr-2 font-semibold">Modality</th>
              <th scope="col" className="py-1.5 pr-2 font-semibold">Arch.</th>
              <th scope="col" className="py-1.5 font-semibold">Source provision · current state</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-jury-border-subtle">
            {model.axes.map((axis) => (
              <tr key={axis.modality}>
                <td className="py-1.5 pr-2 font-semibold text-ink-primary">{axis.modality}</td>
                <td className="py-1.5 pr-2 tabular-nums text-ink-secondary">{axis.selected}</td>
                <td className="py-1.5 text-ink-secondary">
                  {axis.provided === null ? "Withheld" : axis.provided} · {axis.provisionReason}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-[12px] leading-snug text-ink-muted">Binary coverage only — not model performance.</p>
    </section>
  );
}
