import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import templateApi, { exportApi } from '../services/api'

const GridType = {
  TIANZI: '田字格',
  MIZI: '米字格',
  HUIGONG: '回宫格',
  FANGGE: '方格',
}

const DEFAULT_GRID_COLOR = '#000000'

function CopybookEditor({ config, onConfigChange }) {
  const canvasRef = useRef(null)
  const safeConfig = config && typeof config === 'object' ? config : {}
  const [inputText, setInputText] = useState(String(safeConfig.input_text ?? ''))
  const [gridType, setGridType] = useState(safeConfig.grid_type ?? GridType.TIANZI)
  const [gridColor, setGridColor] = useState(
    /^#[0-9A-Fa-f]{6}$/.test(safeConfig.grid_color) ? safeConfig.grid_color : DEFAULT_GRID_COLOR
  )
  const [fontStyle, setFontStyle] = useState(safeConfig.font_style ?? 'zhenkai')
  const [studentName, setStudentName] = useState(String(safeConfig.student_name ?? ''))
  const [studentId, setStudentId] = useState(String(safeConfig.student_id ?? ''))
  const [className, setClassName] = useState(String(safeConfig.class_name ?? ''))
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [newTemplateName, setNewTemplateName] = useState('')
  const [saving, setSaving] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [templates, setTemplates] = useState([])
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [loadingTemplates, setLoadingTemplates] = useState(false)

  const gridSize = 60

  const fetchTemplates = useCallback(async () => {
    setLoadingTemplates(true)
    try {
      const data = await templateApi.getAll()
      setTemplates(data || [])
    } catch (err) {
      console.error('获取模版列表失败:', err)
    } finally {
      setLoadingTemplates(false)
    }
  }, [])

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  useEffect(() => {
    if (config && typeof config === 'object') {
      setInputText(String(config.input_text ?? ''))
      setGridType(config.grid_type ?? GridType.TIANZI)
      setGridColor(/^#[0-9A-Fa-f]{6}$/.test(config.grid_color) ? config.grid_color : DEFAULT_GRID_COLOR)
      setFontStyle(config.font_style ?? 'zhenkai')
      setStudentName(String(config.student_name ?? ''))
      setStudentId(String(config.student_id ?? ''))
      setClassName(String(config.class_name ?? ''))
    }
  }, [config])

  const handleSelectTemplate = useCallback((templateId) => {
    setSelectedTemplateId(templateId)
    if (!templateId) return

    const numericId = Number(templateId)
    const template = templates.find((t) => t.template_id === numericId)
    if (template && template.config_data) {
      const configData = template.config_data
      setGridType(configData.grid_type ?? GridType.TIANZI)
      setGridColor(/^#[0-9A-Fa-f]{6}$/.test(configData.grid_color) ? configData.grid_color : DEFAULT_GRID_COLOR)
      setFontStyle(configData.font_style ?? 'zhenkai')
      setStudentName(String(configData.student_name ?? ''))
      setStudentId(String(configData.student_id ?? ''))
      setClassName(String(configData.class_name ?? ''))
      setInputText(String(configData.input_text ?? ''))
      alert('模版已应用')
    }
  }, [templates])

  useEffect(() => {
    const newConfig = {
      input_text: inputText,
      grid_type: gridType,
      grid_color: gridColor,
      grid_size: gridSize,
      font_style: fontStyle,
      student_name: studentName,
      student_id: studentId,
      class_name: className,
    }
    if (onConfigChange) {
      onConfigChange(newConfig)
    }
  }, [inputText, gridType, gridColor, fontStyle, studentName, studentId, className, onConfigChange])

  const hexToRgba = (hex, alpha) => {
    const validHex = /^#[0-9A-Fa-f]{6}$/.test(hex) ? hex : DEFAULT_GRID_COLOR
    const r = parseInt(validHex.slice(1, 3), 16)
    const g = parseInt(validHex.slice(3, 5), 16)
    const b = parseInt(validHex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }

  const drawGrid = useCallback((ctx, x, y, size, type, color, character = '', isTemplate = false) => {
    if (isTemplate && character) {
      ctx.fillStyle = '#f5f5f5'
      ctx.fillRect(x, y, size, size)
    }

    ctx.strokeStyle = hexToRgba(color, 0.7)
    ctx.lineWidth = 1
    ctx.strokeRect(x, y, size, size)

    ctx.strokeStyle = hexToRgba(color, 0.4)

    if (type === GridType.TIANZI || type === GridType.MIZI) {
      ctx.beginPath()
      ctx.moveTo(x, y + size / 2)
      ctx.lineTo(x + size, y + size / 2)
      ctx.stroke()

      ctx.beginPath()
      ctx.moveTo(x + size / 2, y)
      ctx.lineTo(x + size / 2, y + size)
      ctx.stroke()
    }

    if (type === GridType.MIZI) {
      ctx.beginPath()
      ctx.moveTo(x, y)
      ctx.lineTo(x + size, y + size)
      ctx.stroke()

      ctx.beginPath()
      ctx.moveTo(x + size, y)
      ctx.lineTo(x, y + size)
      ctx.stroke()
    }

    if (type === GridType.HUIGONG) {
      const innerMargin = Math.floor(size / 5)
      ctx.strokeRect(
        x + innerMargin,
        y + innerMargin,
        size - innerMargin * 2,
        size - innerMargin * 2
      )
    }

    if (character) {
      ctx.font = `${Math.floor(size * 0.7)}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = isTemplate ? '#b4b4b4' : '#646464'
      ctx.fillText(character, x + size / 2, y + size / 2)
    }
  }, [])

  const invalidChars = useMemo(() => {
    return (inputText || '')
      .split('')
      .filter((char) => {
        if (
          /^[\u4e00-\u9fff\u3400-\u4dbf]$/.test(char) ||
          /^[a-zA-Z0-9]$/.test(char) ||
          /^\s$/.test(char)
        ) {
          return false
        }
        return true
      })
  }, [inputText])

  const validChars = useMemo(() => {
    return (inputText || '')
      .split('')
      .filter((char) => {
        if (
          /^[\u4e00-\u9fff\u3400-\u4dbf]$/.test(char) ||
          /^[a-zA-Z0-9]$/.test(char)
        ) {
          return true
        }
        return false
      })
  }, [inputText])

  const generatePreview = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height

    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, width, height)

    const hasStudentInfo = studentName || studentId || className
    const headerHeight = hasStudentInfo ? 30 : 0
    const padding = 5
    const size = gridSize
    const gridPadding = 5

    const contentHeight = height - headerHeight - padding * 2
    const cols = Math.max(1, Math.floor((width - padding * 2) / (size + gridPadding)))
    const maxRows = Math.max(1, Math.floor(contentHeight / (size + gridPadding)))

    if (hasStudentInfo) {
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'right'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = '#333'

      const infoParts = []
      if (studentName) infoParts.push(`姓名：${studentName}`)
      if (studentId) infoParts.push(`学号：${studentId}`)
      if (className) infoParts.push(`班级：${className}`)

      const infoText = infoParts.join('  ')
      const x = width - padding
      const y = headerHeight / 2

      ctx.fillText(infoText, x, y)
    }

    const contentTopY = headerHeight + padding

    if (validChars.length === 0) {
      for (let row = 0; row < maxRows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = padding + col * (size + gridPadding)
          const y = contentTopY + row * (size + gridPadding)
          if (x + size <= width && y + size <= height) {
            drawGrid(ctx, x, y, size, gridType, gridColor)
          }
        }
      }
      return
    }

    let rowIndex = 0
    let charIndex = 0
    const totalChars = validChars.length

    while (charIndex < totalChars && rowIndex < maxRows) {
      const currentChar = validChars[charIndex]

      for (let col = 0; col < cols; col++) {
        const x = padding + col * (size + gridPadding)
        const y = contentTopY + row * (size + gridPadding)

        if (x + size > width || y + size > height) {
          continue
        }

        const isTemplate = col === 0
        const charToDraw = isTemplate ? currentChar : ''

        drawGrid(ctx, x, y, size, gridType, gridColor, charToDraw, isTemplate)
      }

      charIndex++
      rowIndex++
    }
  }, [validChars, gridType, gridColor, drawGrid, gridSize, studentName, studentId, className])

  useEffect(() => {
    generatePreview()
  }, [generatePreview])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const resizeCanvas = () => {
      const parent = canvas.parentElement
      if (parent) {
        canvas.width = parent.clientWidth - 10
        canvas.height = parent.clientHeight - 10
        generatePreview()
      }
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    const timer = setTimeout(resizeCanvas, 100)

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      clearTimeout(timer)
    }
  }, [generatePreview])

  const handleSaveTemplate = async () => {
    if (!newTemplateName.trim()) {
      alert('请输入模版名称')
      return
    }

    setSaving(true)
    try {
      const templateData = {
        template_name: newTemplateName.trim(),
        config_data: {
          grid_type: gridType,
          grid_color: gridColor,
          font_style: fontStyle,
          grid_size: gridSize,
          student_name: studentName,
          student_id: studentId,
          class_name: className,
          input_text: inputText,
        },
      }
      await templateApi.create(templateData)
      setNewTemplateName('')
      setShowSaveDialog(false)
      alert('模版保存成功')
      fetchTemplates()
    } catch (err) {
      alert(`保存失败: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleOpenExportDialog = () => {
    if (validChars.length === 0) {
      alert('请先输入汉字')
      return
    }
    setShowExportDialog(true)
  }

  const handleExport = async () => {
    if (validChars.length === 0) {
      alert('请先输入汉字')
      return
    }

    setExporting(true)
    try {
      const exportData = {
        characters: validChars,
        grid_type: gridType,
        grid_color: gridColor,
        font_style: fontStyle,
        student_name: studentName,
        student_id: studentId,
        class_name: className,
      }
      await exportApi.exportPdf(exportData)
      setShowExportDialog(false)
      alert('PDF导出成功')
    } catch (err) {
      alert(`导出失败: ${err.message}`)
    } finally {
      setExporting(false)
    }
  }

  const gridTypes = [
    { value: GridType.TIANZI, label: '田字格' },
    { value: GridType.MIZI, label: '米字格' },
    { value: GridType.HUIGONG, label: '回宫格' },
    { value: GridType.FANGGE, label: '方格' },
  ]

  const fontStyles = [
    { value: 'zhenkai', label: '正楷' },
    { value: 'xingkai', label: '行楷' },
  ]

  return (
    <div className="editor-container">
      <div className="editor-left">
        <div className="section">
          <h3 className="section-title">选择模版</h3>
          <div className="form-group">
            <select
              className="form-select"
              value={selectedTemplateId}
              onChange={(e) => handleSelectTemplate(e.target.value)}
              disabled={loadingTemplates || templates.length === 0}
            >
              <option value="">-- 选择模版 --</option>
              {templates.map((template) => (
                <option key={template.template_id} value={template.template_id}>
                  {template.template_name}
                </option>
              ))}
            </select>
            {templates.length === 0 && !loadingTemplates && (
              <p className="input-hint" style={{ marginTop: '8px' }}>
                暂无保存的模版，请先保存模版
              </p>
            )}
          </div>
        </div>

        <div className="section">
          <h3 className="section-title">输入文字</h3>
          <textarea
            className="text-input"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="请输入文字（支持中文、英文、数字）"
            rows={6}
          />
          {invalidChars.length > 0 && (
            <p className="input-error">
              输入包含不支持的字符：{invalidChars.slice(0, 5).join('、')}
              {invalidChars.length > 5 && ' 等'}
              <br />
              仅支持：中文、英文、数字
            </p>
          )}
        </div>

        <div className="section">
          <h3 className="section-title">学生信息</h3>
          <div className="form-group">
            <label className="form-label">姓名</label>
            <input
              type="text"
              className="form-input"
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              placeholder="请输入姓名"
            />
          </div>
          <div className="form-group">
            <label className="form-label">学号</label>
            <input
              type="text"
              className="form-input"
              value={studentId}
              onChange={(e) => {
                const value = e.target.value
                if (/^[a-zA-Z0-9]*$/.test(value)) {
                  setStudentId(value)
                }
              }}
              placeholder="请输入学号（仅支持数字和英文）"
            />
          </div>
          <div className="form-group">
            <label className="form-label">班级</label>
            <input
              type="text"
              className="form-input"
              value={className}
              onChange={(e) => setClassName(e.target.value)}
              placeholder="请输入班级"
            />
          </div>
        </div>

        <div className="section">
          <h3 className="section-title">格子类型</h3>
          <div className="form-group">
            <select
              className="form-select"
              value={gridType}
              onChange={(e) => setGridType(e.target.value)}
            >
              {gridTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <h3 className="section-title" style={{ marginTop: '16px' }}>格子颜色</h3>
          <div className="form-group">
            <div className="color-input-row">
              <input
                type="color"
                className="color-picker-input"
                value={gridColor}
                onChange={(e) => setGridColor(e.target.value)}
              />
              <input
                type="text"
                className="form-input color-hex-input"
                value={gridColor}
                onChange={(e) => {
                  const val = e.target.value
                  if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                    setGridColor(val.length === 7 ? val : gridColor)
                  }
                }}
                onBlur={(e) => {
                  const val = e.target.value
                  if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                    setGridColor(val)
                  }
                }}
              />
            </div>
          </div>
        </div>

        <div className="section">
          <h3 className="section-title">字体样式</h3>
          <div className="form-group">
            <select
              className="form-select"
              value={fontStyle}
              onChange={(e) => setFontStyle(e.target.value)}
            >
              {fontStyles.map((style) => (
                <option key={style.value} value={style.value}>
                  {style.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="section">
          <button
            className="btn btn-primary"
            style={{ width: '100%', marginBottom: '12px' }}
            onClick={handleOpenExportDialog}
          >
            导出PDF字帖
          </button>
          <button
            className="btn btn-secondary"
            style={{ width: '100%' }}
            onClick={() => setShowSaveDialog(true)}
          >
            保存模版
          </button>
        </div>
      </div>

      <div className="editor-right">
        <div className="preview-header">
          <h3 className="section-title">预览</h3>
        </div>
        <div className="preview-container">
          <canvas ref={canvasRef} className="preview-canvas" />
        </div>
      </div>

      {showSaveDialog && (
        <div className="modal-overlay" onClick={() => setShowSaveDialog(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>保存为模版</h3>
              <button
                className="modal-close"
                onClick={() => setShowSaveDialog(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <label className="form-label">模版名称</label>
              <input
                type="text"
                className="form-input"
                value={newTemplateName}
                onChange={(e) => setNewTemplateName(e.target.value)}
                placeholder="请输入模版名称"
                autoFocus
              />
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowSaveDialog(false)}
              >
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSaveTemplate}
                disabled={saving || !newTemplateName.trim()}
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showExportDialog && (
        <div className="modal-overlay" onClick={() => setShowExportDialog(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>导出PDF字帖</h3>
              <button
                className="modal-close"
                onClick={() => setShowExportDialog(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">导出预览</label>
                <div style={{ padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                  <p style={{ fontSize: '13px', margin: '4px 0' }}>
                    字符数量：<strong>{validChars.length} 个</strong>
                  </p>
                  <p style={{ fontSize: '13px', margin: '4px 0' }}>
                    字符：<strong>{validChars.slice(0, 10).join('')}{validChars.length > 10 ? '...' : ''}</strong>
                  </p>
                  <p style={{ fontSize: '13px', margin: '4px 0' }}>
                    格子类型：<strong>{gridType}</strong>
                  </p>
                  <p style={{ fontSize: '13px', margin: '4px 0' }}>
                    格子颜色：<span style={{
                      display: 'inline-block',
                      width: '14px',
                      height: '14px',
                      borderRadius: '2px',
                      backgroundColor: gridColor,
                      marginRight: '4px',
                      marginLeft: '4px',
                      verticalAlign: 'middle',
                      border: '1px solid #ddd',
                    }} /><strong>{gridColor}</strong>
                  </p>
                  <p style={{ fontSize: '13px', margin: '4px 0' }}>
                    字体样式：<strong>{fontStyle === 'xingkai' ? '行楷' : '正楷'}</strong>
                  </p>
                </div>
              </div>

              {(studentName || studentId || className) && (
                <div className="form-group">
                  <label className="form-label" style={{ fontWeight: '600' }}>页眉信息（将显示在PDF顶部）</label>
                  <div style={{ padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                    {studentName && <p style={{ fontSize: '13px', margin: '4px 0' }}>姓名：{studentName}</p>}
                    {className && <p style={{ fontSize: '13px', margin: '4px 0' }}>班级：{className}</p>}
                    {studentId && <p style={{ fontSize: '13px', margin: '4px 0' }}>学号：{studentId}</p>}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowExportDialog(false)}
              >
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={handleExport}
                disabled={exporting || validChars.length === 0}
              >
                {exporting ? '导出中...' : '导出'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CopybookEditor
