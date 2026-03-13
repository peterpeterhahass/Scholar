import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'
import 'katex/dist/katex.min.css'
import './PaperNotesViewer.css'

interface PaperNotesViewerProps {
  content: string
  taskId?: string
}

interface SectionNotes {
  [key: string]: string
}

interface ParsedSection {
  title: string
  content: string
}

export default function PaperNotesViewer({ content, taskId }: PaperNotesViewerProps) {
  const [userNotes, setUserNotes] = useState<SectionNotes>({})
  const [activeSection, setActiveSection] = useState<string>('')

  // 转换图片路径
  const convertImagePaths = (markdown: string) => {
    if (!taskId) return markdown
    // 将相对路径转换为 API 路径
    return markdown.replace(
      /!\[\]\(images\/([^)]+)\)/g,
      `![](/api/images/${taskId}/$1)`
    )
  }

  const processedContent = convertImagePaths(content)

  // 从 localStorage 加载用户笔记
  useEffect(() => {
    if (taskId) {
      const saved = localStorage.getItem(`paper_notes_${taskId}`)
      if (saved) {
        setUserNotes(JSON.parse(saved))
      }
    }
  }, [taskId])

  // 保存用户笔记到 localStorage
  const saveUserNote = (section: string, note: string) => {
    const updated = { ...userNotes, [section]: note }
    setUserNotes(updated)
    if (taskId) {
      localStorage.setItem(`paper_notes_${taskId}`, JSON.stringify(updated))
    }
  }

  // 解析内容，提取各个章节
  const parseContent = (markdown: string): ParsedSection[] => {
    const sections = markdown.split(/^## /m)
    const parsed: ParsedSection[] = []

    for (let i = 0; i < sections.length; i++) {
      if (i === 0) {
        // 第一部分是标题之前的内容（如果有），跳过
        continue
      }
      const section = sections[i]
      const lines = section.split('\n')
      const title = lines[0].trim()
      const content = lines.slice(1).join('\n').trim()
      if (title) {
        parsed.push({ title, content })
      }
    }

    return parsed
  }

  const sections = parseContent(processedContent)

  // 生成 section ID
  const getSectionId = (title: string) => {
    return title.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '_')
  }

  if (sections.length === 0) {
    return <div className="paper-notes-loading">正在解析笔记...</div>
  }

  return (
    <div className="paper-notes-container">
      {/* 左侧：论文笔记 */}
      <div className="paper-notes-left">
        <div className="paper-notes-header">
          <h2>📄 论文笔记</h2>
        </div>
        <div className="paper-notes-content">
          {sections.map((section, index) => {
            const sectionId = getSectionId(section.title)

            return (
              <div
                key={index}
                id={`section-${sectionId}`}
                className="paper-note-section"
              >
                <h3 className="section-title">{section.title}</h3>
                <div className="section-content">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm, remarkMath]}
                    rehypePlugins={[rehypeKatex]}
                    components={{
                      h1: ({ children }) => <h1>{children}</h1>,
                      h2: ({ children }) => <h2>{children}</h2>,
                      h3: ({ children }) => <h3>{children}</h3>,
                      h4: ({ children }) => <h4>{children}</h4>,
                      p: ({ children }) => <p>{children}</p>,
                      ul: ({ children }) => <ul>{children}</ul>,
                      ol: ({ children }) => <ol>{children}</ol>,
                      li: ({ children }) => <li>{children}</li>,
                      code: ({ className, children, ...props }) => {
                        const match = /language-(\w+)/.exec(className || '')
                        return match ? (
                          <code className={className} {...props}>
                            {children}
                          </code>
                        ) : (
                          <code className="inline-code" {...props}>
                            {children}
                          </code>
                        )
                      },
                      pre: ({ children }) => <pre>{children}</pre>,
                      blockquote: ({ children }) => <blockquote>{children}</blockquote>,
                      strong: ({ children }) => <strong>{children}</strong>,
                      em: ({ children }) => <em>{children}</em>,
                      img: ({ src, alt }) => (
                        <img src={src} alt={alt} className="markdown-image" />
                      ),
                    }}
                  >
                    {section.content}
                  </ReactMarkdown>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 右侧：用户笔记区域 */}
      <div className="paper-notes-right">
        <div className="user-notes-header">
          <h3>✏️ 我的笔记</h3>
          <p className="user-notes-hint">点击左侧章节，在这里记录您的想法和疑问</p>
        </div>
        <div className="user-notes-content">
          {sections.map((section, index) => {
            const sectionId = getSectionId(section.title)
            const isActive = activeSection === sectionId

            return (
              <div
                key={index}
                className={`user-note-section ${isActive ? 'active' : ''}`}
                onClick={() => setActiveSection(sectionId)}
              >
                <div className="user-note-title">{section.title}</div>
                <textarea
                  className="user-note-input"
                  placeholder="在这里记录您的想法、疑问或补充..."
                  value={userNotes[sectionId] || ''}
                  onChange={(e) => saveUserNote(sectionId, e.target.value)}
                  onClick={(e) => e.stopPropagation()}
                />
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
