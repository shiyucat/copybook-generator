import React, { useState, useCallback, useRef, useEffect } from 'react'

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
  const [gridSize, setGridSize] = useState(config.grid_size || 60)
  const [studentName, setStudentName] = useState(config.student_name || '')
  const [studentId, setStudentId] = useState(config.student_id || '')
  const [className, setClassName] = useState(config.class_name || '')

  useEffect(() => {
    if (config) {
      setInputText(config.input_text || '')
      setGridType(config.grid_type || GridType.TIANZI)
      setGridSize(config.grid_size || 60)
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
      student_name: studentName,
      student_id: studentId,
      class_name: className,
    }
    if (onConfigChange) {
      onConfigChange(newConfig)
    }
  }, [inputText, gridType, gridSize, studentName, studentId, className, onConfigChange])

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

    const cols = Math.max(1, Math.floor((width - padding * 2) / (size + padding)))
    const maxRows = Math.max(1, Math.floor((height - padding * 2) / (size + padding)))

    const validChars = (inputText || '')
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

    if (validChars.length === 0) {
      for (let row = 0; row < maxRows; row++) {
        for (let col = 0; col < cols; col++) {
          const x = padding + col * (size + padding)
          const y = padding + row * (size + padding)
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
        const x = padding + col * (size + padding)
        const y = padding + rowIndex * (size + padding)

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
  }, [inputText, gridType, gridSize, drawGrid])

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

  const gridTypes = [
    { value: GridType.TIANZI, label: '田字格' },
    { value: GridType.MIZI, label: '米字格' },
    { value: GridType.HUIGONG, label: '回宫格' },
    { value: GridType.FANGGE, label: '方格' },
  ]

  return (
    <div className="editor-container">
      <div className="editor-left">
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
          <h3 className="section-title">格子设置</h3>
          <div className="form-group">
            <label className="form-label">格子大小: {gridSize}px</label>
            <input
              type="range"
              min="30"
              max="100"
              value={gridSize}
              onChange={(e) => setGridSize(parseInt(e.target.value))}
              className="slider"
            />
          </div>
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
    </div>
  )
}

export default CopybookEditor
