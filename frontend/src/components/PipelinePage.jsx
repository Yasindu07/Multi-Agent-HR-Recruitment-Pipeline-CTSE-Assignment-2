import { useState, useEffect, useCallback } from 'react'
import { API } from '../App'
import PipelineFlow from './PipelineFlow'
import { Briefcase, Users, Settings, Rocket, FileText, Target, Brain, Mic, AlertCircle, CheckCircle2, XCircle } from 'lucide-react'

const INITIAL_AGENTS = {
  document_extractor: { status: 'waiting', label: 'Document Extractor', icon: 'FileText', data: null, duration: null },
  candidate_matcher: { status: 'waiting', label: 'Candidate Matcher', icon: 'GitBranch', data: null, duration: null },
  assessment_coordinator: { status: 'waiting', label: 'Assessment Coordinator', icon: 'Brain', data: null, duration: null },
  interview_strategist: { status: 'waiting', label: 'Interview Strategist', icon: 'MessageSquare', data: null, duration: null },
}

function Tags({ items, cls }) {
  if (!items?.length) return null
  return <div>{items.map((s, i) => <span key={i} className={`tag ${cls}`}>{s}</span>)}</div>
}

function ScoreBadge({ score }) {
  const cls = score >= 80 ? 'score-high' : score >= 60 ? 'score-mid' : 'score-low'
  return <div className={`score-badge ${cls}`}>{score}</div>
}

function RecBadge({ rec }) {
  const map = { STRONG_MATCH: 'badge-strong', MODERATE_MATCH: 'badge-moderate', WEAK_MATCH: 'badge-weak', NO_MATCH: 'badge-no', PASS: 'badge-pass', FAIL: 'badge-fail', STRONGLY_RECOMMEND: 'badge-strong', RECOMMEND: 'badge-moderate', PROCEED_WITH_CAUTION: 'badge-weak' }
  return <span className={`status-badge ${map[rec] || 'badge-moderate'}`}>{rec?.replace(/_/g, ' ')}</span>
}

export default function PipelinePage() {
  const [jobs, setJobs] = useState([])
  const [candidates, setCandidates] = useState([])
  const [selectedJob, setSelectedJob] = useState('ALL')
  const [selectedCandidates, setSelectedCandidates] = useState([])
  const [model, setModel] = useState('llama3.2')
  const [useSample, setUseSample] = useState(false)
  const [agents, setAgents] = useState(INITIAL_AGENTS)
  const [running, setRunning] = useState(false)
  const [logs, setLogs] = useState([])
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('flow')

  useEffect(() => {
    fetch(`${API}/api/jobs`).then(r => r.json()).then(d => setJobs(d.jobs || []))
    fetch(`${API}/api/candidates`).then(r => r.json()).then(d => setCandidates(d.candidates || []))
  }, [])

  const toggleCandidate = (id) => {
    setSelectedCandidates(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const runPipeline = useCallback(() => {
    setRunning(true); setError(null); setLogs([]); setAgents(INITIAL_AGENTS); setActiveTab('flow')
    const params = new URLSearchParams({ model, job_id: selectedJob, use_sample: useSample, candidate_ids: selectedCandidates.join(',') })
    const evtSource = new EventSource(`${API}/api/run?${params}`)

    evtSource.addEventListener('pipeline_start', (e) => { const d = JSON.parse(e.data); setLogs(prev => [...prev, `Pipeline #${d.run_id} started — ${d.resume_count} resumes, ${d.flyer_count} flyers`]) })
    evtSource.addEventListener('agent_start', (e) => { const d = JSON.parse(e.data); setAgents(prev => ({ ...prev, [d.agent]: { ...prev[d.agent], status: 'running' } })); setLogs(prev => [...prev, `${d.label} started...`]) })
    evtSource.addEventListener('agent_complete', (e) => { const d = JSON.parse(e.data); setAgents(prev => ({ ...prev, [d.agent]: { ...prev[d.agent], status: 'completed', data: d, duration: d.duration_seconds } })); setLogs(prev => [...prev, `${d.label} completed (${d.duration_seconds}s)`]) })
    evtSource.addEventListener('agent_skipped', (e) => { const d = JSON.parse(e.data); setAgents(prev => ({ ...prev, [d.agent]: { ...prev[d.agent], status: 'skipped' } })) })
    evtSource.addEventListener('agent_error', (e) => { const d = JSON.parse(e.data); setAgents(prev => ({ ...prev, [d.agent]: { ...prev[d.agent], status: 'failed' } })); setError(d.error) })
    evtSource.addEventListener('pipeline_done', () => { setRunning(false); evtSource.close() })
    evtSource.addEventListener('error', (e) => { try { const d = JSON.parse(e.data || '{}'); setError(d.message) } catch {}; setRunning(false); evtSource.close() })
    evtSource.onerror = () => { setRunning(false); evtSource.close() }
  }, [model, selectedJob, selectedCandidates, useSample])

  const hasResults = Object.values(agents).some(a => a.data)
  const ext = agents.document_extractor?.data
  const match = agents.candidate_matcher?.data
  const assess = agents.assessment_coordinator?.data
  const intv = agents.interview_strategist?.data

  return (
    <div>
      <div className="pipeline-config">
        <div className="config-section">
          <h3><Briefcase size={16} /> Select Job</h3>
          <select value={selectedJob} onChange={e => setSelectedJob(e.target.value)} disabled={running}>
            <option value="ALL">All Open Jobs</option>
            {jobs.filter(j => j.status === 'OPEN').map(j => (<option key={j.job_id} value={j.job_id}>{j.job_id} — {j.title}</option>))}
          </select>
        </div>
        <div className="config-section">
          <h3><Users size={16} /> Select Candidates</h3>
          {candidates.length > 0 ? (
            <div className="candidate-checklist">
              {candidates.map(c => (
                <label key={c.id} className="check-item">
                  <input type="checkbox" checked={selectedCandidates.includes(c.id)} onChange={() => toggleCandidate(c.id)} disabled={running} />
                  <span>{c.name}</span>
                  <span className="check-meta">{(c.skills || []).length} skills, {c.years_of_experience}y exp</span>
                </label>
              ))}
            </div>
          ) : (
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>No candidates in database. Add some first or enable sample data.</p>
          )}
        </div>
        <div className="config-section">
          <h3><Settings size={16} /> Settings</h3>
          <div className="setting-row">
            <label>Model:</label>
            <select value={model} onChange={e => setModel(e.target.value)} disabled={running}>
              <option value="llama3.2">llama3.2</option><option value="llama3:8b">llama3:8b</option>
              <option value="mistral">mistral</option><option value="phi3">phi3</option>
            </select>
          </div>
          <label className="check-item" style={{ marginTop: '0.5rem' }}>
            <input type="checkbox" checked={useSample} onChange={e => setUseSample(e.target.checked)} disabled={running} />
            <span>Include sample data</span>
          </label>
        </div>
      </div>

      <button className="btn-run-large" onClick={runPipeline} disabled={running || (!useSample && selectedCandidates.length === 0)}>
        {running ? <><span className="spinner" /> Pipeline Running...</> : <><Rocket size={18} style={{ marginRight: '0.4rem' }} /> Run Pipeline</>}
      </button>

      {error && <div className="result-card" style={{ borderColor: 'var(--danger)', background: 'var(--danger-bg)', marginTop: '1rem' }}><p style={{ color: 'var(--danger)' }}><AlertCircle size={15} style={{ verticalAlign: 'middle', marginRight: '0.3rem' }} />{error}</p></div>}

      <PipelineFlow agents={agents} />

      {hasResults && (
        <div className="tabs" style={{ marginTop: '1rem' }}>
          <div className="tab-list">
            {[
              { key: 'flow', label: 'Extracted', icon: FileText },
              { key: 'matches', label: 'Matches', icon: Target },
              { key: 'assess', label: 'Assessments', icon: Brain },
              { key: 'guides', label: 'Guides', icon: Mic },
            ].map(t => {
              const Icon = t.icon
              return (
                <button key={t.key} className={`tab-btn ${activeTab === t.key ? 'active' : ''}`} onClick={() => setActiveTab(t.key)}>
                  <Icon size={14} style={{ marginRight: '0.3rem', verticalAlign: 'middle' }} />{t.label}
                </button>
              )
            })}
          </div>

          {activeTab === 'flow' && ext && (
            <div className="card-grid">
              <div>
                <h3 style={{ marginBottom: '0.75rem' }}>Profiles ({ext.profiles?.length})</h3>
                {ext.profiles?.map((p, i) => (
                  <div key={i} className="result-card">
                    <h3>{p.candidate_name}</h3>
                    <div className="detail-row"><span className="detail-label">Experience</span><span className="detail-value">{p.years_of_experience} years</span></div>
                    <Tags items={p.skills} cls="tag-skill" />
                  </div>
                ))}
              </div>
              <div>
                <h3 style={{ marginBottom: '0.75rem' }}>Vacancies ({ext.vacancies?.length})</h3>
                {ext.vacancies?.map((v, i) => (
                  <div key={i} className="result-card">
                    <h3>{v.title}</h3>
                    <div className="detail-row"><span className="detail-label">Dept</span><span className="detail-value">{v.department}</span></div>
                    <Tags items={v.required_skills} cls="tag-skill" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'matches' && match && (
            <div>
              {match.shortlisted?.map((s, i) => {
                const m = s.best_match || {}
                return (
                  <div key={i} className="result-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div><h3><CheckCircle2 size={16} color="var(--success)" /> {m.candidate_name} → {m.job_title}</h3><RecBadge rec={m.recommendation} /></div>
                      <ScoreBadge score={m.overall_match_score} />
                    </div>
                    <div className="detail-row"><span className="detail-label">Skill Match</span><span className="detail-value">{m.skill_match?.skill_match_percentage}%</span></div>
                    <Tags items={m.skill_match?.matched_skills} cls="tag-match" />
                    {m.skill_match?.missing_skills?.length > 0 && <><div style={{ marginTop: '0.5rem', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)' }}>Missing</div><Tags items={m.skill_match.missing_skills} cls="tag-missing" /></>}
                    <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.5rem', fontStyle: 'italic' }}>{m.reasoning}</p>
                  </div>
                )
              })}
              {match.rejected?.map((r, i) => (
                <div key={i} className="result-card" style={{ borderLeftColor: 'var(--danger)', borderLeftWidth: 4 }}>
                  <strong><XCircle size={14} color="var(--danger)" style={{ verticalAlign: 'middle', marginRight: '0.3rem' }} />{r.candidate_profile?.candidate_name}</strong> — Score: {r.best_score}/100 — {r.rejection_reason}
                </div>
              ))}
            </div>
          )}

          {activeTab === 'assess' && assess && (
            <div className="card-grid">
              {assess.results?.map((r, i) => (
                <div key={i} className="result-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <div><h3>{r.candidate_name}</h3><RecBadge rec={r.pass_status} /></div>
                    <ScoreBadge score={Math.round(r.percentage)} />
                  </div>
                  <div className="detail-row"><span className="detail-label">Score</span><span className="detail-value">{r.total_score}/{r.max_score}</span></div>
                  {r.section_scores?.map((s, j) => (
                    <div key={j} style={{ margin: '0.25rem 0' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}><span>{s.section}</span><span>{s.percentage?.toFixed(0)}%</span></div>
                      <div className="progress-bar"><div className="progress-fill" style={{ width: `${s.percentage}%` }} /></div>
                    </div>
                  ))}
                  {r.questions?.length > 0 && (
                    <div style={{ marginTop: '1.5rem' }}>
                      <h4 style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text)' }}>Generated Questions & Simulated Answers:</h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {r.questions.map((q, qIndex) => {
                          const userAnswer = r.answers?.[q.question_id] || 'No answer provided';
                          const isCorrect = q.question_type === 'MCQ' ? String(userAnswer).trim().toLowerCase() === String(q.correct_answer).trim().toLowerCase() : true;
                          return (
                            <div key={qIndex} style={{ padding: '0.75rem', backgroundColor: 'var(--surface-50)', borderRadius: '0.5rem', border: '1px solid var(--border)' }}>
                              <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.25rem' }}>Q{qIndex + 1}: {q.question_text}</div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                <span style={{ fontWeight: 500 }}>Type:</span> {q.question_type} &nbsp;|&nbsp; <span style={{ fontWeight: 500 }}>Skill:</span> {q.skill_tested}
                              </div>
                              {q.options && q.options.length > 0 && (
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem', marginLeft: '0.5rem' }}>
                                  {q.options.map((opt, oIdx) => <div key={oIdx}>{opt}</div>)}
                                </div>
                              )}
                              <div style={{ fontSize: '0.8rem', fontWeight: 500, color: isCorrect ? 'var(--success)' : 'var(--danger)', marginTop: '0.5rem' }}>
                                Candidate Answer: {userAnswer}
                              </div>
                              {q.question_type === 'MCQ' && !isCorrect && (
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                                  Correct Answer: {q.correct_answer}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {activeTab === 'guides' && intv && (
            <div>
              {intv.guides?.map((g, i) => (
                <div key={i} className="result-card" style={{ marginBottom: '1.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div><h3><Mic size={16} /> {g.candidate_name} → {g.job_title}</h3><RecBadge rec={g.recommendation} /></div>
                    <div style={{ display: 'flex', gap: '1rem', textAlign: 'center' }}>
                      <div><div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--primary)' }}>{g.match_score}</div><div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Match</div></div>
                      <div><div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--purple)' }}>{g.assessment_score?.toFixed(0)}%</div><div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Assess</div></div>
                    </div>
                  </div>
                  {g.content && <div className="markdown-content" dangerouslySetInnerHTML={{ __html: simpleMarkdown(g.content) }} />}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function simpleMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/^### (.+)$/gm, '<h3>$1</h3>').replace(/^## (.+)$/gm, '<h2>$1</h2>').replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li>$1</li>').replace(/\n\n/g, '<br/><br/>').replace(/\n/g, '<br/>')
}
