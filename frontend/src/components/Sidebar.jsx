import { LayoutDashboard, Briefcase, Users, Rocket, ClipboardList, Zap, ShieldCheck } from 'lucide-react'

const NAV = [
  { key: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { key: 'jobs', icon: Briefcase, label: 'Jobs' },
  { key: 'candidates', icon: Users, label: 'Candidates' },
  { key: 'pipeline', icon: Rocket, label: 'Run Pipeline' },
  { key: 'results', icon: ClipboardList, label: 'Results' },
]

export default function Sidebar({ page, setPage }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo-icon">
          <Briefcase size={22} />
        </div>
        <div>
          <div className="sidebar-title">HR Pipeline</div>
          <div className="sidebar-subtitle">Multi-Agent System</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        {NAV.map(({ key, icon: Icon, label }) => (
          <button
            key={key}
            className={`nav-item ${page === key ? 'active' : ''}`}
            onClick={() => setPage(key)}
          >
            <Icon size={18} className="nav-icon" />
            <span className="nav-label">{label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="sidebar-badge"><Zap size={12} /> Powered by Ollama</div>
        <div className="sidebar-badge"><ShieldCheck size={12} /> 100% Local</div>
      </div>
    </aside>
  )
}
