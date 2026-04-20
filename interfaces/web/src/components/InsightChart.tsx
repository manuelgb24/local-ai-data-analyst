import type { ChartReference } from "../api/types";

function formatNumber(value: number): string {
  return new Intl.NumberFormat("es", { maximumFractionDigits: 2 }).format(value);
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

export function InsightChart({ chart }: { chart: ChartReference }) {
  const data = chart.data ?? [];
  const xKey = chart.x_key ?? "";
  const yKey = chart.y_key ?? "";
  const maxValue = Math.max(...data.map((row) => numericValue(row[yKey])), 0);

  if (!xKey || !yKey || data.length === 0 || maxValue <= 0) {
    return null;
  }

  return (
    <article className="insight-chart" data-testid={`chart-${chart.name}`}>
      <div className="chart-header">
        <div>
          <p className="eyebrow">Gráfico</p>
          <h4>{chart.title ?? chart.name}</h4>
        </div>
        <span className="status-chip status-soft">embebido</span>
      </div>
      <div className="bar-chart" role="img" aria-label={chart.title ?? chart.name}>
        {data.slice(0, 8).map((row, index) => {
          const label = String(row[xKey] ?? `Item ${index + 1}`);
          const value = numericValue(row[yKey]);
          const width = Math.max((value / maxValue) * 100, 3);
          return (
            <div className="bar-row" key={`${chart.name}-${label}`}>
              <span className="bar-label">{label}</span>
              <div className="bar-track">
                <div className="bar-fill" style={{ width: `${width}%` }} />
              </div>
              <strong>{formatNumber(value)}</strong>
            </div>
          );
        })}
      </div>
    </article>
  );
}

