/**
 * PipelineAI - BranchHistoryViewer Component
 * Visualizes the 16-bit Global Branch History Register (BHR)
 */

export function renderBranchHistoryViewer(bhrList = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], interactive = false) {
  const bitsHtml = bhrList.map((bit, idx) => `
    <div class="bhr-bit-box ${bit === 1 ? 'bit-taken' : 'bit-not-taken'} ${interactive ? 'bit-interactive' : ''}" data-idx="${idx}">
      <span class="bit-val">${bit}</span>
      <span class="bit-label">h${idx + 1}</span>
    </div>
  `).join("");

  return `
    <div class="bhr-container">
      <div class="bhr-header">
        <span class="bhr-title">16-Bit Global Branch History Register (BHR)</span>
        <span class="bhr-hex">Pattern: [ ${bhrList.join("")} ]</span>
      </div>
      <div class="bhr-bits-grid">
        ${bitsHtml}
      </div>
      <div class="bhr-legend">
        <span class="legend-item"><span class="legend-color taken"></span> 1 = Taken</span>
        <span class="legend-item"><span class="legend-color not-taken"></span> 0 = Not Taken</span>
        <span class="legend-hint">Shift direction: ◄ Left (Most recent at h1)</span>
      </div>
    </div>
  `;
}
