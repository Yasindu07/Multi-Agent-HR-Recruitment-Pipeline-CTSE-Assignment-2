import { useState, useRef } from 'react'

const API_BASE = 'http://localhost:8000'

function DropZone({ label, accept, fileType, files, setFiles, disabled }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleFiles = async (fileList) => {
    if (!fileList.length) return
    const formData = new FormData()
    for (const f of fileList) {
      formData.append('files', f)
    }
    formData.append('file_type', fileType)

    try {
      const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: formData })
      const data = await res.json()
      setFiles(prev => [...prev, ...Array.from(fileList).map((f, i) => ({ name: f.name, path: data.paths[i] }))])
    } catch (err) {
      console.error('Upload failed:', err)
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    if (!disabled) handleFiles(e.dataTransfer.files)
  }

  const onDragOver = (e) => { e.preventDefault(); if (!disabled) setDragging(true) }
  const onDragLeave = () => setDragging(false)

  return (
    <div>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>{label}</div>
      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        style={{
          border: `2px dashed ${dragging ? 'var(--primary)' : 'var(--border)'}`,
          borderRadius: 'var(--radius-sm)',
          padding: '1rem',
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          background: dragging ? 'var(--primary-bg)' : 'var(--bg)',
          transition: 'all 0.2s',
          opacity: disabled ? 0.5 : 1,
          minHeight: '60px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.25rem',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple
          style={{ display: 'none' }}
          onChange={(e) => handleFiles(e.target.files)}
          disabled={disabled}
        />
        {files.length === 0 ? (
          <>
            <span style={{ fontSize: '1.25rem' }}>{fileType === 'resume' ? '📄' : '📋'}</span>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Drop files here or click to browse
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>PDF / DOCX</span>
          </>
        ) : (
          <div style={{ width: '100%', textAlign: 'left' }}>
            {files.map((f, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                fontSize: '0.78rem', color: 'var(--text-secondary)', padding: '0.15rem 0'
              }}>
                <span style={{ color: 'var(--success)' }}>✅</span>
                {f.name}
                <button
                  onClick={(e) => { e.stopPropagation(); setFiles(prev => prev.filter((_, j) => j !== i)) }}
                  style={{
                    marginLeft: 'auto', background: 'none', border: 'none',
                    color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.75rem',
                  }}
                >✕</button>
              </div>
            ))}
            <div style={{ fontSize: '0.7rem', color: 'var(--primary)', marginTop: '0.25rem', fontWeight: 500 }}>
              + Add more files
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function FileUpload({ resumeFiles, setResumeFiles, flyerFiles, setFlyerFiles, disabled }) {
  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem',
      padding: '1.25rem', background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', boxShadow: 'var(--shadow-sm)', marginBottom: '1.5rem',
    }}>
      <DropZone
        label="📄 Candidate CVs (Resumes)"
        accept=".pdf,.docx"
        fileType="resume"
        files={resumeFiles}
        setFiles={setResumeFiles}
        disabled={disabled}
      />
      <DropZone
        label="📋 Job Flyers"
        accept=".pdf"
        fileType="flyer"
        files={flyerFiles}
        setFiles={setFlyerFiles}
        disabled={disabled}
      />
    </div>
  )
}
