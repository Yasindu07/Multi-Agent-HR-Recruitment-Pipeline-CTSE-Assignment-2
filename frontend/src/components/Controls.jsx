export default function Controls({ model, setModel, jobId, setJobId, useSample, setUseSample, onRun, running }) {
  return (
    <div className="controls-bar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Model:</span>
        <select value={model} onChange={e => setModel(e.target.value)} disabled={running}>
          <option value="llama3.2">llama3.2</option>
          <option value="llama3:8b">llama3:8b</option>
          <option value="phi3">phi3</option>
          <option value="mistral">mistral</option>
        </select>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Job:</span>
        <select value={jobId} onChange={e => setJobId(e.target.value)} disabled={running}>
          <option value="ALL">All Open Jobs</option>
          <option value="JOB-001">JOB-001 — Senior Full-Stack Developer</option>
          <option value="JOB-002">JOB-002 — Data Scientist</option>
          <option value="JOB-003">JOB-003 — DevOps Engineer</option>
          <option value="JOB-004">JOB-004 — Junior Mobile Developer</option>
          <option value="JOB-005">JOB-005 — ML Engineer</option>
        </select>
      </div>
      <label>
        <input type="checkbox" checked={useSample} onChange={e => setUseSample(e.target.checked)} disabled={running} />
        Use sample data
      </label>
      <button className="btn-run" onClick={onRun} disabled={running}>
        {running ? <><span className="spinner" /> Running...</> : '🚀 Run Pipeline'}
      </button>
    </div>
  )
}
