import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import templateApi, { exportApi } from '../services/api'

const GridType = {
  TIANZI: '田字格',
  MIZI: '米字格',
  HUIGONG: '回宫格',
  FANGGE: '方格',
}

function CopybookEditor({ config, onConfigChange }) {
  const canvasRef = useRef(null)
  const [inputText, setInputText] = useState(config.input_text || '')
  const [gridType, setGridType] = useState(config.grid_type || GridType.TIANZI)
  const [fontStyle, setFontStyle] = useState(config.font_style || 'zhenkai')
  const [studentName, setStudentName] = useState(config.student_name || '')
  const [studentId, setStudentId] = useState(config.student_id || '')
  const [className, setClassName] = useState(config.class_name || '')
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [newTemplateName, setNewTemplateName] = useState('')
  const [saving, setSaving] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [exportCharacter, setExportCharacter] = useState('')
  const [exportPages, setExportPages] = useState(1)
  const [exporting, setExporting] = useState(false)

  const gridSize = 60

  useEffect(() => {
    if (config) {
      setInputText(config.input_text || '')
      setGridType(config.grid_type || GridType.TIANZI)
      setFontStyle(config.font_style || 'zhenkai')
      setStudentName(config.student_name || '')
      setStudentId(config.student_id || '')
      setClassName(config.class_name || '')
    }
  }, [config])

  useEffect(() => {
    const newConfig = {
      input_text: inputText,
      grid_type: gridType,
      grid_size: gridSize,
      font_style: fontStyle,
      student_name: studentName,
      student_id: studentId,
      class_name: className,
    }
    if (onConfigChange) {
      onConfigChange(newConfig)
    }
  }, [inputText, gridType, fontStyle, studentName, studentId, className, onConfigChange])

  const drawGrid = useCallback((ctx, x, y, size, type, character = '', isTemplate = false) => {
    if (isTemplate && character) {
      ctx.fillStyle = '#f5f5f5'
      ctx.fillRect(x, y, size, size)
    }

    ctx.strokeStyle = '#808080'
    ctx.lineWidth = 1
    ctx.strokeRect(x, y, size, size)

    ctx.strokeStyle = '#c8c8c8'

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

    const padding = 5
    const size = gridSize
    const gridPadding = 5

    const cols = Math.max(1, Math.floor((width - padding * 2) / (size + gridPadding)))
    const maxRows = Math.max(1, Math.floor((height - padding * 2) / (size + gridPadding)))

    if (validChars.length === 0) {
      for (let row = 0; row < maxRows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = padding + col * (size + gridPadding)
          const y = padding + row * (size + gridPadding)
          if (x + size <= width && y + size <= height) {
            drawGrid(ctx, x, y, size, gridType)
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
        const y = padding + rowIndex * (size + gridPadding)

        if (x + size > width || y + size > height) {
          continue
        }

        const isTemplate = col === 0
        const charToDraw = isTemplate ? currentChar : ''

        drawGrid(ctx, x, y, size, gridType, charToDraw, isTemplate)
      }

      charIndex++
      rowIndex++
    }
  }, [validChars, gridType, drawGrid, gridSize])

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
          font_style: fontStyle,
          grid_size: gridSize,
          student_name: studentName,
          student_id: studentId,
          class_name: className,
        },
      }
      await templateApi.create(templateData)
      setNewTemplateName('')
      setShowSaveDialog(false)
      alert('模版保存成功')
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
    setExportCharacter(validChars[0])
    setShowExportDialog(true)
  }

  const handleExport = async () => {
    if (!exportCharacter) {
      alert('请选择要生成字帖的汉字')
      return
    }

    setExporting(true)
    try {
      const exportData = {
        character: exportCharacter,
        grid_type: gridType,
        font_style: fontStyle,
        pages: exportPages,
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
          <h3 className="section-title">输入文字</h3>
          <textarea
            className="text-input"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="请输入文字（支持中文、英文、数字）"
            rows={6}
          />
          <p className="input-hint">
            支持：中文、英文、数字<br />
            空格和换行不占格<br />
            不支持：标点符号、特殊字符
          </p>
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
              onChange={(e) => setStudentId(e.target.value)}
              placeholder="请输入学号"
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
          <div className="radio-group">
            {gridTypes.map((type) => (
              <label key={type.value} className="radio-label">
                <input
                  type="radio"
                  name="gridType"
                  value={type.value}
                  checked={gridType === type.value}
                  onChange={(e) => setGridType(e.target.value)}
                />
                <span>{type.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="section">
          <h3 className="section-title">字体样式</h3>
          <div className="radio-group">
            {fontStyles.map((style) => (
              <label key={style.value} className="radio-label">
                <input
                  type="radio"
                  name="fontStyle"
                  value={style.value}
                  checked={fontStyle === style.value}
                  onChange={(e) => setFontStyle(e.target.value)}
                />
                <span>{style.label}</span>
              </label>
            ))}
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
                <label className="form-label">选择汉字</label>
                <select
                  className="form-input"
                  value={exportCharacter}
                  onChange={(e) => setExportCharacter(e.target.value)}
                >
                  {validChars.map((char, index) => (
                    <option key={index} value={char}>
                      {char}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">页数</label>
                <select
                  className="form-input"
                  value={exportPages}
                  onChange={(e) => setExportPages(parseInt(e.target.value))}
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                    <option key={n} value={n}>
                      {n} 页
                    </option>
                  ))}
                </select>
              </div>

              {(studentName || studentId || className) && (
                <div className="form-group" style={{ padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '4px' }}>
                  <label className="form-label" style={{ fontWeight: '600' }}>页眉信息（将显示在PDF顶部）</label>
                  {studentName && <p style={{ fontSize: '13px', margin: '4px 0' }}>姓名：{studentName}</p>}
                  {className && <p style={{ fontSize: '13px', margin: '4px 0' }}>班级：{className}</p>}
                  {studentId && <p style={{ fontSize: '13px', margin: '4px 0' }}>学号：{studentId}</p>}
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
                disabled={exporting || !exportCharacter}
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
