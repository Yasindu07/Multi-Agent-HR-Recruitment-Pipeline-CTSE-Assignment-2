import { useState, useCallback, useEffect } from 'react'
import './index.css'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import DashboardPage from './components/DashboardPage'
import JobsPage from './components/JobsPage'
import CandidatesPage from './components/CandidatesPage'
import PipelinePage from './components/PipelinePage'
import ResultsPage from './components/ResultsPage'

export const API = 'http://localhost:8000'

export default function App() {
  const [page, setPage] = useState('dashboard')

  return (
    <div className="app-layout">
      <Sidebar page={page} setPage={setPage} />
      <div className="main-panel">
        <Header page={page} />
        <div className="page-content">
          {page === 'dashboard' && <DashboardPage />}
          {page === 'jobs' && <JobsPage />}
          {page === 'candidates' && <CandidatesPage />}
          {page === 'pipeline' && <PipelinePage />}
          {page === 'results' && <ResultsPage />}
        </div>
      </div>
    </div>
  )
}
