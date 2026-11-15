/**
 * PipelineAI - PipelineStages Component
 * Visualizes the 5-Stage RISC Pipeline (IF, ID, EX, MEM, WB)
 * with animated instruction packets and flush/stall alerts.
 */

export function renderPipelineStages(stagesData = null, isFlush = false) {
  const stageDefs = [
    { key: "IF", label: "Instruction Fetch", desc: "Fetch PC & Predict Branch" },
    { key: "ID", label: "Instruction Decode", desc: "Decode & Read Regs" },
    { key: "EX", label: "Execute", desc: "ALU & Branch Resolution" },
    { key: "MEM", label: "Memory Access", desc: "Data Read / Write" },
    { key: "WB", label: "Write Back", desc: "Commit & Retire" }
  ];

  const stageCards = stageDefs.map(def => {
    const stage = stagesData ? stagesData[def.key] : null;
    const isBubble = !stage || stage.is_bubble || !stage.instruction;
    const instr = stage ? stage.instruction : null;

    let statusClass = isBubble ? "stage-bubble" : "stage-active";
    let statusText = isBubble ? "NOP / Bubble" : "Active";

    if (isFlush && (def.key === "IF" || def.key === "ID")) {
      statusClass = "stage-flushed";
      statusText = "💥 Squashed (Flush)";
    }

    return `
      <div class="pipeline-stage-box ${statusClass}">
        <div class="stage-tag">${def.key}</div>
        <div class="stage-name">${def.label}</div>
        <div class="stage-content">
          ${!isBubble && instr ? `
            <div class="instr-badge">
              <span class="instr-pc">${instr.pc_hex || `0x${instr.pc?.toString(16)}`}</span>
              <span class="instr-op">${instr.opcode || "BRANCH"}</span>
            </div>
            <div class="instr-meta">
              <span>Pred: <strong>${instr.predicted_taken ? "T" : "NT"}</strong></span>
              <span>Act: <strong>${instr.actual_taken ? "T" : "NT"}</strong></span>
            </div>
          ` : `
            <div class="bubble-placeholder">${statusText}</div>
          `}
        </div>
        <div class="stage-desc">${def.desc}</div>
      </div>
    `;
  }).join('<div class="stage-arrow">➔</div>');

  return `
    <div class="pipeline-stages-container ${isFlush ? 'pipeline-flush-alert' : ''}">
      ${stageCards}
    </div>
  `;
}
