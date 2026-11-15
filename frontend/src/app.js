/**
 * PipelineAI - Master Application Coordinator
 * Manages routing, state, playback animation, and DOM rendering.
 */

import { ApiService } from "./services/api.js?v=2.1";
import { renderDashboard } from "./pages/Dashboard.js?v=2.1";
import { renderSimulatorPage } from "./pages/SimulatorPage.js?v=2.1";
import { renderBenchmarkPage } from "./pages/BenchmarkPage.js?v=2.1";
import { renderLivePredictorPage } from "./pages/LivePredictorPage.js?v=2.1";

// Global App State
const state = {
  currentPage: "simulator", // Default to simulator if navigated there
  health: null,
  metrics: null,
  metadata: null,
  traces: [],
  sim: {
    selectedTrace: 0,
    selectedPredictor: "xgboost",
    results: null,
    cycleTraces: [],
    cycleIndex: 0,
    isPlaying: false,
    playTimer: null,
    loadedBranches: []
  },
  livePredict: {
    pc: "0x4010a4",
    history: [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0],
    result: null
  }
};

async function initApp() {
  console.log("[PipelineAI v2.1] Booting application...");

  // Load backend data
  try {
    state.health = await ApiService.checkHealth();
    const metricsRes = await ApiService.getMetrics();
    if (metricsRes?.metrics) state.metrics = metricsRes.metrics;

    const metaRes = await ApiService.getMetadata();
    if (metaRes?.metadata) state.metadata = metaRes.metadata;

    const tracesRes = await ApiService.getTraces();
    if (tracesRes?.traces) state.traces = tracesRes.traces;
  } catch (err) {
    console.warn("[PipelineAI] Initial data load warning:", err);
  }

  // Bind navigation globally
  window.appNavigate = navigateTo;
  window.triggerSimRun = triggerSimRun;
  window.triggerSimCompare = triggerSimCompare;
  window.runTraceSim = (traceId) => {
    state.sim.selectedTrace = traceId;
    navigateTo("simulator");
    setTimeout(triggerSimRun, 100);
  };
  window.stepSimCycle = stepSimCycle;
  window.setSimCycle = setSimCycle;
  window.togglePlayPause = togglePlayPause;
  window.resetSimPlayback = resetSimPlayback;
  window.triggerLivePredict = triggerLivePredict;
  window.randomizeLivePc = randomizeLivePc;
  window.setLiveBhrPattern = setLiveBhrPattern;
  window.toggleHistoryBit = toggleHistoryBit;

  render();
}

function navigateTo(page) {
  state.currentPage = page;
  if (state.sim.isPlaying) {
    clearInterval(state.sim.playTimer);
    state.sim.isPlaying = false;
  }
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function render() {
  const root = document.getElementById("app-root");
  if (!root) return;

  const navHtml = `
    <header class="app-header">
      <div class="brand-section">
        <span class="brand-logo">⚡</span>
        <div class="brand-titles">
          <span class="brand-name">PipelineAI</span>
          <span class="brand-sub">CPU Pipeline & Branch Predictor</span>
        </div>
      </div>
      <nav class="nav-links">
        <button class="nav-btn ${state.currentPage === 'dashboard' ? 'active' : ''}" onclick="window.appNavigate('dashboard')">
          📊 Dashboard
        </button>
        <button class="nav-btn ${state.currentPage === 'simulator' ? 'active' : ''}" onclick="window.appNavigate('simulator')">
          ⚡ Pipeline Simulator
        </button>
        <button class="nav-btn ${state.currentPage === 'benchmark' ? 'active' : ''}" onclick="window.appNavigate('benchmark')">
          📈 Model Benchmarks
        </button>
        <button class="nav-btn ${state.currentPage === 'live-predictor' ? 'active' : ''}" onclick="window.appNavigate('live-predictor')">
          🎯 Live Predictor
        </button>
      </nav>
      <div class="header-status">
        <span class="status-dot ${state.health?.status === 'healthy' ? 'online' : 'offline'}"></span>
        <span class="status-text">${state.health?.status === 'healthy' ? 'Engine Ready' : 'Connecting...'}</span>
      </div>
    </header>
  `;

  let pageContent = "";
  switch (state.currentPage) {
    case "dashboard":
      pageContent = renderDashboard(state.metrics, state.traces);
      break;
    case "simulator":
      pageContent = renderSimulatorPage(state.sim);
      break;
    case "benchmark":
      pageContent = renderBenchmarkPage(state.metrics, state.metadata);
      break;
    case "live-predictor":
      pageContent = renderLivePredictorPage(state.livePredict);
      break;
    default:
      pageContent = renderSimulatorPage(state.sim);
  }

  const footerHtml = `
    <footer class="app-footer">
      <div>PipelineAI &copy; 2026 — 5-Stage RISC Microarchitecture Simulator & AI Branch Predictor Platform (v2.1)</div>
      <div class="footer-meta">Dataset: 200,000 Branches (10 Traces) | Models: XGBoost, Perceptron, Gshare, Bimodal</div>
    </footer>
  `;

  root.innerHTML = navHtml + `<main class="main-content">${pageContent}</main>` + footerHtml;

  if (state.currentPage === "live-predictor") {
    document.querySelectorAll(".bit-interactive").forEach(el => {
      el.addEventListener("click", () => {
        const idx = parseInt(el.getAttribute("data-idx"), 10);
        toggleHistoryBit(idx);
      });
    });
  }
}

async function triggerSimRun() {
  const traceId = parseInt(document.getElementById("simTraceSelect")?.value || state.sim.selectedTrace, 10);
  const predictor = document.getElementById("simPredictorSelect")?.value || state.sim.selectedPredictor;
  const limit = parseInt(document.getElementById("simLimitSelect")?.value || "60", 10);
  const penalty = parseInt(document.getElementById("simPenaltySelect")?.value || "2", 10);

  state.sim.selectedTrace = traceId;
  state.sim.selectedPredictor = predictor;

  const btn = document.getElementById("btnRunSim");
  if (btn) {
    btn.innerHTML = "⏳ Simulating...";
    btn.disabled = true;
  }

  try {
    const res = await ApiService.runSimulation(traceId, predictor, limit, penalty);
    if (res?.results) {
      state.sim.results = res.results;
      state.sim.cycleTraces = res.results.cycle_traces || [];
      state.sim.cycleIndex = 0;
    }

    try {
      const branchesRes = await ApiService.getTraceDetails(traceId, limit);
      if (branchesRes?.branches) {
        state.sim.loadedBranches = branchesRes.branches;
      }
    } catch (traceErr) {
      console.warn("Trace detail fetching fallback:", traceErr);
    }
  } catch (err) {
    alert("Simulation notice: " + err.message);
  } finally {
    render();
  }
}

async function triggerSimCompare() {
  const traceId = parseInt(document.getElementById("simTraceSelect")?.value || "0", 10);
  const limit = parseInt(document.getElementById("simLimitSelect")?.value || "100", 10);

  try {
    const res = await ApiService.comparePredictors(traceId, limit);
    if (res?.comparison) {
      let msg = "🏆 Multi-Architecture Comparison Results:\n\n";
      for (const [k, v] of Object.entries(res.comparison)) {
        msg += `${v.predictor.toUpperCase().padEnd(16)}: ${v.total_cycles} cycles | Accuracy: ${(v.accuracy*100).toFixed(1)}% | Speedup: ${v.speedup_vs_baseline}x\n`;
      }
      alert(msg);
    }
  } catch (err) {
    alert("Comparison failed: " + err.message);
  }
}

function stepSimCycle(delta) {
  if (!state.sim.cycleTraces.length) return;
  state.sim.cycleIndex = Math.max(0, Math.min(state.sim.cycleTraces.length - 1, state.sim.cycleIndex + delta));
  render();
}

function setSimCycle(val) {
  state.sim.cycleIndex = parseInt(val, 10);
  render();
}

function togglePlayPause() {
  if (state.sim.isPlaying) {
    clearInterval(state.sim.playTimer);
    state.sim.isPlaying = false;
  } else {
    state.sim.isPlaying = true;
    state.sim.playTimer = setInterval(() => {
      if (state.sim.cycleIndex < state.sim.cycleTraces.length - 1) {
        state.sim.cycleIndex++;
        render();
      } else {
        clearInterval(state.sim.playTimer);
        state.sim.isPlaying = false;
        render();
      }
    }, 400);
  }
  render();
}

function resetSimPlayback() {
  if (state.sim.isPlaying) {
    clearInterval(state.sim.playTimer);
    state.sim.isPlaying = false;
  }
  state.sim.cycleIndex = 0;
  render();
}

async function triggerLivePredict() {
  const pcInput = document.getElementById("livePcInput")?.value || "0x4010a4";
  const predictor = document.getElementById("livePredictorSelect")?.value || "xgboost";

  state.livePredict.pc = pcInput;

  try {
    const res = await ApiService.predictSingle(pcInput, state.livePredict.history, predictor);
    if (res?.status === "success") {
      state.livePredict.result = res;
    }
  } catch (err) {
    alert("Prediction request failed: " + err.message);
  }
  render();
}

function randomizeLivePc() {
  const randomPc = 0x400000 + Math.floor(Math.random() * 0x80000) * 4;
  state.livePredict.pc = "0x" + randomPc.toString(16);
  const input = document.getElementById("livePcInput");
  if (input) input.value = state.livePredict.pc;
}

function toggleHistoryBit(idx) {
  state.livePredict.history[idx] = state.livePredict.history[idx] === 1 ? 0 : 1;
  render();
}

function setLiveBhrPattern(type) {
  switch (type) {
    case "all_taken":
      state.livePredict.history = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1];
      break;
    case "all_not_taken":
      state.livePredict.history = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];
      break;
    case "alternating":
      state.livePredict.history = [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0];
      break;
    case "random":
      state.livePredict.history = Array.from({ length: 16 }, () => (Math.random() > 0.5 ? 1 : 0));
      break;
  }
  render();
}

window.addEventListener("DOMContentLoaded", initApp);
