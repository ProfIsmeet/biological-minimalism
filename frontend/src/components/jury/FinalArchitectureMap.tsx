import { FINAL_MODULES, MODALITY_COLOR, type FinalModality } from "@/lib/architecture";

interface RegionPlate {
  id: string;
  order: string;
  label: string;
  modalities: { modality: FinalModality; isContextAddition?: boolean }[];
  note: string | null;
}

// Physical layout is Frontal → Chest → Wrist (master prompt 3 §7.3); the
// PPG+IMU grouping note only appears on the Wrist row, and only EOG carries
// the "context addition" marker — architecture facts sourced from
// lib/architecture.ts, nothing invented here.
const REGION_PLATES: RegionPlate[] = FINAL_MODULES.map((module) => {
  if (module.id === "frontal") {
    return {
      id: module.id,
      order: module.order,
      label: module.label,
      modalities: [{ modality: "EEG" }, { modality: "EOG", isContextAddition: true }],
      note: null,
    };
  }
  if (module.id === "chest") {
    return { id: module.id, order: module.order, label: module.label, modalities: [{ modality: "ECG" }], note: null };
  }
  return {
    id: module.id,
    order: module.order,
    label: module.label,
    modalities: [{ modality: "PPG" }, { modality: "IMU" }],
    note: "PPG + IMU → HR inference",
  };
});

function ModalityNode({ modality, isContextAddition }: { modality: FinalModality; isContextAddition?: boolean }) {
  return (
    <span
      className={
        isContextAddition
          ? "flex items-center gap-1.5 rounded-[6px] border border-final-accent/50 bg-final-accent-soft px-2.5 py-1.5"
          : "flex items-center gap-1.5 rounded-[6px] border border-jury-border-subtle bg-surface-2 px-2.5 py-1.5"
      }
    >
      <span aria-hidden="true" className="h-2 w-2 rounded-full" style={{ backgroundColor: MODALITY_COLOR[modality] }} />
      <span className={isContextAddition ? "text-sm font-semibold text-final-accent" : "text-sm font-semibold text-ink-primary"}>
        {modality}
      </span>
      {isContextAddition ? (
        <span className="text-[10px] font-semibold uppercase tracking-wide text-final-accent">context addition</span>
      ) : null}
    </span>
  );
}

// Master-prompt 3 §7.3 — final sensing architecture plate: a vertical
// anatomical axis (Frontal → Chest → Wrist) with five individual modality
// nodes, the wrist PPG+IMU grouping into HR inference made explicit, and EOG
// marked as the sole context addition. Decorative axis/connector lines are
// aria-hidden; every fact is also present as plain text so the figure has a
// complete accessible equivalent without color.
export function FinalArchitectureMap() {
  return (
    <section aria-labelledby="final-architecture-heading" className="flex flex-col gap-4 rounded-[12px] border border-jury-border-subtle bg-surface-1 p-6">
      <div>
        <h2 id="final-architecture-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Final sensing architecture
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          Five modalities are integrated across three wearable regions, organized here by physical module rather than
          isolated sensor count.
        </p>
      </div>

      <div className="relative pl-7">
        <span aria-hidden="true" className="absolute left-[7px] top-2 bottom-2 w-px bg-jury-border-strong" />
        <div className="flex flex-col gap-6">
          {REGION_PLATES.map((region) => (
            <div key={region.id} className="relative flex flex-col gap-2">
              <span
                aria-hidden="true"
                className="absolute -left-7 top-1 h-3.5 w-3.5 rounded-full border-2 border-final-accent bg-surface-1"
              />
              <p className="text-[11px] font-semibold uppercase tracking-wide text-ink-muted">
                {region.order} — {region.label}
              </p>
              <div className="flex flex-wrap gap-2">
                {region.modalities.map(({ modality, isContextAddition }) => (
                  <ModalityNode key={modality} modality={modality} isContextAddition={isContextAddition} />
                ))}
              </div>
              {region.note ? <p className="text-xs font-medium text-ink-secondary">{region.note}</p> : null}
            </div>
          ))}
        </div>
      </div>

      <p className="border-t border-jury-border-subtle pt-3 text-[11px] leading-relaxed text-ink-muted">
        EOG is architecture-selected context for the frontal module; it is not a current input to the wrist PPG + IMU
        heart-rate model.
      </p>
    </section>
  );
}
