import { useState, useEffect, useRef } from 'react'
import { API } from '../App'
import { Plus, Upload, Pencil, Trash2, Save, X, Briefcase } from 'lucide-react'

function JobForm({ job, onSave, onCancel, isNew }) {
  const [form, setForm] = useState({
    job_id: '', title: '', department: '', required_skills: [],
    preferred_skills: [], min_experience_years: 0, required_education: '',
    description: '', salary_range: '', status: 'OPEN', ...job,
  })
  const [skillInput, setSkillInput] = useState('')
  const [prefInput, setPrefInput] = useState('')

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))
  const addSkill = (key, input, setInput) => {
    if (input.trim()) {
      set(key, [...(form[key] || []), input.trim().toLowerCase()])
      setInput('')
    }
  }
  const removeSkill = (key, idx) => set(key, form[key].filter((_, i) => i !== idx))

  return (
    <div className="form-card">
      <h3>{isNew ? <><Plus size={18} /> Add New Job</> : <><Pencil size={18} /> Edit: {form.title}</>}</h3>
      <div className="form-grid">
        <div className="form-group">
          <label>Job ID</label>
          <input value={form.job_id} onChange={e => set('job_id', e.target.value)} disabled={!isNew} placeholder="JOB-006" />
        </div>
        <div className="form-group">
          <label>Title</label>
          <input value={form.title} onChange={e => set('title', e.target.value)} placeholder="Senior Developer" />
        </div>
        <div className="form-group">
          <label>Department</label>
          <input value={form.department} onChange={e => set('department', e.target.value)} placeholder="Engineering" />
        </div>
        <div className="form-group">
          <label>Min Experience (years)</label>
          <input type="number" value={form.min_experience_years} onChange={e => set('min_experience_years', parseInt(e.target.value) || 0)} />
        </div>
        <div className="form-group full">
          <label>Required Education</label>
          <input value={form.required_education} onChange={e => set('required_education', e.target.value)} />
        </div>
        <div className="form-group full">
          <label>Description</label>
          <textarea rows={3} value={form.description} onChange={e => set('description', e.target.value)} />
        </div>
        <div className="form-group">
          <label>Salary Range</label>
          <input value={form.salary_range} onChange={e => set('salary_range', e.target.value)} />
        </div>
        <div className="form-group">
          <label>Status</label>
          <select value={form.status} onChange={e => set('status', e.target.value)}>
            <option value="OPEN">OPEN</option>
            <option value="CLOSED">CLOSED</option>
            <option value="DRAFT">DRAFT</option>
          </select>
        </div>
        <div className="form-group full">
          <label>Required Skills</label>
          <div className="tag-input-row">
            <input value={skillInput} onChange={e => setSkillInput(e.target.value)} placeholder="Type skill + Enter"
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addSkill('required_skills', skillInput, setSkillInput))} />
            <button className="btn-sm" onClick={() => addSkill('required_skills', skillInput, setSkillInput)}>Add</button>
          </div>
          <div className="tags-wrap">{form.required_skills?.map((s, i) => (
            <span key={i} className="tag tag-skill">{s} <button onClick={() => removeSkill('required_skills', i)}><X size={10} /></button></span>
          ))}</div>
        </div>
        <div className="form-group full">
          <label>Preferred Skills</label>
          <div className="tag-input-row">
            <input value={prefInput} onChange={e => setPrefInput(e.target.value)} placeholder="Type skill + Enter"
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addSkill('preferred_skills', prefInput, setPrefInput))} />
            <button className="btn-sm" onClick={() => addSkill('preferred_skills', prefInput, setPrefInput)}>Add</button>
          </div>
          <div className="tags-wrap">{form.preferred_skills?.map((s, i) => (
            <span key={i} className="tag tag-bonus">{s} <button onClick={() => removeSkill('preferred_skills', i)}><X size={10} /></button></span>
          ))}</div>
        </div>
      </div>
      <div className="form-actions">
        <button className="btn-primary" onClick={() => onSave(form)}><Save size={15} style={{ marginRight: '0.3rem' }} />Save Job</button>
        <button className="btn-secondary" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  )
}

export default function JobsPage() {
  const [jobs, setJobs] = useState([])
  const [editing, setEditing] = useState(null)
  const [editData, setEditData] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const fileRef = useRef(null)

  const loadJobs = () => fetch(`${API}/api/jobs`).then(r => r.json()).then(d => setJobs(d.jobs || []))
  useEffect(() => { loadJobs() }, [])

  const handleSave = async (form) => {
    const isNew = editing === 'new' || editing === 'extract'
    const url = isNew ? `${API}/api/jobs` : `${API}/api/jobs/${form.job_id}`
    const method = isNew ? 'POST' : 'PUT'
    await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    setEditing(null); setEditData(null); loadJobs()
  }

  const handleDelete = async (jobId) => {
    if (!confirm(`Delete job ${jobId}?`)) return
    await fetch(`${API}/api/jobs/${jobId}`, { method: 'DELETE' })
    loadJobs()
  }

  const handleExtract = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setExtracting(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(`${API}/api/jobs/extract`, { method: 'POST', body: formData })
      const data = await res.json()
      if (data.extracted) {
        setEditData(data.extracted)
        setEditing('extract')
      } else {
        alert('Failed to extract job data from flyer.')
      }
    } catch (err) {
      alert('Upload failed: ' + err.message)
    }
    setExtracting(false)
    e.target.value = ''
  }

  if (editing) {
    return <JobForm job={editData || {}} onSave={handleSave} onCancel={() => { setEditing(null); setEditData(null) }} isNew={editing === 'new' || editing === 'extract'} />
  }

  return (
    <div>
      <div className="page-actions">
        <button className="btn-primary" onClick={() => { setEditing('new'); setEditData({}) }}><Plus size={15} /> Add Job Manually</button>
        <button className="btn-accent" onClick={() => fileRef.current?.click()} disabled={extracting}>
          {extracting ? <><span className="spinner" /> Extracting...</> : <><Upload size={15} /> Upload Flyer & Extract</>}
        </button>
        <input ref={fileRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={handleExtract} />
      </div>

      {jobs.length > 0 ? (
        <table className="data-table">
          <thead>
            <tr><th>Job ID</th><th>Title</th><th>Department</th><th>Skills</th><th>Exp</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {jobs.map(j => (
              <tr key={j.job_id}>
                <td><code>{j.job_id}</code></td>
                <td><strong>{j.title}</strong></td>
                <td>{j.department}</td>
                <td><div className="tags-wrap compact">{(j.required_skills || []).slice(0, 4).map((s, i) => <span key={i} className="tag tag-skill">{s}</span>)}{(j.required_skills || []).length > 4 && <span className="tag tag-skill">+{j.required_skills.length - 4}</span>}</div></td>
                <td>{j.min_experience_years}+ yr</td>
                <td><span className={`status-badge ${j.status === 'OPEN' ? 'badge-pass' : 'badge-fail'}`}>{j.status}</span></td>
                <td className="action-cell">
                  <button className="btn-icon" onClick={() => { setEditing(j.job_id); setEditData(j) }} title="Edit"><Pencil size={15} /></button>
                  <button className="btn-icon danger" onClick={() => handleDelete(j.job_id)} title="Delete"><Trash2 size={15} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="empty-state">
          <Briefcase size={48} color="var(--text-muted)" />
          <h3>No jobs yet</h3>
          <p>Add a job manually or upload a job flyer to extract details automatically</p>
        </div>
      )}
    </div>
  )
}
