import { useState, useEffect } from 'react'
import { API } from '../App'
import { Briefcase, Users, Rocket, CheckCircle2, Target, ClipboardList, FileText, GitBranch, Brain, MessageSquare } from 'lucide-react'

export default function DashboardPage() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch(`${API}/api/dashboard`).then(r => r.json()).then(setStats).catch(() => {})
  }, [])

  if (!stats) return <div className="loading-state"><span className="spinner" /> Loading dashboard...</div>

  const cards = [
    { label: 'Open Jobs', value: stats.open_jobs, icon: Briefcase, color: 'var(--primary)' },
    { label: 'Total Candidates', value: stats.total_candidates, icon: Users, color: 'var(--info)' },
    { label: 'Pipeline Runs', value: stats.completed_runs, icon: Rocket, color: 'var(--purple)' },
    { label: 'Shortlisted', value: stats.shortlisted, icon: CheckCircle2, color: 'var(--success)' },
    { label: 'Total Matches', value: stats.total_matches, icon: Target, color: 'var(--warning)' },
    { label: 'Total Jobs', value: stats.total_jobs, icon: ClipboardList, color: 'var(--text-secondary)' },
  ]

  const agentInfo = [
    { icon: FileText, title: 'Document Extractor', desc: 'Parses CVs & Flyers into structured JSON', color: 'var(--info)' },
    { icon: GitBranch, title: 'Candidate Matcher', desc: 'Scores candidates against vacancies', color: 'var(--purple)' },
    { icon: Brain, title: 'Assessment Coordinator', desc: 'Generates quizzes & auto-grades', color: 'var(--success)' },
    { icon: MessageSquare, title: 'Interview Strategist', desc: 'Creates interview guides & reports', color: 'var(--warning)' },
  ]

  return (
    <div>
      <div className="metrics-grid">
        {cards.map(c => {
          const Icon = c.icon
          return (
            <div key={c.label} className="metric-card">
              <div style={{ marginBottom: '0.25rem' }}><Icon size={22} color={c.color} /></div>
              <div className="metric-value" style={{ color: c.color }}>{c.value}</div>
              <div className="metric-label">{c.label}</div>
            </div>
          )
        })}
      </div>

      <div className="result-card">
        <h3><Rocket size={18} /> Recent Pipeline Runs</h3>
        {stats.recent_runs?.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr><th>ID</th><th>Job</th><th>Model</th><th>Status</th><th>Date</th></tr>
            </thead>
            <tbody>
              {stats.recent_runs.map(r => (
                <tr key={r.id}>
                  <td>#{r.id}</td>
                  <td>{r.job_id || 'ALL'}</td>
                  <td><code>{r.model}</code></td>
                  <td><span className={`status-badge ${r.status === 'COMPLETED' ? 'badge-pass' : r.status === 'RUNNING' ? 'badge-moderate' : 'badge-fail'}`}>{r.status}</span></td>
                  <td>{new Date(r.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No pipeline runs yet. Go to "Run Pipeline" to start.</p>
        )}
      </div>

      <div className="result-card" style={{ marginTop: '1rem' }}>
        <h3><GitBranch size={18} /> System Architecture</h3>
        <div className="arch-grid">
          {agentInfo.map(a => {
            const Icon = a.icon
            return (
              <div key={a.title} className="arch-card">
                <Icon size={24} color={a.color} />
                <strong>{a.title}</strong>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{a.desc}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
