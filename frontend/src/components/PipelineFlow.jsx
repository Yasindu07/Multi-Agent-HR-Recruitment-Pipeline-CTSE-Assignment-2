import { FileText, GitBranch, Brain, MessageSquare, ChevronRight, Check, X, SkipForward } from 'lucide-react'

const AGENT_ORDER = ['document_extractor', 'candidate_matcher', 'assessment_coordinator', 'interview_strategist']

const AGENT_ICONS = {
  document_extractor: FileText,
  candidate_matcher: GitBranch,
  assessment_coordinator: Brain,
  interview_strategist: MessageSquare,
}

const STATUS_LABELS = {
  waiting: 'Waiting',
  running: 'Processing...',
  completed: 'Done',
  failed: 'Failed',
  skipped: 'Skipped',
}

const STATUS_ICONS = {
  completed: Check,
  failed: X,
  skipped: SkipForward,
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

export default function PipelineFlow({ agents }) {
  return (
    <div className="pipeline-flow">
      {AGENT_ORDER.map((key, i) => {
        const agent = agents[key]
        const Icon = AGENT_ICONS[key]
        const StatusIcon = STATUS_ICONS[agent.status]
        const prevCompleted = i === 0 || agents[AGENT_ORDER[i - 1]]?.status === 'completed'
        return (
          <div key={key} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
            {i > 0 && <div className={`flow-arrow ${prevCompleted ? 'active' : ''}`}><ChevronRight size={20} /></div>}
            <div className={`agent-card ${agent.status}`} style={{ flex: 1 }}>
              <div className="agent-icon">
                {agent.status === 'running' ? (
                  <span className="spinner" style={{ width: 22, height: 22, borderWidth: 2.5 }} />
                ) : StatusIcon ? (
                  <StatusIcon size={22} />
                ) : (
                  <Icon size={22} />
                )}
              </div>
              <div className="agent-name">{agent.label}</div>
              <div className="agent-status">{STATUS_LABELS[agent.status]}</div>
              {agent.duration && <div className="agent-time">{formatDuration(agent.duration)}</div>}
            </div>
          </div>
        )
      })}
    </div>
  )
}
