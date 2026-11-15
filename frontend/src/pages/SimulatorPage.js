/**
 * PipelineAI - Simulator Page
 * Interactive cycle-accurate CPU pipeline simulator with step execution,
 * branch prediction visualization, stall bubbles, and flush triggers.
 */

import { renderPipelineStages } from "../components/PipelineStages.js";
import { renderBranchHistoryViewer } from "../components/BranchHistoryViewer.js";
import { renderMetricCard } from "../components/MetricCard.js";
import { renderTraceTable } from "../components/TraceTable.js";

export function renderSimulatorPage(simState) {
  const currentCycle = simState.cycleIndex || 0;
  const cycleData = simState.cycleTraces?.[currentCycle] || null;
  const simResults = simState.results || {};

  return `
    <div class="page-simulator">
      <div class="simulator-controls-bar">
        <div class="control-group">
          <label>Workload Trace:</label>
          <select id="simTraceSelect" class="form-select">
            <option value="0" ${simState.selectedTrace === 0 ? "selected" : ""}>Trace #0 (20k branches)</option>
            <option value="1" ${simState.selectedTrace === 1 ? "selected" : ""}>Trace #1 (20k branches)</option>
            <option value="2" ${simState.selectedTrace === 2 ? "selected" : ""}>Trace #2 (20k branches)</option>
            <option value="3" ${simState.selectedTrace === 3 ? "selected" : ""}>Trace #3 (20k branches)</option>
            <option value="4" ${simState.selectedTrace === 4 ? "selected" : ""}>Trace #4 (20k branches)</option>
          </select>
        </div>

        <div class="control-group">
          <label>Branch Predictor:</label>
          <select id="simPredictorSelect" class="form-select">
            <option value="xgboost" ${simState.selectedPredictor === "xgboost" ? "selected" : ""}>🤖 XGBoost (PipelineAI Engine)</option>
            <option value="perceptron" ${simState.selectedPredictor === "perceptron" ? "selected" : ""}>🧠 Perceptron (Neural)</option>
            <option value="gshare" ${simState.selectedPredictor === "gshare" ? "selected" : ""}>⚙️ Gshare (Hardware XOR)</option>
            <option value="bimodal" ${simState.selectedPredictor === "bimodal" ? "selected" : ""}>🔢 Bimodal (2-Bit Counter)</option>
            <option value="static_not_taken" ${simState.selectedPredictor === "static_not_taken" ? "selected" : ""}>⏹️ Static (Always Not Taken)</option>
          </select>
        </div>

        <div class="control-group">
          <label>Branches Limit:</label>
          <select id="simLimitSelect" class="form-select">
            <option value="30">30 Instructions</option>
            <option value="60" selected>60 Instructions</option>
            <option value="120">120 Instructions</option>
            <option value="250">250 Instructions</option>
          </select>
        </div>

        <div class="control-group">
          <label>Penalty (Cycles):</label>
          <select id="simPenaltySelect" class="form-select">
            <option value="2" selected>2 Cycles (Classic 5-Stage)</option>
            <option value="3">3 Cycles (Deep Pipeline)</option>
          </select>
        </div>

        <div class="control-actions">
          <button id="btnRunSim" class="btn btn-primary" onclick="window.triggerSimRun()">▶ Run Simulation</button>
          <button id="btnCompareSim" class="btn btn-secondary" onclick="window.triggerSimCompare()">⚖️ Compare All</button>
        </div>
      </div>

      <!-- Live Execution Timeline Controls -->
      ${simState.cycleTraces?.length ? `
        <div class="playback-toolbar">
          <div class="playback-buttons">
            <button class="btn btn-sm" onclick="window.stepSimCycle(-1)">⏮ Prev Cycle</button>
            <button class="btn btn-sm btn-primary" id="btnPlayPause" onclick="window.togglePlayPause()">
              ${simState.isPlaying ? "⏸ Pause" : "▶ Play Animation"}
            </button>
            <button class="btn btn-sm" onclick="window.stepSimCycle(1)">⏭ Next Cycle</button>
            <button class="btn btn-sm btn-outline" onclick="window.resetSimPlayback()">🔄 Reset</button>
          </div>
          <div class="cycle-indicator">
            <span>Cycle: <strong>${cycleData ? cycleData.cycle : 0}</strong> / ${simState.cycleTraces.length}</span>
            <input type="range" min="0" max="${simState.cycleTraces.length - 1}" value="${currentCycle}"
                   class="cycle-slider" oninput="window.setSimCycle(this.value)">
          </div>
        </div>
      ` : ""}

      <!-- 5-Stage Animated Pipeline Diagram -->
      <div class="panel-section">
        <div class="panel-title">
          <h3>⚡ Cycle ${cycleData ? cycleData.cycle : 0}: 5-Stage Pipeline Status</h3>
          ${cycleData?.misprediction ? `
            <span class="badge badge-danger">💥 MISPREDICTION DETECTED IN EX! Flushed IF & ID!</span>
          ` : `
            <span class="badge badge-success">✓ Pipeline Flowing Smoothly</span>
          `}
        </div>
        ${renderPipelineStages(cycleData?.stages, cycleData?.misprediction)}
      </div>

      <!-- Real-time BHR Register State -->
      <div class="panel-section">
        ${renderBranchHistoryViewer(cycleData?.bhr_list || [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])}
      </div>

      <!-- Cumulative Performance Telemetry -->
      <div class="metrics-grid">
        ${renderMetricCard("Total Clock Cycles", simResults.total_cycles || 0, "cycles", "Execution elapsed", "blue", "⏱️")}
        ${renderMetricCard("Instructions Retired", simResults.instructions_retired || 0, "inst", "Throughput count", "green", "🎯")}
        ${renderMetricCard("Cycles Per Instruction (CPI)", simResults.cpi || 1.0, "CPI", "Lower is better (Ideal: 1.0)", "amber", "📉")}
        ${renderMetricCard("Misprediction Rate", `${((simResults.misprediction_rate || 0) * 100).toFixed(1)}%`, "", `${simResults.branches_mispredicted || 0} flushes triggered`, "purple", "⚠️")}
      </div>

      <!-- Trace Branch Records Table -->
      <div class="panel-section">
        ${renderTraceTable(simState.loadedBranches || [], "Active Workload Instructions")}
      </div>
    </div>
  `;
}
