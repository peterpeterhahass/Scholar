import { useCallback, useState } from 'react'
import './FileUpload.css'

interface FileUploadProps {
  onFileSelect: (file: File) => void
  loading: boolean
}

export default function FileUpload({ onFileSelect, loading }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (loading) return

    const files = e.dataTransfer.files
    if (files && files[0]) {
      const file = files[0]
      if (file.type === 'application/pdf') {
        onFileSelect(file)
      } else {
        alert('请上传 PDF 文件')
      }
    }
  }, [loading, onFileSelect])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (loading) return

    const files = e.target.files
    if (files && files[0]) {
      const file = files[0]
      if (file.type === 'application/pdf') {
        onFileSelect(file)
      } else {
        alert('请上传 PDF 文件')
      }
    }
  }, [loading, onFileSelect])

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-area ${dragActive ? 'active' : ''} ${loading ? 'loading' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          accept="application/pdf"
          onChange={handleChange}
          disabled={loading}
        />
        <label htmlFor="file-upload" className="file-upload-label">
          <div className="upload-icon">📄</div>
          <h3>拖拽 PDF 文件到这里</h3>
          <p>或者点击选择文件</p>
          <span className="file-limit">最大支持 10MB</span>
        </label>
      </div>
    </div>
  )
}
