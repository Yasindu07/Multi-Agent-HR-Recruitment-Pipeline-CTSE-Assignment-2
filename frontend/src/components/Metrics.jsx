export default function Metrics({ agents }) {
  const ext = agents.document_extractor?.data
  const match = agents.candidate_matcher?.data
  const assess = agents.assessment_coordinator?.data
  const intv = agents.interview_strategist?.data

  const items = [
    { label: 'CVs Extracted', value: ext?.profiles?.length ?? '—', color: 'var(--primary)' },
    { label: 'Vacancies', value: ext?.vacancies?.length ?? '—', color: 'var(--info)' },
    { label: 'Shortlisted', value: match?.shortlisted?.length ?? '—', color: 'var(--success)' },
    { label: 'Rejected', value: match?.rejected?.length ?? '—', color: 'var(--danger)' },
    { label: 'Assessed', value: assess?.results?.length ?? '—', color: 'var(--purple)' },
    { label: 'Guides', value: intv?.guides?.length ?? '—', color: 'var(--warning)' },
  ]

  return (
    <div className="metrics-grid">
      {items.map(({ label, value, color }) => (
        <div key={label} className="metric-card">
          <div className="metric-value" style={{ color }}>{value}</div>
          <div className="metric-label">{label}</div>
        </div>
      ))}
    </div>
  )
}
