/**
 * PipelineAI - Benchmark & Model Comparison Page
 * Comparative charts, accuracy, MPKI, and feature importance rankings.
 */

export function renderBenchmarkPage(metrics = {}, metadata = {}) {
  const models = Object.values(metrics);
  const featureImp = metadata.feature_importance || [];

  return `
    <div class="page-benchmark">
      <div class="hero-banner">
        <div class="hero-text">
          <h2>Branch Predictor Benchmark Suite</h2>
          <p>
            Evaluated on 30,000 unseen test set branches from real execution traces.
            Comparing hardware heuristics (Bimodal, Gshare), neural perceptrons, and gradient boosting (XGBoost).
          </p>
        </div>
      </div>

      <!-- Comparative Leaderboard Table -->
      <div class="panel-section">
        <div class="panel-title">
          <h3>🏆 Model Performance Leaderboard</h3>
          <span class="badge badge-primary">Test Set (30,000 Branches)</span>
        </div>
        <div class="table-scroll">
          <table class="data-table leaderboard-table">
            <thead>
              <tr>
                <th>Predictor Model</th>
                <th>Accuracy</th>
                <th>Misprediction Rate</th>
                <th>MPKI (Branches)</th>
                <th>Precision</th>
                <th>Recall</th>
                <th>F1 Score</th>
                <th>Latency (ms)</th>
              </tr>
            </thead>
            <tbody>
              ${models.map(m => `
                <tr class="${m.model_name.includes('XGBoost') || m.model_name.includes('Perceptron') ? 'highlight-row' : ''}">
                  <td><strong>${m.model_name}</strong></td>
                  <td><span class="badge badge-success">${(m.accuracy * 100).toFixed(2)}%</span></td>
                  <td>${(m.misprediction_rate * 100).toFixed(2)}%</td>
                  <td><strong>${m.mpki}</strong></td>
                  <td>${m.precision}</td>
                  <td>${m.recall}</td>
                  <td><strong>${m.f1}</strong></td>
                  <td>${m.inference_latency_ms} ms</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>

      <!-- Graphical Accuracy & MPKI Comparison Bars -->
      <div class="charts-grid">
        <div class="chart-card">
          <h4>🎯 Prediction Accuracy (%) — Higher is Better</h4>
          <div class="bar-chart">
            ${models.map(m => {
              const pct = (m.accuracy * 100).toFixed(1);
              return `
                <div class="bar-item">
                  <div class="bar-label">${m.model_name.split(" ")[0]}</div>
                  <div class="bar-track">
                    <div class="bar-fill accuracy-fill" style="width: ${pct}%"></div>
                  </div>
                  <div class="bar-val">${pct}%</div>
                </div>
              `;
            }).join("")}
          </div>
        </div>

        <div class="chart-card">
          <h4>⚡ Mispredictions Per Kilo-Instructions (MPKI) — Lower is Better</h4>
          <div class="bar-chart">
            ${models.map(m => {
              const maxMpki = 60;
              const fillPct = Math.min(100, (m.mpki / maxMpki) * 100);
              return `
                <div class="bar-item">
                  <div class="bar-label">${m.model_name.split(" ")[0]}</div>
                  <div class="bar-track">
                    <div class="bar-fill mpki-fill" style="width: ${fillPct}%"></div>
                  </div>
                  <div class="bar-val">${m.mpki}</div>
                </div>
              `;
            }).join("")}
          </div>
        </div>
      </div>

      <!-- Feature Importance Rankings -->
      <div class="panel-section">
        <div class="panel-title">
          <h3>🔍 XGBoost Feature Importance (BHR & PC Modulo)</h3>
          <span class="badge badge-info">17 Extracted Microarchitectural Features</span>
        </div>
        <p class="section-desc">
          Shows how heavily the gradient boosted tree relies on recent branch history bits (h1 = immediately prior branch outcome)
          versus earlier history bits and hashed Program Counter (pc_idx).
        </p>
        <div class="features-list">
          ${featureImp.slice(0, 10).map((f, i) => `
            <div class="feature-bar-item">
              <span class="feat-rank">#${i + 1}</span>
              <span class="feat-name"><code>${f.feature}</code> (${f.feature.startsWith('h') ? `History t-${f.feature.slice(1)}` : 'PC Hash'})</span>
              <div class="feat-track">
                <div class="feat-fill" style="width: ${Math.round(f.importance * 350)}%"></div>
              </div>
              <span class="feat-score">${(f.importance * 100).toFixed(2)}%</span>
            </div>
          `).join("")}
        </div>
      </div>
    </div>
  `;
}
