import { useState } from 'react'
import FileUploadWithMode from './components/FileUploadWithMode'
import PaperNotesViewer from './components/PaperNotesViewer'
import PPTViewer from './components/PPTViewer'
import './App.css'

interface NotesData {
  notes: string
  metadata: {
    original_filename?: string
    file_size?: number
    source?: string
    markdown_size?: number
    model: string
    tokens_used: number
    task_id?: string
  }
}

interface PPTData {
  download_url: string
  task_id?: string
  metadata: {
    original_filename?: string
    slides_count?: number
    title?: string
  }
}

interface Task {
  task_id: string
  markdown_exists: boolean
  markdown_size?: number
  images_dir_exists: boolean
  image_count?: number
}

function App() {
  const [notesData, setNotesData] = useState<NotesData | null>(null)
  const [pptData, setPPTData] = useState<PPTData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [showTasks, setShowTasks] = useState(false)
  const [loadingTasks, setLoadingTasks] = useState(false)
  const [savedPPTContents, setSavedPPTContents] = useState<any[]>([])
  const [showSavedContents, setShowSavedContents] = useState(false)
  const [loadingSavedContents, setLoadingSavedContents] = useState(false)

  // 获取任务列表
  const fetchTasks = async () => {
    setLoadingTasks(true)
    // 清空当前显示的内容，以便正确切换到任务列表页面
    setNotesData(null)
    setPPTData(null)
    setShowSavedContents(false)
    try {
      const response = await fetch('/api/tasks')
      if (!response.ok) throw new Error('获取任务列表失败')

      const data = await response.json()
      setTasks(data.tasks || [])
      setShowTasks(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取任务列表失败')
    } finally {
      setLoadingTasks(false)
    }
  }

  // 获取已保存的 PPT 内容列表
  const fetchSavedPPTContents = async () => {
    console.log('开始获取已保存的 PPT 内容列表')
    setLoadingSavedContents(true)
    // 清空当前显示的内容，以便正确切换到已保存内容页面
    setNotesData(null)
    setPPTData(null)
    setShowTasks(false)
    try {
      const response = await fetch('/api/saved-ppt-contents')
      console.log('响应状态:', response.status)

      if (!response.ok) throw new Error('获取已保存的 PPT 内容失败')

      const data = await response.json()
      console.log('获取到的数据:', data)
      setSavedPPTContents(data.contents || [])
      setShowSavedContents(true)
      console.log('已保存内容列表已更新，共', data.contents?.length || 0, '项')
    } catch (err) {
      console.error('获取已保存内容失败:', err)
      setError(err instanceof Error ? err.message : '获取已保存的 PPT 内容失败')
    } finally {
      setLoadingSavedContents(false)
    }
  }

  // 基于已保存的 PPT 内容生成 PPT
  const handleGenerateFromSavedContent = async (taskId: string) => {
    console.log('开始基于已保存内容生成 PPT, taskId:', taskId)
    setLoading(true)
    setError(null)
    setNotesData(null)
    setPPTData(null)
    setShowSavedContents(false)

    try {
      const apiUrl = `/api/generate-ppt-from-saved-content?task_id=${taskId}`
      console.log('请求 URL:', apiUrl)

      const response = await fetch(apiUrl, {
        method: 'POST',
      })

      console.log('响应状态:', response.status)

      if (!response.ok) {
        const errorData = await response.json()
        console.error('错误响应:', errorData)
        throw new Error(errorData.detail || '生成 PPT 失败')
      }

      const pptData = await response.json()
      console.log('PPT 数据:', pptData)

      setPPTData({
        download_url: pptData.download_url,
        task_id: pptData.task_id,
        metadata: pptData.metadata
      })
      console.log('PPT 数据已设置，应该显示 PPTViewer 组件')
    } catch (err) {
      console.error('生成 PPT 失败:', err)
      setError(err instanceof Error ? err.message : '生成 PPT 失败，请重试')
    } finally {
      setLoading(false)
      console.log('loading 已设置为 false')
    }
  }

  // 预览已生成的笔记（不调用LLM，直接读取缓存）
  const handlePreviewNotes = async (taskId: string) => {
    setLoading(true)
    setError(null)
    setPPTData(null)
    setShowTasks(false)

    try {
      const response = await fetch(`/api/notes/${taskId}`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '获取笔记失败')
      }

      const data = await response.json()
      setNotesData({
        notes: data.content,
        metadata: {
          source: 'existing_task',
          model: 'cached',
          tokens_used: 0,
          task_id: taskId,
        }
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取笔记失败')
    } finally {
      setLoading(false)
    }
  }

  // 生成 Marp PPT
  const handleGenerateMarpPPT = async (taskId: string) => {
    setLoading(true)
    setError(null)
    setNotesData(null)
    setPPTData(null)
    setShowTasks(false)

    try {
      const response = await fetch(`/api/generate-marp-ppt?task_id=${taskId}`, {
        method: 'POST',
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '生成 Marp PPT 失败')
      }

      const data = await response.json()
      setPPTData({
        download_url: data.download_url,
        task_id: data.task_id,
        metadata: data.metadata
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成 Marp PPT 失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  // 从任务生成笔记
  const handleGenerateFromTask = async (taskId: string, mode: 'notes' | 'ppt' | 'both' = 'notes') => {
    setLoading(true)
    setError(null)

    // 只在需要时清空对应的数据
    if (mode === 'notes') {
      setPPTData(null)
    } else if (mode === 'ppt') {
      setNotesData(null)
    } else {
      setNotesData(null)
      setPPTData(null)
    }

    setShowTasks(false)

    try {
      // 根据模式生成内容
      if (mode === 'notes' || mode === 'both') {
        const notesResponse = await fetch(`/api/generate-notes-from-task?task_id=${taskId}`, {
          method: 'POST',
        })

        if (!notesResponse.ok) {
          const errorData = await notesResponse.json()
          throw new Error(errorData.detail || '生成笔记失败')
        }

        const data = await notesResponse.json()

        // 将图片路径转换为 API 路径
        data.notes = data.notes.replace(
          /!\[\]\(images\/([^)]+)\)/g,
          `![](/api/images/${taskId}/$1)`
        )

        // 添加 task_id 到 metadata
        data.metadata.task_id = taskId

        setNotesData(data)
      }

      if (mode === 'ppt' || mode === 'both') {
        // 使用新的基于笔记的 PPT 生成接口
        const pptResponse = await fetch(`/api/generate-ppt-from-notes?task_id=${taskId}`, {
          method: 'POST',
        })

        if (!pptResponse.ok) {
          const errorData = await pptResponse.json()
          throw new Error(errorData.detail || '生成PPT失败')
        }

        const pptData = await pptResponse.json()
        setPPTData({
          download_url: pptData.download_url,
          task_id: pptData.task_id,
          metadata: pptData.metadata
        })
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = async (file: File, mode: 'notes' | 'ppt' | 'both') => {
    setLoading(true)
    setError(null)

    // 只在需要时清空对应的数据
    if (mode === 'notes') {
      setPPTData(null)
    } else if (mode === 'ppt') {
      setNotesData(null)
    } else {
      setNotesData(null)
      setPPTData(null)
    }

    setShowTasks(false)

    const formData = new FormData()
    formData.append('file', file)

    try {
      // 根据模式选择不同的API端点
      let endpoint = '/api/upload-pdf'
      if (mode === 'ppt') {
        // 使用新的基于笔记的 PPT 生成接口
        endpoint = '/api/upload-pdf-ppt-v2'
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '上传失败')
      }

      const data = await response.json()

      // 处理笔记数据
      if (data.notes && (mode === 'notes' || mode === 'both')) {
        // 将图片路径转换为 API 路径（如果有 task_id）
        if (data.task_id) {
          data.notes = data.notes.replace(
            /!\[\]\(images\/([^)]+)\)/g,
            `![](/api/images/${data.task_id}/$1)`
          )
          data.metadata.task_id = data.task_id
        }
        setNotesData(data)
      }

      // 处理PPT数据
      if (data.download_url && (mode === 'ppt' || mode === 'both')) {
        setPPTData({
          download_url: data.download_url,
          task_id: data.task_id,
          metadata: data.metadata
        })
      }

      // 如果是both模式但只返回了一种数据，需要额外请求
      if (mode === 'both') {
        if (data.notes && !data.download_url && data.task_id) {
          // 有笔记但没PPT，生成PPT（使用新接口）
          const pptResponse = await fetch(`/api/generate-ppt-from-notes?task_id=${data.task_id}`, {
            method: 'POST',
          })
          if (pptResponse.ok) {
            const pptData = await pptResponse.json()
            setPPTData({
              download_url: pptData.download_url,
              task_id: pptData.task_id,
              metadata: pptData.metadata
            })
          }
        } else if (data.download_url && !data.notes && data.task_id) {
          // 有PPT但没笔记，生成笔记
          const notesResponse = await fetch(`/api/generate-notes-from-task?task_id=${data.task_id}`, {
            method: 'POST',
          })
          if (notesResponse.ok) {
            const notesData = await notesResponse.json()
            notesData.notes = notesData.notes.replace(
              /!\[\]\(images\/([^)]+)\)/g,
              `![](/api/images/${data.task_id}/$1)`
            )
            notesData.metadata.task_id = data.task_id
            setNotesData(notesData)
          }
        }
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>📚 PDF 笔记生成器</h1>
        <p>上传 PDF 文档，自动生成结构化学习笔记</p>
        <div className="header-buttons">
          <button
            className="btn-secondary"
            onClick={fetchTasks}
            disabled={loadingTasks}
          >
            {loadingTasks ? '加载中...' : '📋 查看已提取文档'}
          </button>
          <button
            className="btn-secondary"
            onClick={fetchSavedPPTContents}
            disabled={loadingSavedContents}
          >
            {loadingSavedContents ? '加载中...' : '🎨 已保存的PPT内容'}
          </button>
        </div>
      </header>

      <main className="app-main">
        {showSavedContents ? (
          <div className="tasks-container">
            <div className="tasks-header">
              <h2>已保存的 PPT 内容</h2>
              <button
                className="btn-text"
                onClick={() => setShowSavedContents(false)}
              >
                返回上传
              </button>
            </div>

            {savedPPTContents.length === 0 ? (
              <div className="empty-state">
                <p>暂无已保存的 PPT 内容</p>
                <p className="empty-state-hint">生成 PPT 后会自动保存内容</p>
              </div>
            ) : (
              <div className="tasks-list">
                {savedPPTContents.map((content) => (
                  <div key={content.task_id} className="task-item">
                    <div className="task-info">
                      <h3>{content.title}</h3>
                      <div className="task-details">
                        <span>📊 {content.slide_count} 张幻灯片</span>
                        <span>📝 {content.content_length} 字符</span>
                      </div>
                    </div>
                    <div className="task-actions">
                      <button
                        className="btn-primary"
                        onClick={() => handleGenerateFromSavedContent(content.task_id)}
                        disabled={loading}
                      >
                        {loading ? '生成中...' : '⚡ 快速生成PPT'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : showTasks ? (
          <div className="tasks-container">
            <div className="tasks-header">
              <h2>已提取的文档</h2>
              <button
                className="btn-text"
                onClick={() => setShowTasks(false)}
              >
                返回上传
              </button>
            </div>

            {tasks.length === 0 ? (
              <div className="empty-state">
                <p>暂无已提取的文档</p>
              </div>
            ) : (
              <div className="tasks-list">
                {tasks.map((task) => (
                  <div key={task.task_id} className="task-item">
                    <div className="task-info">
                      <h3>任务 ID: {task.task_id.slice(0, 8)}...</h3>
                      <div className="task-details">
                        <span>📄 {task.markdown_size ? `${(task.markdown_size / 1024).toFixed(1)} KB` : '未知大小'}</span>
                        {task.image_count !== undefined && (
                          <span>🖼️ {task.image_count} 张图片</span>
                        )}
                      </div>
                    </div>
                    <div className="task-actions">
                      <button
                        className="btn-secondary"
                        onClick={() => handlePreviewNotes(task.task_id)}
                        disabled={loading}
                      >
                        {loading ? '加载中...' : '👁️ 预览笔记'}
                      </button>
                      <button
                        className="btn-primary"
                        onClick={() => handleGenerateFromTask(task.task_id, 'notes')}
                        disabled={loading}
                      >
                        {loading ? '生成中...' : '📝 笔记'}
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleGenerateFromTask(task.task_id, 'ppt')}
                        disabled={loading}
                      >
                        {loading ? '生成中...' : '📊 PPT'}
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleGenerateMarpPPT(task.task_id)}
                        disabled={loading}
                      >
                        {loading ? '生成中...' : '✨ Marp PPT'}
                      </button>
                      <button
                        className="btn-secondary"
                        onClick={() => handleGenerateFromTask(task.task_id, 'both')}
                        disabled={loading}
                      >
                        {loading ? '生成中...' : '📚 全部'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            <FileUploadWithMode
              onFileSelect={handleFileSelect}
              loading={loading}
            />

            {error && (
              <div className="error-message">
                ❌ {error}
              </div>
            )}

            {loading && (
              <div className="loading-container">
                <div className="spinner"></div>
                <p>正在处理您的文档，请稍候...</p>
              </div>
            )}

            {notesData && !loading && (
              <div className="notes-container">
                <div className="notes-header">
                  <h2>📝 生成的笔记</h2>
                  <div className="metadata">
                    {notesData.metadata.source === 'existing_task' && (
                      <span className="badge">来自已提取文档</span>
                    )}
                    {notesData.metadata.original_filename && (
                      <span>文件: {notesData.metadata.original_filename}</span>
                    )}
                    <span>模型: {notesData.metadata.model}</span>
                    <span>
                      tokens: {notesData.metadata.tokens_used.toLocaleString()}
                    </span>
                  </div>
                </div>
                <PaperNotesViewer
                  content={notesData.notes}
                  taskId={notesData.metadata.task_id}
                  showNotePanel={false}
                />
              </div>
            )}

            {pptData && !loading && (
              <PPTViewer
                downloadUrl={pptData.download_url}
                taskId={pptData.task_id || ''}
                metadata={pptData.metadata}
              />
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default App
