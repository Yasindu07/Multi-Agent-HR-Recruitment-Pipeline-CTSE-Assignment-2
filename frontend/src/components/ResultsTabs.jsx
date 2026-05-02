import { useState } from 'react'

function ScoreBadge({ score }) {
  const cls = score >= 80 ? 'score-high' : score >= 60 ? 'score-mid' : 'score-low'
  return <div className={`score-badge ${cls}`}>{score}</div>
}

function RecBadge({ rec }) {
  const map = { STRONG_MATCH: 'badge-strong', MODERATE_MATCH: 'badge-moderate', WEAK_MATCH: 'badge-weak', NO_MATCH: 'badge-no', PASS: 'badge-pass', FAIL: 'badge-fail', STRONGLY_RECOMMEND: 'badge-strong', RECOMMEND: 'badge-moderate', PROCEED_WITH_CAUTION: 'badge-weak' }
  return <span className={`status-badge ${map[rec] || 'badge-moderate'}`}>{rec?.replace(/_/g, ' ')}</span>
}

function Tags({ items, cls }) {
  if (!items?.length) return null
  return <div>{items.map((s, i) => <span key={i} className={`tag ${cls}`}>{s}</span>)}</div>
}

/* ── Tab 1: Extracted Data ─────────────────── */
function ExtractedTab({ data }) {
  if (!data) return <p style={{ color: 'var(--text-muted)' }}>Waiting for Agent 1 to complete...</p>
  return (
    <div className="card-grid">
      <div>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>👤 Candidate Profiles ({data.profiles?.length || 0})</h3>
        {data.profiles?.map((p, i) => (
          <div key={i} className="result-card">
            <h3>{p.candidate_name || 'Unknown'}</h3>
            <div className="detail-row"><span className="detail-label">Email</span><span className="detail-value">{p.email || 'N/A'}</span></div>
            <div className="detail-row"><span className="detail-label">Experience</span><span className="detail-value">{p.years_of_experience || 0} years</span></div>
            <div className="detail-row"><span className="detail-label">Phone</span><span className="detail-value">{p.phone || 'N/A'}</span></div>
            <div style={{ margin: '0.75rem 0 0.25rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Skills</div>
            <Tags items={p.skills} cls="tag-skill" />
            {p.education?.length > 0 && (
              <>
                <div style={{ margin: '0.75rem 0 0.25rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Education</div>
                {p.education.map((e, j) => <div key={j} style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>• {e.degree} — {e.institution} ({e.year})</div>)}
              </>
            )}
          </div>
        ))}
      </div>
      <div>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>💼 Job Vacancies ({data.vacancies?.length || 0})</h3>
        {data.vacancies?.map((v, i) => (
          <div key={i} className="result-card">
            <h3>{v.title || 'Unknown'}</h3>
            <div className="detail-row"><span className="detail-label">Job ID</span><span className="detail-value">{v.job_id}</span></div>
            <div className="detail-row"><span className="detail-label">Department</span><span className="detail-value">{v.department || 'N/A'}</span></div>
            <div className="detail-row"><span className="detail-label">Min Experience</span><span className="detail-value">{v.min_experience_years}+ years</span></div>
            <div style={{ margin: '0.75rem 0 0.25rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Required Skills</div>
            <Tags items={v.required_skills} cls="tag-skill" />
          </div>
        ))}
        {data.errors?.length > 0 && (
          <div className="result-card" style={{ borderColor: 'var(--danger)' }}>
            <h3>⚠️ Parse Errors</h3>
            {data.errors.map((e, i) => <div key={i} style={{ fontSize: '0.82rem', color: 'var(--danger)' }}>• {e.error}</div>)}
          </div>
        )}
      </div>
    </div>
  )
}

/* ── Tab 2: Match Results ──────────────────── */
function MatchTab({ data }) {
  if (!data) return <p style={{ color: 'var(--text-muted)' }}>Waiting for Agent 2 to complete...</p>
  return (
    <div>
      {data.shortlisted?.length > 0 && (
        <>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>✅ Shortlisted Candidates</h3>
          <div className="card-grid">
            {data.shortlisted.map((s, i) => {
              const m = s.best_match || {}
              return (
                <div key={i} className="result-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                    <div>
                      <h3 style={{ marginBottom: '0.25rem' }}>{m.candidate_name} → {m.job_title}</h3>
                      <RecBadge rec={m.recommendation} />
                    </div>
                    <ScoreBadge score={m.overall_match_score} />
                  </div>
                  <div className="detail-row"><span className="detail-label">Skill Match</span><span className="detail-value">{m.skill_match?.skill_match_percentage}%</span></div>
                  <div className="detail-row"><span className="detail-label">Experience Score</span><span className="detail-value">{m.experience_match?.experience_score}/100</span></div>
                  <div style={{ margin: '0.5rem 0 0.25rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Matched Skills</div>
                  <Tags items={m.skill_match?.matched_skills} cls="tag-match" />
                  {m.skill_match?.missing_skills?.length > 0 && (
                    <>
                      <div style={{ margin: '0.5rem 0 0.25rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Missing Skills</div>
                      <Tags items={m.skill_match?.missing_skills} cls="tag-missing" />
                    </>
                  )}
                  {m.skill_match?.bonus_skills?.length > 0 && (
                    <>
                      <div style={{ margin: '0.5rem 0 0.25rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Bonus Skills</div>
                      <Tags items={m.skill_match?.bonus_skills} cls="tag-bonus" />
                    </>
                  )}
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginTop: '0.75rem', fontStyle: 'italic' }}>{m.reasoning}</p>
                </div>
              )
            })}
          </div>
        </>
      )}
      {data.rejected?.length > 0 && (
        <>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '1.5rem 0 0.75rem' }}>❌ Rejected Candidates</h3>
          {data.rejected.map((r, i) => (
            <div key={i} className="result-card" style={{ borderColor: 'var(--danger)', borderLeftWidth: 4 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <strong>{r.candidate_profile?.candidate_name || 'Unknown'}</strong>
                <span style={{ color: 'var(--danger)', fontWeight: 600, fontSize: '0.85rem' }}>Score: {r.best_score}/100</span>
              </div>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{r.rejection_reason}</p>
            </div>
          ))}
        </>
      )}
    </div>
  )
}

/* ── Tab 3: Assessments ────────────────────── */
function AssessmentTab({ data }) {
  if (!data) return <p style={{ color: 'var(--text-muted)' }}>Waiting for Agent 3 to complete...</p>
  return (
    <div className="card-grid">
      {data.results?.map((r, i) => (
        <div key={i} className="result-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
            <div>
              <h3 style={{ marginBottom: '0.25rem' }}>📝 {r.candidate_name}</h3>
              <RecBadge rec={r.pass_status} />
            </div>
            <ScoreBadge score={Math.round(r.percentage)} />
          </div>
          <div className="detail-row"><span className="detail-label">Total Score</span><span className="detail-value">{r.total_score}/{r.max_score}</span></div>
          <div className="detail-row"><span className="detail-label">Percentage</span><span className="detail-value">{r.percentage?.toFixed(1)}%</span></div>
          {r.section_scores?.map((s, j) => (
            <div key={j} style={{ margin: '0.5rem 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', fontWeight: 500 }}>
                <span>{s.section}</span>
                <span>{s.scored}/{s.max} ({s.percentage?.toFixed(0)}%)</span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${s.percentage}%` }} />
              </div>
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
  )
}

/* ── Tab 4: Interview Guides ───────────────── */
function GuidesTab({ data }) {
  if (!data) return <p style={{ color: 'var(--text-muted)' }}>Waiting for Agent 4 to complete...</p>
  return (
    <div>
      {data.guides?.map((g, i) => (
        <div key={i} className="result-card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h3 style={{ marginBottom: '0.25rem' }}>🎤 {g.candidate_name} → {g.job_title}</h3>
              <RecBadge rec={g.recommendation} />
            </div>
            <div style={{ display: 'flex', gap: '1rem', textAlign: 'center' }}>
              <div><div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary)' }}>{g.match_score}</div><div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Match</div></div>
              <div><div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--purple)' }}>{g.assessment_score?.toFixed(0)}%</div><div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Assessment</div></div>
            </div>
          </div>
          {g.content && <div className="markdown-content" dangerouslySetInnerHTML={{ __html: simpleMarkdown(g.content) }} />}
        </div>
      ))}
    </div>
  )
}

/* ── Tab 5: Logs ───────────────────────────── */
function LogsTab({ logs }) {
  if (!logs?.length) return <p style={{ color: 'var(--text-muted)' }}>No logs yet.</p>
  return (
    <div>
      <p style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
        {logs.length} log entries
      </p>
      {logs.map((log, i) => {
        const cls = log.includes('✅') ? 'log-ok' : log.includes('❌') ? 'log-err' : log.includes('⚠') ? 'log-warn' : ''
        return <div key={i} className={`log-entry ${cls}`}>{log}</div>
      })}
    </div>
  )
}

/* Simple Markdown → HTML */
function simpleMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>')
}

/* ── Main Tabs Container ──────────────────── */
const TAB_CONFIG = [
  { key: 'extracted', label: '📄 Extracted Data', agentKey: 'document_extractor' },
  { key: 'matches', label: '🎯 Match Results', agentKey: 'candidate_matcher' },
  { key: 'assessments', label: '📝 Assessments', agentKey: 'assessment_coordinator' },
  { key: 'guides', label: '🎤 Interview Guides', agentKey: 'interview_strategist' },
  { key: 'logs', label: '📊 Pipeline Logs', agentKey: null },
]

export default function ResultsTabs({ agents, logs }) {
  const [activeTab, setActiveTab] = useState('extracted')

  return (
    <div className="tabs">
      <div className="tab-list">
        {TAB_CONFIG.map(({ key, label, agentKey }) => {
          const hasData = agentKey ? agents[agentKey]?.data : logs?.length > 0
          return (
            <button key={key} className={`tab-btn ${activeTab === key ? 'active' : ''}`} onClick={() => setActiveTab(key)}>
              {label} {hasData && '●'}
            </button>
          )
        })}
      </div>
      <div>
        {activeTab === 'extracted' && <ExtractedTab data={agents.document_extractor?.data} />}
        {activeTab === 'matches' && <MatchTab data={agents.candidate_matcher?.data} />}
        {activeTab === 'assessments' && <AssessmentTab data={agents.assessment_coordinator?.data} />}
        {activeTab === 'guides' && <GuidesTab data={agents.interview_strategist?.data} />}
        {activeTab === 'logs' && <LogsTab logs={logs} />}
      </div>
    </div>
  )
}
