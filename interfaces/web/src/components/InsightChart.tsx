import { useMemo, useState } from "react";

import type { ChartReference } from "../api/types";

type ChartView = "auto" | "bar" | "line" | "scatter" | "table";
type ResolvedChartView = Exclude<ChartView, "auto">;

const CHART_VIEWS: Array<{ value: ChartView; label: string }> = [
  { value: "auto", label: "Auto" },
  { value: "bar", label: "Barras" },
  { value: "line", label: "Línea" },
  { value: "scatter", label: "Puntos" },
  { value: "table", label: "Tabla" },
];

function formatNumber(value: number): string {
  return new Intl.NumberFormat("es", { maximumFractionDigits: 2 }).format(value);
}

function formatLabel(value: string): string {
  return value.replace(/[_-]+/g, " ");
}

function numericValue(value: unknown): number {
  if (typeof value === "number") {
    return value;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
}

function defaultChartView(chart: ChartReference, hasPlottableData: boolean): ResolvedChartView {
  if (!hasPlottableData) {
    return "table";
  }
  if (chart.chart_type === "line" || chart.chart_type === "scatter") {
    return chart.chart_type;
  }
  return "bar";
}

function BarChart({ chart, xKey, yKey }: { chart: ChartReference; xKey: string; yKey: string }) {
  const data = chart.data ?? [];
  const maxValue = Math.max(...data.map((row) => numericValue(row[yKey])), 0);

  if (data.length === 0 || maxValue <= 0) {
    return <ChartTable chart={chart} />;
  }

  return (
    <div className="bar-chart" role="img" aria-label={chart.title ?? chart.name} data-testid="chart-view-bar">
      {data.slice(0, 8).map((row, index) => {
        const label = String(row[xKey] ?? `Item ${index + 1}`);
        const value = numericValue(row[yKey]);
        const width = Math.max((value / maxValue) * 100, 3);
        return (
          <div className="bar-row" key={`${chart.name}-${label}`}>
            <span className="bar-label">{label}</span>
            <div className="bar-track" aria-hidden="true">
              <div className="bar-fill" style={{ width: `${width}%` }} />
            </div>
            <strong>{formatNumber(value)}</strong>
          </div>
        );
      })}
    </div>
  );
}

function XYChart({
  chart,
  xKey,
  yKey,
  variant,
}: {
  chart: ChartReference;
  xKey: string;
  yKey: string;
  variant: "line" | "scatter";
}) {
  const data = (chart.data ?? []).slice(0, 12);
  const values = data.map((row) => numericValue(row[yKey]));
  const maxValue = Math.max(...values, 0);
  const minValue = Math.min(...values, 0);
  const range = Math.max(maxValue - minValue, 1);
  const width = 420;
  const height = 220;
  const padding = 28;
  const points = data.map((row, index) => {
    const x = padding + (data.length <= 1 ? 0 : (index / (data.length - 1)) * (width - padding * 2));
    const y = height - padding - ((numericValue(row[yKey]) - minValue) / range) * (height - padding * 2);
    return { x, y, label: String(row[xKey] ?? `Item ${index + 1}`), value: numericValue(row[yKey]) };
  });
  const pathData = points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");

  if (points.length === 0) {
    return <ChartTable chart={chart} />;
  }

  return (
    <div className="xy-chart" data-testid={variant === "line" ? "chart-view-line" : "chart-view-scatter"}>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={chart.title ?? chart.name}>
        <line x1={padding} x2={width - padding} y1={height - padding} y2={height - padding} className="chart-axis" />
        <line x1={padding} x2={padding} y1={padding} y2={height - padding} className="chart-axis" />
        {variant === "line" && points.length > 1 ? <path className="line-path" d={pathData} /> : null}
        {points.map((point) => (
          <g key={`${chart.name}-${point.label}`}>
            <circle className="point-dot" cx={point.x} cy={point.y} r="5" />
            <title>{`${point.label}: ${formatNumber(point.value)}`}</title>
          </g>
        ))}
      </svg>
    </div>
  );
}

function ChartTable({ chart }: { chart: ChartReference }) {
  const rows = chart.data ?? [];
  const columns = useMemo(() => {
    const names = new Set<string>();
    for (const row of rows) {
      Object.keys(row).forEach((column) => names.add(column));
    }
    return [...names];
  }, [rows]);

  if (rows.length === 0 || columns.length === 0) {
    return (
      <div className="mini-empty-state" data-testid="chart-view-table">
        <strong>Sin datos visualizables</strong>
        <p className="muted">El resultado no devolvió filas para esta vista.</p>
      </div>
    );
  }

  return (
    <div className="chart-table table-wrapper" data-testid="chart-view-table">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.slice(0, 8).map((row, index) => (
            <tr key={`${chart.name}-table-${index}`}>
              {columns.map((column) => (
                <td key={`${chart.name}-table-${index}-${column}`}>{String(row[column] ?? "—")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function InsightChart({ chart }: { chart: ChartReference }) {
  const [selectedView, setSelectedView] = useState<ChartView>("auto");
  const data = chart.data ?? [];
  const xKey = chart.x_key ?? "";
  const yKey = chart.y_key ?? "";
  const hasPlottableData = Boolean(xKey && yKey && data.length > 0 && Math.max(...data.map((row) => numericValue(row[yKey])), 0) > 0);
  const resolvedView = selectedView === "auto" ? defaultChartView(chart, hasPlottableData) : selectedView;

  if (data.length === 0) {
    return null;
  }

  return (
    <article className="insight-chart" data-testid={`chart-${chart.name}`}>
      <div className="chart-header">
        <div>
          <p className="eyebrow">Gráfico</p>
          <h4>{chart.title ?? chart.name}</h4>
          {xKey && yKey ? (
            <p className="chart-subtitle">
              {formatLabel(yKey)} por {formatLabel(xKey)}
            </p>
          ) : null}
        </div>
        <span className="status-chip status-soft">visual</span>
      </div>
      <div className="chart-switcher" aria-label="Tipo de gráfico">
        {CHART_VIEWS.map((view) => (
          <button
            key={view.value}
            type="button"
            className={`chart-switcher-button ${selectedView === view.value ? "chart-switcher-button-active" : ""}`}
            onClick={() => setSelectedView(view.value)}
            aria-pressed={selectedView === view.value}
          >
            {view.label}
          </button>
        ))}
      </div>
      {resolvedView === "table" || !hasPlottableData ? <ChartTable chart={chart} /> : null}
      {resolvedView === "bar" && hasPlottableData ? <BarChart chart={chart} xKey={xKey} yKey={yKey} /> : null}
      {resolvedView === "line" && hasPlottableData ? <XYChart chart={chart} xKey={xKey} yKey={yKey} variant="line" /> : null}
      {resolvedView === "scatter" && hasPlottableData ? <XYChart chart={chart} xKey={xKey} yKey={yKey} variant="scatter" /> : null}
    </article>
  );
}
