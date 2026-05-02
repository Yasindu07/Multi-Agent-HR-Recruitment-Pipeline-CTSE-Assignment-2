export default function Welcome() {
  return (
    <div className="welcome-card">
      <h2>👋 Welcome to the HR Recruitment Pipeline</h2>
      <p>
        This Multi-Agent System automates the full hiring lifecycle using 4 specialized AI agents,
        all running locally on your machine with zero cloud dependencies.
      </p>
      <div style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', textAlign: 'left', maxWidth: '900px', margin: '2rem auto 0' }}>
        {[
          { icon: '🔵', title: 'Document Extractor', desc: 'Parses CVs & Job Flyers into structured JSON', tool: 'PDF/DOCX Parser' },
          { icon: '🟣', title: 'Candidate Matcher', desc: 'Scores & ranks candidates against vacancies', tool: 'SQLite Database' },
          { icon: '🟢', title: 'Assessment Coordinator', desc: 'Generates personalized quizzes + auto-grades', tool: 'JSON Generator' },
          { icon: '🟠', title: 'Interview Strategist', desc: 'Creates interview guides + comparison reports', tool: 'Markdown Writer' },
        ].map(({ icon, title, desc, tool }) => (
          <div key={title} className="result-card" style={{ padding: '1.25rem' }}>
            <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{icon}</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.25rem' }}>{title}</div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{desc}</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Tool: {tool}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: '2rem', display: 'flex', gap: '1.5rem', justifyContent: 'center', flexWrap: 'wrap' }}>
        {['✅ 100% Local', '🔒 Privacy-First', '🔄 Smart Routing', '📊 Full Observability'].map(f => (
          <span key={f} style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', background: 'var(--bg)', padding: '0.4rem 0.8rem', borderRadius: '999px', border: '1px solid var(--border)' }}>{f}</span>
        ))}
      </div>
    </div>
  )
}
