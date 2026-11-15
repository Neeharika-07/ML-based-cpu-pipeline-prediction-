/**
 * PipelineAI - TraceTable Component
 * Displays branch trace data records with status chips and PC indexing.
 */

export function renderTraceTable(branches = [], title = "Trace Branches") {
  if (!branches || branches.length === 0) {
    return `<div class="empty-state">No trace branch records loaded.</div>`;
  }

  const rows = branches.map((b, i) => {
    const isTaken = (b.taken === 1 || b.label === 1);
    const pcVal = b.pc || 0;
    const pcHex = b.pc_hex || `0x${Number(pcVal).toString(16)}`;
    const pcIdx = b.pc_idx !== undefined ? b.pc_idx : (Number(pcVal) % 4096);

    return `
      <tr>
        <td>#${b.branch_index !== undefined ? b.branch_index : i + 1}</td>
        <td><code>${pcHex}</code></td>
        <td><span class="badge-pc">${pcIdx}</span></td>
        <td>
          <span class="outcome-badge ${isTaken ? 'badge-taken' : 'badge-not-taken'}">
            ${isTaken ? 'TAKEN (1)' : 'NOT TAKEN (0)'}
          </span>
        </td>
      </tr>
    `;
  }).join("");

  return `
    <div class="trace-table-container">
      <div class="table-header">
        <h4>${title} (${branches.length} records)</h4>
      </div>
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>Branch Index</th>
              <th>Program Counter (PC)</th>
              <th>PC Index (Hash)</th>
              <th>Branch Outcome</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    </div>
  `;
}
