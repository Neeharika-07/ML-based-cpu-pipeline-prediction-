/**
 * PipelineAI - MetricCard Component
 * Displays microarchitectural and ML key performance indicators.
 */

export function renderMetricCard(title, value, unit = "", subtitle = "", color = "blue", icon = "📊") {
  return `
    <div class="metric-card metric-${color}">
      <div class="metric-header">
        <span class="metric-title">${title}</span>
        <span class="metric-icon">${icon}</span>
      </div>
      <div class="metric-body">
        <span class="metric-value">${value}</span>
        <span class="metric-unit">${unit}</span>
      </div>
      ${subtitle ? `<div class="metric-subtitle">${subtitle}</div>` : ""}
    </div>
  `;
}
