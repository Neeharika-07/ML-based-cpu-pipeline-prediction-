/**
 * PipelineAI - Dashboard Page
 * System overview, KPI cards, and quick start launcher.
 */

import { renderMetricCard } from "../components/MetricCard.js";
import { renderPipelineStages } from "../components/PipelineStages.js";
import { renderBranchHistoryViewer } from "../components/BranchHistoryViewer.js";

export function renderDashboard(metrics = null, traces = []) {
  const xgbMetric = metrics?.XGBoost || {
    accuracy: 0.8338,
    misprediction_rate: 0.1662,
    mpki: 33.23,
    f1: 0.7360
  };

  const perceptronMetric = metrics?.Perceptron || {
    accuracy: 0.8592,
    mpki: 28.16
  };

  const totalBranches = traces.reduce((acc, t) => acc + (t.total_branches || 0), 200000);

  return `
    <div class="page-dashboard">
      <div class="hero-banner">
        <div class="hero-text">
          <h2>PipelineAI Microarchitecture Engine</h2>
          <p>
            AI-driven Branch Predictor & 5-stage CPU Pipeline Hazard Simulator for modern RISC microprocessors.
            Trained on 200,000 real execution trace branches across 10 benchmark programs.
          </p>
        </div>
        <div class="hero-actions">
          <button class="btn btn-primary" onclick="window.appNavigate('simulator')">🚀 Launch Pipeline Simulator</button>
          <button class="btn btn-secondary" onclick="window.appNavigate('benchmark')">📊 View AI Benchmarks</button>
        </div>
      </div>

      <!-- KPI Summary Cards -->
      <div class="metrics-grid">
        ${renderMetricCard("AI Peak Accuracy", `${(perceptronMetric.accuracy * 100).toFixed(1)}%`, "", "Perceptron / XGBoost AI", "green", "🎯")}
        ${renderMetricCard("Microarchitectural MPKI", `${xgbMetric.mpki}`, "MPKI", "Mispredictions Per 1K Instructions", "purple", "⚡")}
        ${renderMetricCard("Speedup vs Baseline", "1.28x", "Faster", "Cycle reduction vs static stall", "amber", "⏱️")}
        ${renderMetricCard("Benchmark Dataset", `${totalBranches.toLocaleString()}`, "branches", "10 Traces (Train/Val/Test)", "blue", "💾")}
      </div>

      <!-- Live Pipeline Demo View -->
      <div class="panel-section">
        <div class="panel-title">
          <h3>⚡ 5-Stage CPU Pipeline Microarchitecture (IF ➔ ID ➔ EX ➔ MEM ➔ WB)</h3>
          <span class="badge badge-info">Zero-Penalty Speculative Execution</span>
        </div>
        ${renderPipelineStages({
          IF: { instruction: { pc: 0x4010a4, pc_hex: "0x4010a4", opcode: "BEQ", predicted_taken: 1, actual_taken: 1 }, is_bubble: false },
          ID: { instruction: { pc: 0x4010a0, pc_hex: "0x4010a0", opcode: "BNE", predicted_taken: 0, actual_taken: 0 }, is_bubble: false },
          EX: { instruction: { pc: 0x40109c, pc_hex: "0x40109c", opcode: "BEQ", predicted_taken: 1, actual_taken: 1 }, is_bubble: false },
          MEM: { instruction: { pc: 0x401098, pc_hex: "0x401098", opcode: "LOAD", predicted_taken: 0, actual_taken: 0 }, is_bubble: false },
          WB: { instruction: { pc: 0x401094, pc_hex: "0x401094", opcode: "ADD", predicted_taken: 0, actual_taken: 0 }, is_bubble: false }
        })}
      </div>

      <!-- Global History Register Showcase -->
      <div class="panel-section">
        <div class="panel-title">
          <h3>🧠 Global Branch History Register (BHR)</h3>
          <span class="badge badge-success">16-Bit Speculative Shift Window</span>
        </div>
        ${renderBranchHistoryViewer([1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0])}
      </div>

      <!-- Quick Trace Dataset Cards -->
      <div class="panel-section">
        <div class="panel-title">
          <h3>📂 Trace Workload Profiles</h3>
          <span class="badge badge-secondary">10 CPU Traces Available</span>
        </div>
        <div class="traces-grid">
          ${(traces.length ? traces : [
            { trace_id: 0, total_branches: 20016, taken_percentage: 39.4 },
            { trace_id: 1, total_branches: 20016, taken_percentage: 42.1 },
            { trace_id: 2, total_branches: 20016, taken_percentage: 36.8 },
            { trace_id: 3, total_branches: 20016, taken_percentage: 38.2 }
          ]).slice(0, 4).map(t => `
            <div class="trace-card">
              <div class="trace-card-header">
                <span class="trace-badge">Trace #${t.trace_id}</span>
                <span class="trace-ratio">${t.taken_percentage}% Taken</span>
              </div>
              <div class="trace-card-body">
                <div>Total Branches: <strong>${t.total_branches.toLocaleString()}</strong></div>
                <div>Warmup: <strong>16 branches</strong></div>
                <div>Split: <strong>14k Train / 3k Val / 3k Test</strong></div>
              </div>
              <button class="btn btn-sm btn-outline" onclick="window.runTraceSim(${t.trace_id})">Simulate Trace #${t.trace_id} ➔</button>
            </div>
          `).join("")}
        </div>
      </div>
    </div>
  `;
}
