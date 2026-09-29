"use client";

import { CartesianGrid, Cell, ResponsiveContainer, Scatter, ScatterChart, XAxis, YAxis, ZAxis } from "recharts";

import { ChartFrame, SemanticTable } from "@/components/visualization/shared/ChartFrame";
import { directionalityLabel, tabularNumber, uncertaintyLabel } from "@/lib/visualization/dataToMark";
import {
  PPG_DALIA_CAPACITY_CONTROL,
  PPG_DALIA_SUBJECT_HETEROGENEITY,
  PTT_SUBJECT_HETEROGENEITY,
  SLEEP_EDF_PRIMARY_ABC,
  seriesMeanSd,
  type SeedSeries,
} from "@/data/stage6/sensitivitySmallMultiples";

/** One family: seed/subject-level dots + a mean diamond per series, X = metric value, Y = categorical series row. */
function SeriesPanel({ series, unit }: { series: SeedSeries[]; unit: string }) {
  const rows = series.map((s, rowIndex) => {
    const stats = seriesMeanSd(s.values);
    const points = Object.entries(s.values).map(([sampleId, value]) => ({ x: value, y: rowIndex, sampleId, seriesLabel: s.label }));
    return { series: s, rowIndex, stats, points };
  });
  const allValues = series.flatMap((s) => Object.values(s.values));
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const pad = Math.max(0.05, (max - min) * 0.15);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
        <CartesianGrid strokeDasharray="2 3" stroke="#1B2A31" />
        <XAxis
          type="number"
          dataKey="x"
          domain={[min - pad, max + pad]}
          tickFormatter={(v: number) => v.toFixed(2)}
          tick={{ fontSize: 12, fill: "#8CA0A6" }}
          label={{ value: unit, position: "insideBottom", offset: -6, fontSize: 12, fill: "#8CA0A6" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          type="number"
          dataKey="y"
          domain={[-0.5, series.length - 0.5]}
          ticks={series.map((_, i) => i)}
          tickFormatter={(v: number) => series[v]?.label.split(" ")[0] ?? ""}
          tick={{ fontSize: 11, fill: "#8CA0A6" }}
          width={80}
          axisLine={false}
          tickLine={false}
        />
        <ZAxis range={[36, 36]} />
        {rows.map((row) => (
          <Scatter key={`${row.series.label}-points`} data={row.points} fill="#69B7AD" fillOpacity={0.75} shape="circle" isAnimationActive={false}>
            {row.points.map((p) => (
              <Cell key={p.sampleId} />
            ))}
          </Scatter>
        ))}
        <Scatter
          data={rows.map((row) => ({ x: row.stats.mean, y: row.rowIndex }))}
          fill="#D5A45E"
          shape="diamond"
          isAnimationActive={false}
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

export function SensitivitySmallMultiples() {
  return (
    <section aria-labelledby="sensitivity-small-multiples-heading" className="flex flex-col gap-4">
      <div>
        <h2 id="sensitivity-small-multiples-heading" className="text-2xl font-semibold leading-tight tracking-[-0.02em] text-ink-primary">
          Sensitivity &amp; ablation small multiples
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-ink-secondary">
          Participant/seed-level points (teal circles) and the sample mean (ochre diamond, never a population confidence
          interval) for each governing quantitative result. One comparable metric family per panel.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartFrame
          id="ppg-dalia-capacity"
          title={PPG_DALIA_CAPACITY_CONTROL.title}
          unit={PPG_DALIA_CAPACITY_CONTROL.metric}
          evidenceClassLabel="Governing"
          summary={`${directionalityLabel(PPG_DALIA_CAPACITY_CONTROL.direction)}. ${PPG_DALIA_CAPACITY_CONTROL.sampleUnit}.`}
          footer={
            <>
              <p className="text-xs text-ink-muted">{uncertaintyLabel("seed_sd")} · {PPG_DALIA_CAPACITY_CONTROL.claimBoundary}</p>
              <SemanticTable
                caption="PPG-DaLiA capacity-controlled seed values"
                columns={["Series", "n seeds", "Mean MAE (bpm)"]}
                rows={PPG_DALIA_CAPACITY_CONTROL.series.map((s) => {
                  const stats = seriesMeanSd(s.values);
                  return { key: s.label, cells: [s.label, String(stats.n), tabularNumber(stats.mean, 2)] };
                })}
              />
            </>
          }
        >
          <SeriesPanel series={PPG_DALIA_CAPACITY_CONTROL.series} unit="MAE (bpm)" />
        </ChartFrame>

        <ChartFrame
          id="ptt-heterogeneity"
          title={PTT_SUBJECT_HETEROGENEITY.title}
          unit={PTT_SUBJECT_HETEROGENEITY.metric}
          evidenceClassLabel="Governing"
          summary={`${directionalityLabel(PTT_SUBJECT_HETEROGENEITY.direction)}. ${PTT_SUBJECT_HETEROGENEITY.sampleUnit}. Sign flips when subject s2 is excluded — shown, not concealed.`}
          footer={
            <>
              <p className="text-xs text-jury-warning">
                Aggregate WITH s2: {tabularNumber(PTT_SUBJECT_HETEROGENEITY.aggregateWithS2.deltaBMinusA, 3)} ({PTT_SUBJECT_HETEROGENEITY.aggregateWithS2.direction}) ·
                WITHOUT s2: {tabularNumber(PTT_SUBJECT_HETEROGENEITY.aggregateWithoutS2.deltaBMinusA, 3)} ({PTT_SUBJECT_HETEROGENEITY.aggregateWithoutS2.direction})
              </p>
              <p className="text-xs text-ink-muted">{uncertaintyLabel("none")} · {PTT_SUBJECT_HETEROGENEITY.claimBoundary}</p>
              <SemanticTable
                caption="PTT per-subject delta"
                columns={["Subject", "Delta MAE (bpm, B-A)"]}
                rows={Object.entries(PTT_SUBJECT_HETEROGENEITY.perSubjectDelta).map(([id, v]) => ({ key: id, cells: [id, tabularNumber(v, 3)] }))}
              />
            </>
          }
        >
          <SeriesPanel series={[{ label: "PTT (n=4 subjects)", values: PTT_SUBJECT_HETEROGENEITY.perSubjectDelta }]} unit="delta MAE (bpm)" />
        </ChartFrame>

        <ChartFrame
          id="sleep-edf-primary"
          title={SLEEP_EDF_PRIMARY_ABC.title}
          unit={SLEEP_EDF_PRIMARY_ABC.metric}
          evidenceClassLabel="Governing"
          summary={`${directionalityLabel(SLEEP_EDF_PRIMARY_ABC.direction)}. ${SLEEP_EDF_PRIMARY_ABC.sampleUnit}.`}
          footer={
            <>
              <p className="text-xs text-ink-muted">{uncertaintyLabel("seed_sd")} · {SLEEP_EDF_PRIMARY_ABC.claimBoundary}</p>
              <SemanticTable
                caption="Sleep-EDF primary A/B/C macro-F1 by series"
                columns={["Series", "n seeds", "Mean macro-F1"]}
                rows={SLEEP_EDF_PRIMARY_ABC.series.map((s) => {
                  const stats = seriesMeanSd(s.values);
                  return { key: s.label, cells: [s.label, String(stats.n), tabularNumber(stats.mean, 3)] };
                })}
              />
            </>
          }
        >
          <SeriesPanel series={SLEEP_EDF_PRIMARY_ABC.series} unit="macro-F1" />
        </ChartFrame>

        <ChartFrame
          id="ppg-dalia-subject-activity"
          title={PPG_DALIA_SUBJECT_HETEROGENEITY.title}
          unit={PPG_DALIA_SUBJECT_HETEROGENEITY.metric}
          evidenceClassLabel="Governing"
          summary={`${directionalityLabel(PPG_DALIA_SUBJECT_HETEROGENEITY.direction)}. ${PPG_DALIA_SUBJECT_HETEROGENEITY.sampleUnit}.`}
          footer={
            <>
              <p className="text-xs text-ink-muted">{uncertaintyLabel("none")} · {PPG_DALIA_SUBJECT_HETEROGENEITY.claimBoundary}</p>
              <SemanticTable
                caption="PPG-DaLiA per-subject capacity-controlled delta"
                columns={["Subject", "Delta MAE (bpm, A_cap->B)"]}
                rows={Object.entries(PPG_DALIA_SUBJECT_HETEROGENEITY.perSubjectDelta).map(([id, v]) => ({ key: id, cells: [id, tabularNumber(v, 3)] }))}
              />
            </>
          }
        >
          <SeriesPanel series={[{ label: "PPG-DaLiA (n=3 subjects)", values: PPG_DALIA_SUBJECT_HETEROGENEITY.perSubjectDelta }]} unit="delta MAE (bpm)" />
        </ChartFrame>
      </div>
    </section>
  );
}
