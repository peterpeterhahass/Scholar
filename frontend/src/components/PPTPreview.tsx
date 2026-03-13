import { useEffect, useRef, useState } from 'react'

interface PPTPreviewProps {
  pptUrl: string
  onClose: () => void
}

function PPTPreview({ pptUrl, onClose }: PPTPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [slideCount, setSlideCount] = useState(0)
  const [currentSlide, setCurrentSlide] = useState(0)

  useEffect(() => {
    const loadPPT = async () => {
      try {
        setLoading(true)

        // 动态加载 pptxjs 库
        const script = document.createElement('script')
        script.src = 'https://cdn.jsdelivr.net/npm/pptxjs@latest/bundle/pptx.bundle.js'
        script.async = true
        document.body.appendChild(script)

        script.onload = () => {
          // 加载 PPT 文件
          const pptx = new (window as any).PptxGenJS()

          fetch(pptUrl)
            .then(res => res.arrayBuffer())
            .then(buffer => {
              const zip = new (window as any).JSZip()
              zip.loadAsync(buffer).then(() => {
                // 解析 PPT
                pptx.load(zip).then(() => {
                  // 渲染第一页
                  if (containerRef.current) {
                    containerRef.current.innerHTML = ''
                    const slideDiv = document.createElement('div')
                    slideDiv.style.width = '100%'
                    slideDiv.style.height = '100%'
                    containerRef.current.appendChild(slideDiv)

                    pptx.renderTo(slideDiv)
                    setSlideCount(pptx.slides.length)
                    setLoading(false)
                  }
                })
              })
            })
        }

        script.onerror = () => {
          setError('加载PPT预览组件失败')
          setLoading(false)
        }
      } catch (err) {
        setError('预览PPT时出错')
        setLoading(false)
      }
    }

    loadPPT()
  }, [pptUrl])

  const handlePrevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1)
    }
  }

  const handleNextSlide = () => {
    if (currentSlide < slideCount - 1) {
      setCurrentSlide(currentSlide + 1)
    }
  }

  return (
    <div className="ppt-preview-modal">
      <div className="ppt-preview-content">
        <div className="ppt-preview-header">
          <h3>PPT 预览</h3>
          <button className="btn-close" onClick={onClose}>✕</button>
        </div>

        {loading && (
          <div className="ppt-loading">
            <div className="spinner"></div>
            <p>正在加载 PPT...</p>
          </div>
        )}

        {error && (
          <div className="ppt-error">
            <p>{error}</p>
            <p className="tip">提示: 您可以下载PPT文件后在本地查看</p>
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="ppt-viewer" ref={containerRef}>
              {/* PPT 将在这里渲染 */}
            </div>

            <div className="ppt-controls">
              <button onClick={handlePrevSlide} disabled={currentSlide === 0}>
                ← 上一页
              </button>
              <span className="slide-indicator">
                {currentSlide + 1} / {slideCount}
              </span>
              <button onClick={handleNextSlide} disabled={currentSlide >= slideCount - 1}>
                下一页 →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default PPTPreview
