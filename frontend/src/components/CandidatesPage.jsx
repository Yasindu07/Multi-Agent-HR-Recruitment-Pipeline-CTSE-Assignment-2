import { useState, useEffect, useRef } from 'react'
import { API } from '../App'
import { Plus, Upload, Pencil, Trash2, Save, X, Users } from 'lucide-react'

function CandidateForm({ candidate, onSave, onCancel, isNew }) {
  const [form, setForm] = useState({
    name: '', email: '', phone: '', years_of_experience: 0,
    skills: [], education: [], work_experience: [], github_url: '',
    certifications: [], source_file: '', ...candidate,
  })
  const [skillInput, setSkillInput] = useState('')

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))
  const addSkill = () => {
    if (skillInput.trim()) {
      set('skills', [...(form.skills || []), skillInput.trim().toLowerCase()])
      setSkillInput('')
    }
  }
  const removeSkill = (idx) => set('skills', form.skills.filter((_, i) => i !== idx))

  return (
    <div className="form-card">
      <h3>{isNew ? <><Plus size={18} /> Add New Candidate</> : <><Pencil size={18} /> Edit: {form.name}</>}</h3>
      <div className="form-grid">
        <div className="form-group"><label>Full Name</label>
          <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="John Doe" /></div>
        <div className="form-group"><label>Email</label>
          <input value={form.email} onChange={e => set('email', e.target.value)} placeholder="john@example.com" /></div>
        <div className="form-group"><label>Phone</label>
          <input value={form.phone} onChange={e => set('phone', e.target.value)} /></div>
        <div className="form-group"><label>Years of Experience</label>
          <input type="number" value={form.years_of_experience} onChange={e => set('years_of_experience', parseInt(e.target.value) || 0)} /></div>
        <div className="form-group full"><label>GitHub URL</label>
          <input value={form.github_url} onChange={e => set('github_url', e.target.value)} placeholder="https://github.com/..." /></div>
        <div className="form-group full">
          <label>Skills</label>
          <div className="tag-input-row">
            <input value={skillInput} onChange={e => setSkillInput(e.target.value)} placeholder="Type skill + Enter"
              onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addSkill())} />
            <button className="btn-sm" onClick={addSkill}>Add</button>
          </div>
          <div className="tags-wrap">{form.skills?.map((s, i) => (
            <span key={i} className="tag tag-skill">{s} <button onClick={() => removeSkill(i)}><X size={10} /></button></span>
          ))}</div>
        </div>
        <div className="form-group full">
          <label>Education (JSON)</label>
          <textarea rows={3} value={JSON.stringify(form.education || [], null, 2)}
            onChange={e => { try { set('education', JSON.parse(e.target.value)) } catch {} }} />
        </div>
        <div className="form-group full">
          <label>Work Experience (JSON)</label>
          <textarea rows={4} value={JSON.stringify(form.work_experience || [], null, 2)}
            onChange={e => { try { set('work_experience', JSON.parse(e.target.value)) } catch {} }} />
        </div>
      </div>
      <div className="form-actions">
        <button className="btn-primary" onClick={() => onSave(form)}><Save size={15} style={{ marginRight: '0.3rem' }} />Save Candidate</button>
        <button className="btn-secondary" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  )
}

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState([])
  const [editing, setEditing] = useState(null)
  const [editData, setEditData] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const fileRef = useRef(null)

  const load = () => fetch(`${API}/api/candidates`).then(r => r.json()).then(d => setCandidates(d.candidates || []))
  useEffect(() => { load() }, [])

  const handleSave = async (form) => {
    const isNew = editing === 'new' || editing === 'extract'
    const url = isNew ? `${API}/api/candidates` : `${API}/api/candidates/${form.id}`
    const method = isNew ? 'POST' : 'PUT'
    await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    setEditing(null); setEditData(null); load()
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this candidate?')) return
    await fetch(`${API}/api/candidates/${id}`, { method: 'DELETE' })
    load()
  }

  const handleExtract = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setExtracting(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(`${API}/api/candidates/extract`, { method: 'POST', body: formData })
      const data = await res.json()
      if (data.extracted) {
        const extracted = data.extracted
        setEditData({
          name: extracted.candidate_name || '',
          email: extracted.email || '',
          phone: extracted.phone || '',
          years_of_experience: extracted.years_of_experience || 0,
          skills: extracted.skills || [],
          education: extracted.education || [],
          work_experience: extracted.work_experience || [],
          github_url: extracted.github_url || '',
          certifications: extracted.certifications || [],
          source_file: data.source_file || '',
        })
        setEditing('extract')
      } else {
        alert('Failed to extract from CV.')
      }
    } catch (err) {
      alert('Upload failed: ' + err.message)
    }
    setExtracting(false)
    e.target.value = ''
  }

  if (editing) {
    return <CandidateForm candidate={editData || {}} onSave={handleSave}
      onCancel={() => { setEditing(null); setEditData(null) }}
      isNew={editing === 'new' || editing === 'extract'} />
  }

  return (
    <div>
      <div className="page-actions">
        <button className="btn-primary" onClick={() => { setEditing('new'); setEditData({}) }}><Plus size={15} /> Add Manually</button>
        <button className="btn-accent" onClick={() => fileRef.current?.click()} disabled={extracting}>
          {extracting ? <><span className="spinner" /> Extracting CV...</> : <><Upload size={15} /> Upload CV & Extract</>}
        </button>
        <input ref={fileRef} type="file" accept=".pdf,.docx" style={{ display: 'none' }} onChange={handleExtract} />
      </div>

      {candidates.length > 0 ? (
        <table className="data-table">
          <thead>
            <tr><th>ID</th><th>Name</th><th>Email</th><th>Skills</th><th>Exp</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {candidates.map(c => (
              <tr key={c.id}>
                <td>#{c.id}</td>
                <td><strong>{c.name}</strong></td>
                <td>{c.email || '—'}</td>
                <td><div className="tags-wrap compact">{(c.skills || []).slice(0, 4).map((s, i) => <span key={i} className="tag tag-skill">{s}</span>)}{(c.skills || []).length > 4 && <span className="tag tag-skill">+{c.skills.length - 4}</span>}</div></td>
                <td>{c.years_of_experience}y</td>
                <td className="action-cell">
                  <button className="btn-icon" onClick={() => { setEditing(c.id); setEditData(c) }}><Pencil size={15} /></button>
                  <button className="btn-icon danger" onClick={() => handleDelete(c.id)}><Trash2 size={15} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="empty-state">
          <Users size={48} color="var(--text-muted)" />
          <h3>No candidates yet</h3>
          <p>Add a candidate manually or upload a CV to extract their profile automatically</p>
        </div>
      )}
    </div>
  )
}
