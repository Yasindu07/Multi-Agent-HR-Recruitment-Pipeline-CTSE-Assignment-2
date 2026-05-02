import { LayoutDashboard, Briefcase, Users, Rocket, ClipboardList, Bot, Wifi } from 'lucide-react'

const TITLES = {
  dashboard: { icon: LayoutDashboard, title: 'Dashboard', desc: 'Overview of your recruitment pipeline' },
  jobs: { icon: Briefcase, title: 'Job Vacancies', desc: 'Manage job postings and flyers' },
  candidates: { icon: Users, title: 'Candidates', desc: 'Manage candidate profiles and CVs' },
  pipeline: { icon: Rocket, title: 'Run Pipeline', desc: 'Execute the AI recruitment pipeline' },
  results: { icon: ClipboardList, title: 'Results History', desc: 'View past pipeline runs and outcomes' },
}

export default function Header({ page }) {
  const t = TITLES[page] || TITLES.dashboard
  const Icon = t.icon
  return (
    <header className="top-header">
      <div>
        <h1 className="page-title"><Icon size={22} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />{t.title}</h1>
        <p className="page-desc">{t.desc}</p>
      </div>
      <div className="header-right">
        <span className="header-badge"><Bot size={13} style={{ marginRight: '0.3rem', verticalAlign: 'middle' }} />Ollama + LangGraph</span>
        <span className="header-badge green"><Wifi size={13} style={{ marginRight: '0.3rem', verticalAlign: 'middle' }} />Connected</span>
      </div>
    </header>
  )
}
