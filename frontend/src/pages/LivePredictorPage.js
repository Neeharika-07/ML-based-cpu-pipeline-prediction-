/**
 * PipelineAI - Live Predictor Interactive Page
 * Allows users to manually test branch address and history bit combinations.
 */

import { renderBranchHistoryViewer } from "../components/BranchHistoryViewer.js";

export function renderLivePredictorPage(predState = {}) {
  const result = predState.result;
  const currentHistory = predState.history || [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0];

  return `
    <div class="page-live-predictor">
      <div class="hero-banner">
        <div class="hero-text">
          <h2>Interactive Branch Predictor Console</h2>
          <p>
            Test real-time branch speculative predictions. Input any 64-bit Program Counter (PC) address
            and toggle the 16-bit Global Branch History register to see immediate ML inference.
          </p>
        </div>
      </div>

      <div class="predictor-workspace">
        <div class="card predictor-input-card">
          <div class="card-header">
            <h4>⚙️ Branch Instruction Configuration</h4>
          </div>
          <div class="card-body">
            <div class="form-group">
              <label>Program Counter (PC) Address:</label>
              <div class="input-group">
                <input type="text" id="livePcInput" class="form-control"
                       value="${predState.pc || '0x4010a4'}" placeholder="e.g. 0x4010a4 or 4198564">
                <button class="btn btn-outline" onclick="window.randomizeLivePc()">🎲 Random PC</button>
              </div>
              <small class="text-muted">Will be hashed modulo 4096 (ASLR invariant predictor index)</small>
            </div>

            <div class="form-group">
              <label>Predictor Architecture Engine:</label>
              <select id="livePredictorSelect" class="form-select">
                <option value="xgboost">🤖 XGBoost Classifier (PipelineAI Flagship)</option>
                <option value="perceptron">🧠 Jiménez-Lin Perceptron (Neural)</option>
                <option value="gshare">⚙️ Gshare (PC ⊕ BHR Hash)</option>
                <option value="bimodal">🔢 Bimodal (2-Bit Saturating Counter)</option>
              </select>
            </div>

            <div class="form-group">
              <label>16-Bit Global Branch History (BHR):</label>
              <p class="text-muted">Click any bit below to toggle its state (1 = Taken, 0 = Not Taken):</p>
              ${renderBranchHistoryViewer(currentHistory, true)}
              <div class="bhr-actions" style="margin-top: 10px;">
                <button class="btn btn-sm btn-outline" onclick="window.setLiveBhrPattern('all_taken')">All Taken (1s)</button>
                <button class="btn btn-sm btn-outline" onclick="window.setLiveBhrPattern('all_not_taken')">All Not Taken (0s)</button>
                <button class="btn btn-sm btn-outline" onclick="window.setLiveBhrPattern('alternating')">Alternating (1010...)</button>
                <button class="btn btn-sm btn-outline" onclick="window.setLiveBhrPattern('random')">🎲 Random</button>
              </div>
            </div>

            <button class="btn btn-primary btn-block" onclick="window.triggerLivePredict()">
              ⚡ Run Speculative Branch Prediction
            </button>
          </div>
        </div>

        <!-- Prediction Result Display -->
        <div class="card predictor-result-card">
          <div class="card-header">
            <h4>🎯 Speculative Inference Output</h4>
          </div>
          <div class="card-body">
            ${result ? `
              <div class="result-banner ${result.prediction === 1 ? 'result-taken' : 'result-not-taken'}">
                <div class="result-tag">${result.prediction === 1 ? 'BRANCH TAKEN (1)' : 'BRANCH NOT TAKEN (0)'}</div>
                <div class="result-label">Speculative Target Path Selected</div>
                <div class="result-confidence">
                  Model Confidence: <strong>${(result.confidence * 100).toFixed(1)}%</strong>
                </div>
              </div>

              <div class="result-details">
                <div class="detail-row">
                  <span>Input PC:</span>
                  <code>${result.pc_hex} (${result.pc})</code>
                </div>
                <div class="detail-row">
                  <span>PC Index (PC % 4096):</span>
                  <strong>${result.pc_idx}</strong>
                </div>
                <div class="detail-row">
                  <span>Engine Used:</span>
                  <strong>${result.predictor.toUpperCase()}</strong>
                </div>
                <div class="detail-row">
                  <span>BHR History Used:</span>
                  <code>${result.history_str}</code>
                </div>
                <div class="detail-row">
                  <span>Pipeline Action:</span>
                  <em>${result.prediction === 1 ? 'Fetch target branch address into IF stage.' : 'Continue fetching fall-through PC+4 into IF stage.'}</em>
                </div>
              </div>
            ` : `
              <div class="empty-state">
                <div class="empty-icon">💡</div>
                <p>Configure PC and History above and click <strong>Run Speculative Branch Prediction</strong> to test live inference.</p>
              </div>
            `}
          </div>
        </div>
      </div>
    </div>
  `;
}
