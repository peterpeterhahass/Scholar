import { useState } from 'react'

interface PPTViewerProps {
  downloadUrl: string
  taskId: string
  metadata: {
    original_filename?: string
    slides_count?: number
    title?: string
  }
}

function PPTViewer({ downloadUrl, taskId, metadata }: PPTViewerProps) {
  const [downloading, setDownloading] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const response = await fetch(downloadUrl)
      if (!response.ok) throw new Error('下载失败')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${metadata.title || 'presentation'}.pptx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      alert('下载失败，请重试')
    } finally {
      setDownloading(false)
    }
  }

  const handlePreview = () => {
    setShowPreview(true)
  }

  return (
    <>
      <div className="ppt-container">
        <div className="ppt-header">
          <h2>📊 生成的 PPT</h2>
          <div className="ppt-metadata">
            {metadata.original_filename && (
              <span>源文件: {metadata.original_filename}</span>
            )}
            {metadata.slides_count && (
              <span>幻灯片数: {metadata.slides_count}</span>
            )}
            {metadata.title && (
              <span>标题: {metadata.title}</span>
            )}
          </div>
        </div>

        <div className="ppt-preview">
          <div className="ppt-icon">📊</div>
          <h3>PowerPoint 演示文稿已生成</h3>
          <p>包含 {metadata.slides_count || 0} 张幻灯片</p>

          <div className="ppt-actions">
            <button
              className="btn-primary"
              onClick={handlePreview}
            >
              👁️ 预览 PPT
            </button>
            <button
              className="btn-secondary"
              onClick={handleDownload}
              disabled={downloading}
            >
              {downloading ? '下载中...' : '⬇️ 下载 PPT'}
            </button>
          </div>

          <div className="ppt-tips">
            <h4>💡 使用提示</h4>
            <ul>
              <li>点击"预览PPT"可直接在浏览器中查看幻灯片</li>
              <li>点击"下载PPT"可保存到本地编辑</li>
              <li>PPT 已根据论文结构自动生成</li>
            </ul>
          </div>
        </div>
      </div>

      {showPreview && (
        <div className="ppt-preview-modal" onClick={() => setShowPreview(false)}>
          <div className="ppt-preview-content" onClick={(e) => e.stopPropagation()}>
            <div className="ppt-preview-header">
              <h3>📊 {metadata.title || 'PPT预览'}</h3>
              <button className="btn-close" onClick={() => setShowPreview(false)}>✕</button>
            </div>

            <iframe
              src={`https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(window.location.origin + downloadUrl)}`}
              style={{
                flex: 1,
                width: '100%',
                border: 'none',
                borderRadius: '0 0 12px 12px'
              }}
              title="PPT Preview"
            />
          </div>
        </div>
      )}
    </>
  )
}

export default PPTViewer
