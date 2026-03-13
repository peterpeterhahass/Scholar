import { useState } from 'react'

interface FileUploadWithModeProps {
  onFileSelect: (file: File, mode: 'notes' | 'ppt' | 'both') => void
  loading: boolean
}

function FileUploadWithMode({ onFileSelect, loading }: FileUploadWithModeProps) {
  const [dragActive, setDragActive] = useState(false)
  const [selectedMode, setSelectedMode] = useState<'notes' | 'ppt' | 'both'>('notes')

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0], selectedMode)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0], selectedMode)
    }
  }

  return (
    <div className="upload-container">
      <div className="mode-selector">
        <h3>选择输出模式</h3>
        <div className="mode-buttons">
          <button
            className={`mode-btn ${selectedMode === 'notes' ? 'active' : ''}`}
            onClick={() => setSelectedMode('notes')}
            disabled={loading}
          >
            📝 仅生成笔记
          </button>
          <button
            className={`mode-btn ${selectedMode === 'ppt' ? 'active' : ''}`}
            onClick={() => setSelectedMode('ppt')}
            disabled={loading}
          >
            📊 仅生成PPT
          </button>
          <button
            className={`mode-btn ${selectedMode === 'both' ? 'active' : ''}`}
            onClick={() => setSelectedMode('both')}
            disabled={loading}
          >
            📚 笔记 + PPT
          </button>
        </div>
        <p className="mode-description">
          {selectedMode === 'notes' && '生成详细的学术笔记（Markdown格式）'}
          {selectedMode === 'ppt' && '生成演示文稿（PowerPoint格式，适合汇报）'}
          {selectedMode === 'both' && '同时生成笔记和PPT，一次性获得两种格式'}
        </p>
      </div>

      <div
        className={`file-upload-area ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          accept=".pdf"
          onChange={handleChange}
          disabled={loading}
          style={{ display: 'none' }}
        />
        <label htmlFor="file-upload" className={`upload-label ${loading ? 'disabled' : ''}`}>
          <div className="upload-icon">
            {loading ? '⏳' : '📄'}
          </div>
          <div className="upload-text">
            {loading ? '处理中...' : '拖拽 PDF 文件到此处，或点击选择文件'}
          </div>
          <div className="upload-hint">
            最大支持 10MB
          </div>
        </label>
      </div>
    </div>
  )
}

export default FileUploadWithMode
