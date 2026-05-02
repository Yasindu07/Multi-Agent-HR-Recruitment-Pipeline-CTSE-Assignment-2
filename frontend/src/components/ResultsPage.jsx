import { useState, useEffect } from 'react'
import { API } from '../App'
import { ArrowLeft, Eye, ClipboardList, Target, Calendar, Cpu, CheckCircle2, XCircle, Users, Briefcase, FileText } from 'lucide-react'

export default function ResultsPage() {
  const [runs, setRuns] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    fetch(`${API}/api/results`).then(r => r.json()).then(d => setRuns(d.runs || []))
  }, [])

  const viewRun = async (id) => {
    setSelected(id)
    const res = await fetch(`${API}/api/results/${id}`)
    const data = await res.json()
    setDetail(data)
  }

  if (detail) {
    const run = detail.run
    const results = typeof run.results === 'string' ? JSON.parse(run.results) : run.results
    return (
      <div>
        <button className="btn-secondary" onClick={() => { setDetail(null); setSelected(null) }}><ArrowLeft size={15} style={{ marginRight: '0.3rem' }} />Back to List</button>
        <div className="result-card" style={{ marginTop: '1rem' }}>
          <h3>Pipeline Run #{run.id}</h3>
          <div className="detail-row"><span className="detail-label">Job</span><span className="detail-value">{run.job_id || 'ALL'}</span></div>
          <div className="detail-row"><span className="detail-label">Model</span><span className="detail-value"><code>{run.model}</code></span></div>
          <div className="detail-row"><span className="detail-label">Status</span><span className="detail-value"><span className={`status-badge ${run.status === 'COMPLETED' ? 'badge-pass' : 'badge-fail'}`}>{run.status}</span></span></div>
          <div className="detail-row"><span className="detail-label">Created</span><span className="detail-value">{new Date(run.created_at).toLocaleString()}</span></div>
          {run.completed_at && <div className="detail-row"><span className="detail-label">Completed</span><span className="detail-value">{new Date(run.completed_at).toLocaleString()}</span></div>}

          {results && (
            <div className="metrics-grid" style={{ marginTop: '1rem' }}>
              {[
                { label: 'Profiles', value: results.profiles_count, icon: FileText, color: 'var(--primary)' },
                { label: 'Shortlisted', value: results.shortlisted_count, icon: CheckCircle2, color: 'var(--success)' },
                { label: 'Rejected', value: results.rejected_count, icon: XCircle, color: 'var(--danger)' },
                { label: 'Assessments', value: results.assessments_count, icon: Users, color: 'var(--purple)' },
                { label: 'Guides', value: results.guides_count, icon: Briefcase, color: 'var(--warning)' },
              ].map(m => {
                const Icon = m.icon
                return (
                  <div key={m.label} className="metric-card">
                    <Icon size={18} color={m.color} />
                    <div className="metric-value" style={{ color: m.color }}>{m.value ?? '—'}</div>
                    <div className="metric-label">{m.label}</div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {detail.matches?.length > 0 && (
          <div className="result-card" style={{ marginTop: '1rem' }}>
            <h3><Target size={18} /> Match Results</h3>
            <table className="data-table">
              <thead><tr><th>Candidate</th><th>Job</th><th>Score</th><th>Recommendation</th><th>Assessment</th></tr></thead>
              <tbody>
                {detail.matches.map(m => (
                  <tr key={m.id}>
                    <td>{m.candidate_name || `#${m.candidate_id}`}</td>
                    <td>{m.job_title || m.job_id}</td>
                    <td><strong>{m.match_score}/100</strong></td>
                    <td><span className={`status-badge ${m.recommendation?.includes('STRONG') ? 'badge-strong' : m.recommendation?.includes('MODERATE') ? 'badge-moderate' : 'badge-weak'}`}>{m.recommendation?.replace(/_/g, ' ')}</span></td>
                    <td>{m.assessment_score ? `${m.assessment_score.toFixed(1)}%` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      {runs.length > 0 ? (
        <table className="data-table">
          <thead><tr><th>Run ID</th><th>Job</th><th>Model</th><th>Status</th><th>Date</th><th>Actions</th></tr></thead>
          <tbody>
            {runs.map(r => (
              <tr key={r.id}>
                <td>#{r.id}</td>
                <td>{r.job_title || r.job_id || 'ALL'}</td>
                <td><code>{r.model}</code></td>
                <td><span className={`status-badge ${r.status === 'COMPLETED' ? 'badge-pass' : r.status === 'RUNNING' ? 'badge-moderate' : 'badge-fail'}`}>{r.status}</span></td>
                <td>{new Date(r.created_at).toLocaleString()}</td>
                <td><button className="btn-sm" onClick={() => viewRun(r.id)}><Eye size={13} style={{ marginRight: '0.2rem' }} />View</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="empty-state">
          <ClipboardList size={48} color="var(--text-muted)" />
          <h3>No pipeline runs yet</h3>
          <p>Go to "Run Pipeline" to execute the AI recruitment pipeline</p>
        </div>
      )}
    </div>
  )
}
