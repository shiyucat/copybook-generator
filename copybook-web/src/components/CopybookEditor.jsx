import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import templateApi, { exportApi, pinyinApi } from '../services/api'

const GridType = {
  TIANZI: '田字格',
  MIZI: '米字格',
  HUIGONG: '回宫格',
  FANGGE: '方格',
}

const DEFAULT_GRID_COLOR = '#000000'
const DEFAULT_FONT_COLOR = '#000000'
const DEFAULT_PINYIN_COLOR = '#000000'
const DEFAULT_CHARACTER_COLOR = '#000000'
const DEFAULT_RIGHT_GRID_COLOR = '#000000'
const DEFAULT_STROKE_ORDER_COLOR = '#000000'
const DEFAULT_SHOW_CHARACTER_PINYIN = true
const DEFAULT_RIGHT_GRID_TYPE = '米字格'

const SceneType = {
  NORMAL: 'normal',
  CHARACTER: 'character',
}

const SceneTypeLabels = {
  [SceneType.NORMAL]: '普通练字场景',
  [SceneType.CHARACTER]: '生字场景',
}

const PageSize = {
  A4: { name: 'A4', width: 210, height: 297 },
  SIZE_16K: { name: '16开', width: 185, height: 260 },
  A5: { name: 'A5', width: 148, height: 210 },
  B5: { name: 'B5', width: 176, height: 250 },
}

const DEFAULT_PAGE_SIZE = 'A4'

const GridSizeOptions = [
  { value: 2.0, label: '2.0 cm (幼小衔接)', isDefault: true },
  { value: 1.8, label: '1.8 cm (小学 1-2 年级 推荐)' },
  { value: 1.5, label: '1.5 cm (小学 3-6 年级)' },
  { value: 1.2, label: '1.2 cm (初中 / 成人行楷)' },
  { value: 1.0, label: '1.0 cm (小楷密集版)' },
]

const DEFAULT_GRID_SIZE_CM = 2.0
const DEFAULT_LINES_PER_CHAR = 1
const DEFAULT_SHOW_PINYIN = false

const PRINT_CONFIG = {
  MARGIN_LEFT_MM: 20,
  MARGIN_RIGHT_MM: 20,
  MARGIN_TOP_MM: 30,
  MARGIN_BOTTOM_MM: 20,
  HEADER_HEIGHT_MM: 10,
  GRID_COLS: 5,
  GRID_ROWS: 10,
  BORDER_RATIO: 0.1,
}

const CHARACTER_SCENE_CONFIG = {
  CHARACTER_BOX_SIZE_MM: 50,
  RIGHT_GRID_SIZE_MM: 20,
  GAP_SIZE_MM: 2,
  RIGHT_GRID_ROWS: 2,
  STROKE_ORDER_ROW_HEIGHT_MM: 10,
}

function CopybookEditor({ config, onConfigChange, selectedTemplateId: propSelectedTemplateId, onTemplateIdChange }) {
  const canvasRef = useRef(null)
  const safeConfig = config && typeof config === 'object' ? config : {}
  const [inputText, setInputText] = useState(String(safeConfig.input_text ?? ''))
  const [gridType, setGridType] = useState(safeConfig.grid_type ?? GridType.TIANZI)
  const [gridColor, setGridColor] = useState(
    /^#[0-9A-Fa-f]{6}$/.test(safeConfig.grid_color) ? safeConfig.grid_color : DEFAULT_GRID_COLOR
  )
  const [gridSizeCm, setGridSizeCm] = useState(safeConfig.grid_size_cm ?? DEFAULT_GRID_SIZE_CM)
  const [linesPerChar, setLinesPerChar] = useState(
    safeConfig.lines_per_char ? Math.max(1, Math.min(50, parseInt(safeConfig.lines_per_char, 10))) : DEFAULT_LINES_PER_CHAR
  )
  const [showPinyin, setShowPinyin] = useState(safeConfig.show_pinyin ?? DEFAULT_SHOW_PINYIN)
  const [pinyinColor, setPinyinColor] = useState(
    /^#[0-9A-Fa-f]{6}$/.test(safeConfig.pinyin_color) ? safeConfig.pinyin_color : DEFAULT_PINYIN_COLOR
  )
  const [fontStyle, setFontStyle] = useState(safeConfig.font_style ?? 'zhenkai')
  const [fontColor, setFontColor] = useState(
    /^#[0-9A-Fa-f]{6}$/.test(safeConfig.font_color) ? safeConfig.font_color : DEFAULT_FONT_COLOR
  )
  const [studentName, setStudentName] = useState(String(safeConfig.student_name ?? ''))
  const [studentId, setStudentId] = useState(String(safeConfig.student_id ?? ''))
  const [className, setClassName] = useState(String(safeConfig.class_name ?? ''))
  const [pageSize, setPageSize] = useState(safeConfig.page_size ?? DEFAULT_PAGE_SIZE)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [newTemplateName, setNewTemplateName] = useState('')
  const [saving, setSaving] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [templates, setTemplates] = useState([])
  const [selectedTemplateId, setSelectedTemplateId] = useState('')
  const [loadingTemplates, setLoadingTemplates] = useState(false)
  const [currentPage, setCurrentPage] = useState(0)
  const [pinyinData, setPinyinData] = useState({})
  const [loadingPinyin, setLoadingPinyin] = useState(false)
  const [sceneType, setSceneType] = useState(safeConfig.scene_type ?? SceneType.NORMAL)
  const [showCharacterPinyin, setShowCharacterPinyin] = useState(
    safeConfig.show_character_pinyin !== undefined 
      ? safeConfig.show_character_pinyin 
      : DEFAULT_SHOW_CHARACTER_PINYIN
  )
  const [characterColor, setCharacterColor] = useState(
    /^#[0-9A-Fa-f]{6}$/.test(safeConfig.character_color) 
      ? safeConfig.character_color 
      : DEFAULT_CHARACTER_COLOR
  )
  const [rightGridColor, setRightGridColor] = useState(
    /^#[0-9A-Fa-f]{6}$/.test(safeConfig.right_grid_color) 
      ? safeConfig.right_grid_color 
      : DEFAULT_RIGHT_GRID_COLOR
  )
  const [rightGridType, setRightGridType] = useState(
    safeConfig.right_grid_type ?? DEFAULT_RIGHT_GRID_TYPE
  )
  const [strokeOrderColor, setStrokeOrderColor] = useState(
    /^#[0-9A-Fa-f]{6}$/.test(safeConfig.stroke_order_color) 
      ? safeConfig.stroke_order_color 
      : DEFAULT_STROKE_ORDER_COLOR
  )

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
      setSceneType(config.scene_type ?? SceneType.NORMAL)
      setGridType(config.grid_type ?? GridType.TIANZI)
      setGridColor(/^#[0-9A-Fa-f]{6}$/.test(config.grid_color) ? config.grid_color : DEFAULT_GRID_COLOR)
      setGridSizeCm(config.grid_size_cm ?? DEFAULT_GRID_SIZE_CM)
      setLinesPerChar(
        config.lines_per_char != null 
          ? Math.max(1, Math.min(50, parseInt(config.lines_per_char, 10))) 
          : DEFAULT_LINES_PER_CHAR
      )
      setShowPinyin(config.show_pinyin ?? DEFAULT_SHOW_PINYIN)
      setPinyinColor(/^#[0-9A-Fa-f]{6}$/.test(config.pinyin_color) ? config.pinyin_color : DEFAULT_PINYIN_COLOR)
      setFontStyle(config.font_style ?? 'zhenkai')
      setFontColor(/^#[0-9A-Fa-f]{6}$/.test(config.font_color) ? config.font_color : DEFAULT_FONT_COLOR)
      setStudentName(String(config.student_name ?? ''))
      setStudentId(String(config.student_id ?? ''))
      setClassName(String(config.class_name ?? ''))
      setPageSize(config.page_size ?? DEFAULT_PAGE_SIZE)
      setShowCharacterPinyin(
        config.show_character_pinyin !== undefined 
          ? config.show_character_pinyin 
          : DEFAULT_SHOW_CHARACTER_PINYIN
      )
      setCharacterColor(
        /^#[0-9A-Fa-f]{6}$/.test(config.character_color) 
          ? config.character_color 
          : DEFAULT_CHARACTER_COLOR
      )
      setRightGridColor(
        /^#[0-9A-Fa-f]{6}$/.test(config.right_grid_color) 
          ? config.right_grid_color 
          : DEFAULT_RIGHT_GRID_COLOR
      )
      setRightGridType(config.right_grid_type ?? DEFAULT_RIGHT_GRID_TYPE)
      setStrokeOrderColor(
        /^#[0-9A-Fa-f]{6}$/.test(config.stroke_order_color) 
          ? config.stroke_order_color 
          : DEFAULT_STROKE_ORDER_COLOR
      )
    }
  }, [config])

  useEffect(() => {
    if (propSelectedTemplateId !== undefined && propSelectedTemplateId !== null) {
      const propIdStr = String(propSelectedTemplateId)
      if (propIdStr !== selectedTemplateId) {
        setSelectedTemplateId(propIdStr)
      }
    }
  }, [propSelectedTemplateId, selectedTemplateId])

  const handleSelectTemplate = useCallback((templateId) => {
    setSelectedTemplateId(templateId)
    if (onTemplateIdChange) {
      onTemplateIdChange(templateId ? Number(templateId) : null)
    }
    if (!templateId) return

    const numericId = Number(templateId)
    const template = templates.find((t) => t.template_id === numericId)
    if (template && template.config_data) {
      const configData = template.config_data
      setSceneType(configData.scene_type ?? SceneType.NORMAL)
      setGridType(configData.grid_type ?? GridType.TIANZI)
      setGridColor(/^#[0-9A-Fa-f]{6}$/.test(configData.grid_color) ? configData.grid_color : DEFAULT_GRID_COLOR)
      setGridSizeCm(configData.grid_size_cm ?? DEFAULT_GRID_SIZE_CM)
      setLinesPerChar(
        configData.lines_per_char != null 
          ? Math.max(1, Math.min(50, parseInt(configData.lines_per_char, 10))) 
          : DEFAULT_LINES_PER_CHAR
      )
      setShowPinyin(configData.show_pinyin ?? DEFAULT_SHOW_PINYIN)
      setPinyinColor(/^#[0-9A-Fa-f]{6}$/.test(configData.pinyin_color) ? configData.pinyin_color : DEFAULT_PINYIN_COLOR)
      setFontStyle(configData.font_style ?? 'zhenkai')
      setFontColor(/^#[0-9A-Fa-f]{6}$/.test(configData.font_color) ? configData.font_color : DEFAULT_FONT_COLOR)
      setStudentName(String(configData.student_name ?? ''))
      setStudentId(String(configData.student_id ?? ''))
      setClassName(String(configData.class_name ?? ''))
      setPageSize(configData.page_size ?? DEFAULT_PAGE_SIZE)
      setShowCharacterPinyin(
        configData.show_character_pinyin !== undefined 
          ? configData.show_character_pinyin 
          : DEFAULT_SHOW_CHARACTER_PINYIN
      )
      setCharacterColor(
        /^#[0-9A-Fa-f]{6}$/.test(configData.character_color) 
          ? configData.character_color 
          : DEFAULT_CHARACTER_COLOR
      )
      setRightGridColor(
        /^#[0-9A-Fa-f]{6}$/.test(configData.right_grid_color) 
          ? configData.right_grid_color 
          : DEFAULT_RIGHT_GRID_COLOR
      )
      setRightGridType(configData.right_grid_type ?? DEFAULT_RIGHT_GRID_TYPE)
      setStrokeOrderColor(
        /^#[0-9A-Fa-f]{6}$/.test(configData.stroke_order_color) 
          ? configData.stroke_order_color 
          : DEFAULT_STROKE_ORDER_COLOR
      )
      setCurrentPage(0)
      alert('模版已应用')
    }
  }, [templates, onTemplateIdChange])

  useEffect(() => {
    const newConfig = {
      input_text: inputText,
      scene_type: sceneType,
      grid_type: gridType,
      grid_color: gridColor,
      grid_size: gridSize,
      grid_size_cm: gridSizeCm,
      lines_per_char: linesPerChar,
      show_pinyin: showPinyin,
      pinyin_color: pinyinColor,
      font_style: fontStyle,
      font_color: fontColor,
      student_name: studentName,
      student_id: studentId,
      class_name: className,
      page_size: pageSize,
      show_character_pinyin: showCharacterPinyin,
      character_color: characterColor,
      right_grid_color: rightGridColor,
      right_grid_type: rightGridType,
      stroke_order_color: strokeOrderColor,
    }
    if (onConfigChange) {
      onConfigChange(newConfig)
    }
  }, [inputText, sceneType, gridType, gridColor, gridSizeCm, linesPerChar, showPinyin, pinyinColor, fontStyle, fontColor, studentName, studentId, className, pageSize, showCharacterPinyin, characterColor, rightGridColor, rightGridType, strokeOrderColor, onConfigChange])

  const hexToRgba = (hex, alpha) => {
    const validHex = /^#[0-9A-Fa-f]{6}$/.test(hex) ? hex : DEFAULT_GRID_COLOR
    const r = parseInt(validHex.slice(1, 3), 16)
    const g = parseInt(validHex.slice(3, 5), 16)
    const b = parseInt(validHex.slice(5, 7), 16)
    return `rgba(${r}, ${g}, ${b}, ${alpha})`
  }

  const drawGrid = useCallback((ctx, x, y, size, type, color, character = '', isTemplate = false, pinyin = '', showPinyin = false, fontColor = DEFAULT_FONT_COLOR, pinyinColor = DEFAULT_PINYIN_COLOR) => {
    const drawDashedLine = (ctx, x1, y1, x2, y2, dashLength = 5) => {
      const dx = x2 - x1
      const dy = y2 - y1
      const length = Math.sqrt(dx * dx + dy * dy)
      const dashCount = Math.floor(length / (dashLength * 2))
      const actualDashLength = length / (dashCount * 2)

      ctx.beginPath()
      for (let i = 0; i < dashCount; i++) {
        const startRatio = (i * 2) / (dashCount * 2)
        const endRatio = (i * 2 + 1) / (dashCount * 2)
        ctx.moveTo(x1 + dx * startRatio, y1 + dy * startRatio)
        ctx.lineTo(x1 + dx * endRatio, y1 + dy * endRatio)
      }
      ctx.stroke()
    }

    if (isTemplate && character) {
      ctx.fillStyle = '#f5f5f5'
      ctx.fillRect(x, y, size, size)
    }

    ctx.strokeStyle = hexToRgba(color, 0.7)
    ctx.lineWidth = 1

    if (showPinyin) {
      const pinyinGridHeight = size / 3
      const charGridHeight = size - pinyinGridHeight
      const charGridY = y + pinyinGridHeight

      ctx.strokeRect(x, y, size, size)

      ctx.strokeStyle = hexToRgba(color, 0.7)
      ctx.beginPath()
      ctx.moveTo(x, charGridY)
      ctx.lineTo(x + size, charGridY)
      ctx.stroke()

      ctx.strokeStyle = hexToRgba(color, 0.5)
      const line1Y = y
      const line2Y = y + pinyinGridHeight * 0.25
      const line3Y = y + pinyinGridHeight * 0.75
      const line4Y = charGridY

      if (pinyin) {
        const pinyinFontSize = Math.max(10, Math.floor(pinyinGridHeight * 0.5))
        ctx.font = `${pinyinFontSize}px sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = pinyinColor
        ctx.fillText(pinyin, x + size / 2, line2Y + (line3Y - line2Y) / 2)
      }

      ctx.strokeStyle = hexToRgba(color, 0.5)
      drawDashedLine(ctx, x, line2Y, x + size, line2Y, 3)
      drawDashedLine(ctx, x, line3Y, x + size, line3Y, 3)

      if (type === GridType.TIANZI || type === GridType.MIZI) {
        ctx.strokeStyle = hexToRgba(color, 0.4)
        ctx.beginPath()
        ctx.moveTo(x, charGridY + charGridHeight / 2)
        ctx.lineTo(x + size, charGridY + charGridHeight / 2)
        ctx.stroke()

        ctx.beginPath()
        ctx.moveTo(x + size / 2, charGridY)
        ctx.lineTo(x + size / 2, charGridY + charGridHeight)
        ctx.stroke()
      }

      if (type === GridType.MIZI) {
        ctx.strokeStyle = hexToRgba(color, 0.4)
        ctx.beginPath()
        ctx.moveTo(x, charGridY)
        ctx.lineTo(x + size, charGridY + charGridHeight)
        ctx.stroke()

        ctx.beginPath()
        ctx.moveTo(x + size, charGridY)
        ctx.lineTo(x, charGridY + charGridHeight)
        ctx.stroke()
      }

      if (type === GridType.HUIGONG) {
        ctx.strokeStyle = hexToRgba(color, 0.4)
        const innerMargin = Math.floor(charGridHeight / 5)
        ctx.strokeRect(
          x + innerMargin,
          charGridY + innerMargin,
          size - innerMargin * 2,
          charGridHeight - innerMargin * 2
        )
      }

      if (character) {
        const charFontSize = Math.floor(charGridHeight * 0.7)
        ctx.font = `${charFontSize}px sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = isTemplate ? fontColor : '#646464'
        ctx.fillText(character, x + size / 2, charGridY + charGridHeight / 2)
      }
    } else {
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
        const charFontSize = Math.floor(size * 0.7)
        ctx.font = `${charFontSize}px sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = isTemplate ? fontColor : '#646464'
        ctx.fillText(character, x + size / 2, y + size / 2)
      }
    }
  }, [])

  const drawCharacterBox = useCallback((ctx, x, y, size, color, character = '', fontColor = DEFAULT_FONT_COLOR, pinyin = '', pinyinColor = DEFAULT_PINYIN_COLOR, showPinyin = false) => {
    const outerLineWidth = 2
    const innerMargin = size * 0.15
    const tianziSize = size - 2 * innerMargin
    const tianziX = x + innerMargin
    const tianziY = y + innerMargin

    ctx.strokeStyle = hexToRgba(color, 0.8)
    ctx.lineWidth = outerLineWidth
    ctx.strokeRect(x, y, size, size)

    ctx.strokeStyle = hexToRgba(color, 0.8)
    ctx.lineWidth = 1.5
    ctx.strokeRect(tianziX, tianziY, tianziSize, tianziSize)

    ctx.strokeStyle = hexToRgba(color, 0.5)
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(tianziX, tianziY + tianziSize / 2)
    ctx.lineTo(tianziX + tianziSize, tianziY + tianziSize / 2)
    ctx.stroke()

    ctx.beginPath()
    ctx.moveTo(tianziX + tianziSize / 2, tianziY)
    ctx.lineTo(tianziX + tianziSize / 2, tianziY + tianziSize)
    ctx.stroke()

    if (showPinyin && pinyin) {
      const pinyinY = y + innerMargin / 2
      const pinyinFontSize = Math.max(12, Math.floor(innerMargin * 0.6))
      ctx.font = `${pinyinFontSize}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = pinyinColor
      ctx.fillText(pinyin, x + size / 2, pinyinY)
    }

    if (character) {
      const charFontSize = Math.floor(tianziSize * 0.7)
      ctx.font = `${charFontSize}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = fontColor
      ctx.fillText(character, tianziX + tianziSize / 2, tianziY + tianziSize / 2)
    }
  }, [])

  const STROKE_NAME_TO_CHAR = {
    '横': '一',
    '竖': '丨',
    '撇': '丿',
    '捺': '㇏',
    '点': '丶',
    '横折': '𠃍',
    '竖钩': '亅',
    '横钩': '乛',
    '撇点': '𡿨',
    '横撇': '㇇',
    '捺钩': '㇏',
    '竖折': '𠃊',
    '竖弯': '㇄',
    '横折钩': '𠃌',
    '横折提': '㇊',
    '横折弯': '㇍',
    '横折折': '㇅',
    '横折弯钩': '㇈',
    '横撇弯钩': '㇌',
    '横折折折': '㇎',
    '横折折折钩': '㇉',
    '竖提': '𠄌',
    '竖折折': '㇞',
    '竖折折钩': '㇉',
    '斜钩': '㇂',
    '卧钩': '㇃',
    '弯钩': '㇁',
    '撇折': '𠃋',
    '撇折撇': '㇋',
    '撇折点': '𡿨',
    '横斜钩': '⺄',
  }

  const getStrokeOrderText = useCallback((character) => {
    const defaultText = `笔顺：${character}`
    
    const strokesMap = {
      '一': ['横'],
      '二': ['横', '横'],
      '三': ['横', '横', '横'],
      '十': ['横', '竖'],
      '人': ['撇', '捺'],
      '大': ['横', '撇', '捺'],
      '小': ['竖钩', '点', '点'],
      '口': ['竖', '横折', '横'],
      '日': ['竖', '横折', '横', '横'],
      '月': ['撇', '横折钩', '横', '横'],
      '水': ['竖钩', '横撇', '撇', '捺'],
      '火': ['点', '撇', '撇', '捺'],
      '山': ['竖', '竖折', '竖'],
      '石': ['横', '撇', '竖', '横折', '横'],
      '田': ['竖', '横折', '横', '竖', '横'],
      '土': ['横', '竖', '横'],
      '王': ['横', '横', '竖', '横'],
      '木': ['横', '竖', '撇', '捺'],
      '禾': ['撇', '横', '竖', '撇', '捺'],
      '米': ['点', '撇', '横', '竖', '撇', '捺'],
      '竹': ['撇', '横', '点', '撇', '横', '点'],
      '鸟': ['撇', '横折钩', '点', '竖折折钩', '横'],
      '马': ['横折', '竖折折钩', '横'],
      '牛': ['撇', '横', '横', '竖'],
      '羊': ['点', '撇', '横', '横', '横', '竖'],
      '犬': ['横', '撇', '捺', '点'],
      '龙': ['横', '撇', '竖弯钩', '撇', '点'],
      '虎': ['竖', '横', '横撇', '撇', '横', '竖弯钩', '撇', '横折弯钩'],
      '心': ['点', '卧钩', '点', '点'],
      '手': ['撇', '横', '横', '竖钩'],
      '耳': ['横', '竖', '竖', '横', '横', '横'],
      '目': ['竖', '横折', '横', '横', '横'],
      '虫': ['竖', '横折', '横', '竖', '横', '点'],
      '云': ['横', '横', '撇折', '点'],
      '电': ['竖', '横折', '横', '横', '竖弯钩'],
      '雨': ['横', '竖', '横折钩', '竖', '点', '点', '点', '点'],
      '风': ['撇', '横折弯钩', '撇', '点'],
      '花': ['横', '竖', '竖', '撇', '竖', '撇', '竖弯钩'],
      '草': ['横', '竖', '竖', '竖', '横折', '横', '横', '横', '竖'],
      '树': ['横', '竖', '撇', '点', '横', '竖', '横折', '横', '横', '竖钩', '点', '点'],
      '林': ['横', '竖', '撇', '点', '横', '竖', '撇', '捺'],
      '森': ['横', '竖', '撇', '捺', '横', '竖', '撇', '点', '横', '竖', '撇', '捺'],
      '男': ['竖', '横折', '横', '竖', '横', '横折钩', '撇'],
      '女': ['撇点', '撇', '横'],
      '开': ['横', '横', '撇', '竖'],
      '关': ['点', '撇', '横', '横', '撇', '捺'],
      '正': ['横', '竖', '横', '竖', '横'],
      '反': ['撇', '横撇', '捺'],
      '文': ['点', '横', '撇', '捺'],
      '六': ['点', '横', '撇', '点'],
      '七': ['横', '竖弯钩'],
      '八': ['撇', '捺'],
      '九': ['撇', '横折弯钩'],
      '四': ['竖', '横折', '撇', '竖折', '横'],
      '五': ['横', '竖', '横折', '横'],
      '六': ['点', '横', '撇', '点'],
      '七': ['横', '竖弯钩'],
      '八': ['撇', '捺'],
      '九': ['撇', '横折弯钩'],
      '十': ['横', '竖'],
      '百': ['横', '撇', '竖', '横折', '横', '横'],
      '千': ['撇', '横', '竖'],
      '万': ['横', '横折钩', '撇'],
      '上': ['竖', '横', '横'],
      '下': ['横', '竖', '点'],
      '左': ['横', '撇', '横', '竖', '横'],
      '右': ['横', '撇', '竖', '横折', '横'],
      '中': ['竖', '横折', '横', '竖'],
      '东': ['横', '撇折', '竖钩', '撇', '点'],
      '西': ['横', '竖', '横折', '撇', '竖折', '横'],
      '南': ['横', '竖', '竖', '横折钩', '点', '撇', '横', '横', '竖'],
      '北': ['竖', '横', '提', '撇', '竖弯钩'],
      '你': ['撇', '竖', '撇', '横撇', '竖钩', '撇', '点'],
      '我': ['撇', '横', '竖钩', '提', '斜钩', '撇', '点'],
      '他': ['撇', '竖', '横折钩', '竖', '竖弯钩'],
      '们': ['撇', '竖', '点', '竖', '横折钩'],
      '说': ['点', '横折提', '点', '撇', '竖', '横折', '横', '撇', '竖弯钩'],
      '话': ['点', '横折提', '撇', '横', '竖', '竖', '横折', '横'],
      '学': ['点', '点', '撇', '点', '横撇', '横撇', '竖钩', '横'],
      '习': ['横折钩', '点', '提'],
      '校': ['横', '竖', '撇', '点', '点', '横', '撇', '捺', '撇', '捺'],
      '老': ['横', '竖', '横', '撇', '撇', '竖弯钩'],
      '师': ['竖', '撇', '横', '竖', '横折钩', '竖'],
      '好': ['撇点', '撇', '横', '横撇', '竖钩', '横'],
      '爸': ['撇', '点', '撇', '捺', '横折', '竖', '横', '竖折折钩'],
      '妈': ['撇点', '撇', '横', '横折', '竖折折钩', '横'],
      '哥': ['横', '竖', '横折', '横', '竖', '横', '竖', '横折', '横', '竖钩'],
      '弟': ['点', '撇', '横折', '横', '竖折折钩', '竖', '撇'],
      '姐': ['撇点', '撇', '横', '竖', '横折', '横', '横', '横'],
      '妹': ['撇点', '撇', '横', '横', '横', '竖', '撇', '捺'],
    }
    
    const strokes = strokesMap[character]
    if (!strokes || strokes.length === 0) {
      return defaultText
    }
    
    const strokeChars = strokes.map(s => STROKE_NAME_TO_CHAR[s] || s)
    
    if (strokeChars.length === 1) {
      return `笔顺：${character}`
    }
    
    const firstStroke = strokeChars[0]
    return `笔顺：${firstStroke}${character}`
  }, [])

  const drawStrokeOrderRow = useCallback((ctx, x, y, width, height, character, strokeOrderColor) => {
    ctx.strokeStyle = hexToRgba(strokeOrderColor, 0.5)
    ctx.lineWidth = 1
    ctx.strokeRect(x, y, width, height)
    
    const strokeOrderText = getStrokeOrderText(character)
    
    const fontSize = Math.max(12, Math.floor(height * 0.5))
    ctx.font = `${fontSize}px sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillStyle = strokeOrderColor
    
    ctx.fillText(strokeOrderText, x + width / 2, y + height / 2)
  }, [getStrokeOrderText])

  const drawCharacterRow = useCallback((ctx, x, y, rowWidth, character, pinyin, gridColor, fontColor, pinyinColor, rightGridColor, rightGridType, strokeOrderColor, mmToPx, showPinyin = false) => {
    const charBoxSize = mmToPx(CHARACTER_SCENE_CONFIG.CHARACTER_BOX_SIZE_MM)
    const gridSize = mmToPx(CHARACTER_SCENE_CONFIG.RIGHT_GRID_SIZE_MM)
    const gap = mmToPx(CHARACTER_SCENE_CONFIG.GAP_SIZE_MM)
    const rightRows = CHARACTER_SCENE_CONFIG.RIGHT_GRID_ROWS
    const strokeOrderRowHeight = mmToPx(CHARACTER_SCENE_CONFIG.STROKE_ORDER_ROW_HEIGHT_MM)

    drawCharacterBox(ctx, x, y, charBoxSize, gridColor, character, fontColor, pinyin, pinyinColor, showPinyin)

    const rightAreaX = x + charBoxSize + gap
    const rightAreaWidth = rowWidth - charBoxSize - gap

    const cols = Math.max(1, Math.floor(rightAreaWidth / gridSize))

    const rightGridsY = y
    const strokeOrderRowY = rightGridsY + rightRows * gridSize

    drawStrokeOrderRow(ctx, rightAreaX, strokeOrderRowY, cols * gridSize, strokeOrderRowHeight, character, strokeOrderColor)

    for (let row = 0; row < rightRows; row++) {
      for (let col = 0; col < cols; col++) {
        const gridX = rightAreaX + col * gridSize
        const gridY = y + row * gridSize
        
        if (gridX + gridSize <= x + rowWidth) {
          drawGrid(ctx, gridX, gridY, gridSize, rightGridType, rightGridColor)
        }
      }
    }

    return charBoxSize
  }, [drawCharacterBox, drawGrid, drawStrokeOrderRow])

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

  const calculatePageInfo = useCallback((pageNumber, validCharsArr, maxRowsParam, linesPerCharParam) => {
    if (validCharsArr.length === 0) {
      return { charIndex: 0, linesOffset: 0, totalPages: 1 }
    }

    let totalPages = 0
    let tempCharIndex = 0
    let tempLinesOffset = 0
    let tempLinesOnPage = 0

    while (tempCharIndex < validCharsArr.length) {
      const linesRemainingForChar = linesPerCharParam - tempLinesOffset
      const availableLines = maxRowsParam - tempLinesOnPage

      if (linesRemainingForChar <= availableLines) {
        tempLinesOnPage += linesRemainingForChar
        tempCharIndex++
        tempLinesOffset = 0

        if (tempLinesOnPage >= maxRowsParam || tempCharIndex >= validCharsArr.length) {
          totalPages++
          tempLinesOnPage = 0
        }
      } else {
        tempLinesOnPage = maxRowsParam
        tempLinesOffset += availableLines
        totalPages++
        tempLinesOnPage = 0
      }
    }

    totalPages = Math.max(1, totalPages)

    let currentPage = 0
    let charIndex = 0
    let linesOffset = 0
    let linesOnPage = 0

    while (currentPage < pageNumber && charIndex < validCharsArr.length) {
      const linesRemainingForChar = linesPerCharParam - linesOffset
      const availableLines = maxRowsParam - linesOnPage

      if (linesRemainingForChar <= availableLines) {
        linesOnPage += linesRemainingForChar
        charIndex++
        linesOffset = 0

        if (linesOnPage >= maxRowsParam) {
          currentPage++
          linesOnPage = 0
        }
      } else {
        linesOnPage = maxRowsParam
        linesOffset += availableLines
        currentPage++
        linesOnPage = 0
      }
    }

    return {
      charIndex: Math.min(charIndex, validCharsArr.length - 1),
      linesOffset,
      totalPages,
    }
  }, [])

  const calculateCharacterSceneLayout = useCallback(() => {
    const currentPageSize = PageSize[pageSize] || PageSize.A4
    const usableWidthMm = currentPageSize.width - PRINT_CONFIG.MARGIN_LEFT_MM - PRINT_CONFIG.MARGIN_RIGHT_MM
    const usableHeightMm = currentPageSize.height - PRINT_CONFIG.MARGIN_TOP_MM - PRINT_CONFIG.MARGIN_BOTTOM_MM
    
    const charBoxSize = CHARACTER_SCENE_CONFIG.CHARACTER_BOX_SIZE_MM
    const rightGridSize = CHARACTER_SCENE_CONFIG.RIGHT_GRID_SIZE_MM
    const rightRows = CHARACTER_SCENE_CONFIG.RIGHT_GRID_ROWS
    const strokeOrderRowHeight = CHARACTER_SCENE_CONFIG.STROKE_ORDER_ROW_HEIGHT_MM
    const gap = CHARACTER_SCENE_CONFIG.GAP_SIZE_MM
    
    const rightAreaHeight = rightGridSize * rightRows + strokeOrderRowHeight
    const rowHeightMm = Math.max(charBoxSize, rightAreaHeight) + gap
    const maxRowsPerPage = Math.max(1, Math.floor(usableHeightMm / rowHeightMm))
    
    return {
      maxRowsPerPage,
      rowHeightMm,
      usableWidthMm,
      usableHeightMm,
      charBoxSize,
      rightGridSize,
      rightRows,
      strokeOrderRowHeight,
      gap,
    }
  }, [pageSize])

  const totalPages = useMemo(() => {
    if (sceneType === SceneType.CHARACTER) {
      if (validChars.length === 0) return 1
      const { maxRowsPerPage } = calculateCharacterSceneLayout()
      return Math.max(1, Math.ceil(validChars.length / maxRowsPerPage))
    }
    
    const currentPageSize = PageSize[pageSize] || PageSize.A4
    const usableHeightMm = currentPageSize.height - PRINT_CONFIG.MARGIN_TOP_MM - PRINT_CONFIG.MARGIN_BOTTOM_MM
    const cellSizeMm = gridSizeCm * 10
    const maxRows = Math.max(1, Math.floor(usableHeightMm / cellSizeMm))
    
    return calculatePageInfo(0, validChars, maxRows, linesPerChar).totalPages
  }, [validChars, pageSize, gridSizeCm, linesPerChar, calculatePageInfo, sceneType, calculateCharacterSceneLayout])

  useEffect(() => {
    const needPinyin = (sceneType === SceneType.NORMAL && showPinyin) || 
                       (sceneType === SceneType.CHARACTER && showCharacterPinyin)
    
    if (!needPinyin || validChars.length === 0) {
      setPinyinData({})
      return
    }

    const uniqueChars = [...new Set(validChars)]
    
    const fetchPinyin = async () => {
      setLoadingPinyin(true)
      try {
        const data = await pinyinApi.getPinyin(uniqueChars)
        setPinyinData(data || {})
      } catch (err) {
        console.error('获取拼音失败:', err)
        setPinyinData({})
      } finally {
        setLoadingPinyin(false)
      }
    }

    fetchPinyin()
  }, [validChars, showPinyin, sceneType, showCharacterPinyin])

  const generatePreview = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const canvasWidth = canvas.width
    const canvasHeight = canvas.height

    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvasWidth, canvasHeight)

    const currentPageSize = PageSize[pageSize] || PageSize.A4
    const pageWidthMm = currentPageSize.width
    const pageHeightMm = currentPageSize.height

    const marginLeftMm = PRINT_CONFIG.MARGIN_LEFT_MM
    const marginRightMm = PRINT_CONFIG.MARGIN_RIGHT_MM
    const marginTopMm = PRINT_CONFIG.MARGIN_TOP_MM
    const marginBottomMm = PRINT_CONFIG.MARGIN_BOTTOM_MM

    const usableWidthMm = pageWidthMm - marginLeftMm - marginRightMm
    const usableHeightMm = pageHeightMm - marginTopMm - marginBottomMm

    const cellSizeMm = gridSizeCm * 10

    const borderWidthMm = usableWidthMm * PRINT_CONFIG.BORDER_RATIO
    const actualUsableWidthMm = usableWidthMm - 2 * borderWidthMm

    const cols = Math.max(1, Math.floor(actualUsableWidthMm / cellSizeMm))
    const maxRows = Math.max(1, Math.floor(usableHeightMm / cellSizeMm))

    const gridPaddingMm = (actualUsableWidthMm - cols * cellSizeMm) / 2 + borderWidthMm

    const pageRatio = pageWidthMm / pageHeightMm
    const canvasRatio = canvasWidth / canvasHeight

    let scale
    let offsetX = 0
    let offsetY = 0

    if (canvasRatio > pageRatio) {
      scale = canvasHeight / pageHeightMm
      offsetX = (canvasWidth - pageWidthMm * scale) / 2
    } else {
      scale = canvasWidth / pageWidthMm
      offsetY = (canvasHeight - pageHeightMm * scale) / 2
    }

    const mmToPx = (mm) => mm * scale

    const previewMarginLeft = mmToPx(marginLeftMm)
    const previewGridPadding = mmToPx(gridPaddingMm)
    const previewCellSize = mmToPx(cellSizeMm)

    ctx.save()
    ctx.beginPath()
    ctx.rect(offsetX, offsetY, mmToPx(pageWidthMm), mmToPx(pageHeightMm))
    ctx.clip()

    ctx.fillStyle = '#ffffff'
    ctx.fillRect(offsetX, offsetY, mmToPx(pageWidthMm), mmToPx(pageHeightMm))

    ctx.strokeStyle = '#e0e0e0'
    ctx.lineWidth = 1
    ctx.strokeRect(offsetX, offsetY, mmToPx(pageWidthMm), mmToPx(pageHeightMm))

    ctx.font = `${Math.max(10, mmToPx(3.5))}px sans-serif`
    ctx.textAlign = 'right'
    ctx.textBaseline = 'middle'
    ctx.fillStyle = '#333'

    const infoParts = []
    infoParts.push(`姓名：${studentName || '______'}`)
    infoParts.push(`学号：${studentId || '______'}`)
    infoParts.push(`班级：${className || '______'}`)

    const infoText = infoParts.join('  ')
    const headerX = offsetX + mmToPx(pageWidthMm - marginRightMm)
    const headerY = offsetY + mmToPx(15)

    ctx.fillText(infoText, headerX, headerY)

    if (sceneType === SceneType.CHARACTER) {
      const { maxRowsPerPage, rowHeightMm, usableWidthMm } = calculateCharacterSceneLayout()
      
      if (validChars.length === 0) {
        const previewAreaX = offsetX + previewMarginLeft
        const previewAreaY = offsetY + mmToPx(marginTopMm)
        const previewAreaWidth = mmToPx(usableWidthMm)
        const previewAreaHeight = mmToPx(usableHeightMm)

        ctx.strokeStyle = hexToRgba(gridColor, 0.3)
        ctx.lineWidth = 1
        ctx.setLineDash([5, 5])
        ctx.strokeRect(previewAreaX, previewAreaY, previewAreaWidth, previewAreaHeight)
        ctx.setLineDash([])

        ctx.font = `${Math.max(14, mmToPx(5))}px sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = '#999'
        ctx.fillText('请输入要练习的生字', previewAreaX + previewAreaWidth / 2, previewAreaY + previewAreaHeight / 2)
      } else {
        const startCharIndex = currentPage * maxRowsPerPage
        const previewAreaX = offsetX + previewMarginLeft
        const previewAreaWidth = mmToPx(usableWidthMm)
        const rowHeightPx = mmToPx(rowHeightMm)

        for (let rowOnPage = 0; rowOnPage < maxRowsPerPage; rowOnPage++) {
          const charIndex = startCharIndex + rowOnPage
          if (charIndex >= validChars.length) break

          const currentChar = validChars[charIndex]
          const charPinyin = pinyinData[currentChar] || ''
          const rowY = offsetY + mmToPx(marginTopMm) + rowOnPage * rowHeightPx

          drawCharacterRow(
            ctx,
            previewAreaX,
            rowY,
            previewAreaWidth,
            currentChar,
            charPinyin,
            gridColor,
            characterColor,
            pinyinColor,
            rightGridColor,
            rightGridType,
            strokeOrderColor,
            mmToPx,
            showCharacterPinyin
          )
        }
      }
    } else {
      if (validChars.length === 0) {
        for (let row = 0; row < maxRows; row++) {
          for (let col = 0; col < cols; col++) {
            const x = offsetX + previewMarginLeft + previewGridPadding + col * previewCellSize
            const y = offsetY + mmToPx(marginTopMm + row * cellSizeMm)
            drawGrid(ctx, x, y, previewCellSize, gridType, gridColor)
          }
        }
        ctx.restore()
        return
      }

      const pageInfo = calculatePageInfo(currentPage, validChars, maxRows, linesPerChar)
      let charIndex = pageInfo.charIndex
      let linesOffset = pageInfo.linesOffset
      let rowIndex = 0

      while (charIndex < validChars.length && rowIndex < maxRows) {
        const currentChar = validChars[charIndex]
        const charPinyin = pinyinData[currentChar] || ''

        const linesRemainingForChar = linesPerChar - linesOffset
        const linesToRenderThisPage = Math.min(linesRemainingForChar, maxRows - rowIndex)

        for (let lineRepeat = 0; lineRepeat < linesToRenderThisPage; lineRepeat++) {
          for (let col = 0; col < cols; col++) {
            const x = offsetX + previewMarginLeft + previewGridPadding + col * previewCellSize
            const y = offsetY + mmToPx(marginTopMm + rowIndex * cellSizeMm)

            const isTemplate = col === 0
            const charToDraw = isTemplate ? currentChar : ''

            drawGrid(ctx, x, y, previewCellSize, gridType, gridColor, charToDraw, isTemplate, charPinyin, showPinyin, fontColor, pinyinColor)
          }
          rowIndex++
          linesOffset++
        }

        if (linesOffset >= linesPerChar) {
          charIndex++
          linesOffset = 0
        }
      }

      while (rowIndex < maxRows) {
        for (let col = 0; col < cols; col++) {
          const x = offsetX + previewMarginLeft + previewGridPadding + col * previewCellSize
          const y = offsetY + mmToPx(marginTopMm + rowIndex * cellSizeMm)
          drawGrid(ctx, x, y, previewCellSize, gridType, gridColor)
        }
        rowIndex++
      }
    }

    ctx.restore()
  }, [validChars, gridType, gridColor, drawGrid, drawCharacterRow, calculateCharacterSceneLayout, pageSize, studentName, studentId, className, gridSizeCm, linesPerChar, currentPage, pinyinData, showPinyin, fontColor, pinyinColor, calculatePageInfo, sceneType, showCharacterPinyin, characterColor, rightGridColor, rightGridType])

  useEffect(() => {
    if (currentPage >= totalPages && totalPages > 0) {
      setCurrentPage(Math.max(0, totalPages - 1))
    }
  }, [validChars, totalPages, currentPage])

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
          scene_type: sceneType,
          grid_type: gridType,
          grid_color: gridColor,
          grid_size_cm: gridSizeCm,
          lines_per_char: linesPerChar,
          show_pinyin: showPinyin,
          pinyin_color: pinyinColor,
          font_style: fontStyle,
          font_color: fontColor,
          grid_size: gridSize,
          student_name: studentName,
          student_id: studentId,
          class_name: className,
          page_size: pageSize,
          show_character_pinyin: showCharacterPinyin,
          character_color: characterColor,
          right_grid_color: rightGridColor,
          right_grid_type: rightGridType,
          stroke_order_color: strokeOrderColor,
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
        scene_type: sceneType,
        grid_type: gridType,
        grid_color: gridColor,
        grid_size_cm: gridSizeCm,
        lines_per_char: linesPerChar,
        show_pinyin: showPinyin,
        pinyin_color: pinyinColor,
        font_style: fontStyle,
        font_color: fontColor,
        student_name: studentName,
        student_id: studentId,
        class_name: className,
        page_size: pageSize,
        show_character_pinyin: showCharacterPinyin,
        character_color: characterColor,
        right_grid_color: rightGridColor,
        right_grid_type: rightGridType,
        stroke_order_color: strokeOrderColor,
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
          <h3 className="section-title">场景选择</h3>
          <div className="form-group">
            <select
              className="form-select"
              value={sceneType}
              onChange={(e) => setSceneType(e.target.value)}
            >
              {Object.entries(SceneTypeLabels).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
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

        {sceneType === SceneType.NORMAL && (
          <>
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

              <h3 className="section-title" style={{ marginTop: '16px' }}>格子大小</h3>
              <div className="form-group">
                <select
                  className="form-select"
                  value={gridSizeCm}
                  onChange={(e) => setGridSizeCm(parseFloat(e.target.value))}
                >
                  {GridSizeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <h3 className="section-title" style={{ marginTop: '16px' }}>每个字的行数</h3>
              <div className="form-group">
                <input
                  type="number"
                  className="form-input"
                  value={linesPerChar}
                  onChange={(e) => {
                    const val = parseInt(e.target.value, 10)
                    if (!isNaN(val) && val >= 1 && val <= 50) {
                      setLinesPerChar(val)
                    } else if (e.target.value === '') {
                      setLinesPerChar(1)
                    }
                  }}
                  min={1}
                  max={50}
                  placeholder="请输入行数（1-50）"
                />
                <p className="input-hint" style={{ marginTop: '4px', fontSize: '12px' }}>
                  每个字在字帖中重复显示的行数（1-50行）
                </p>
              </div>

              <h3 className="section-title" style={{ marginTop: '16px' }}>拼音显示</h3>
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={showPinyin}
                    onChange={(e) => setShowPinyin(e.target.checked)}
                    className="checkbox-input"
                  />
                  <span className="checkbox-text">显示拼音（开启后在字帖预览中显示）</span>
                </label>
              </div>

              {showPinyin && (
                <div className="form-group">
                  <h3 className="section-title" style={{ marginTop: '12px', marginBottom: '8px' }}>拼音颜色</h3>
                  <div className="color-input-row">
                    <input
                      type="color"
                      className="color-picker-input"
                      value={pinyinColor}
                      onChange={(e) => setPinyinColor(e.target.value)}
                    />
                    <input
                      type="text"
                      className="form-input color-hex-input"
                      value={pinyinColor}
                      onChange={(e) => {
                        const val = e.target.value
                        if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                          setPinyinColor(val.length === 7 ? val : pinyinColor)
                        }
                      }}
                      onBlur={(e) => {
                        const val = e.target.value
                        if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                          setPinyinColor(val)
                        }
                      }}
                    />
                  </div>
                </div>
              )}

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

              <h3 className="section-title" style={{ marginTop: '16px' }}>字体颜色</h3>
              <div className="form-group">
                <div className="color-input-row">
                  <input
                    type="color"
                    className="color-picker-input"
                    value={fontColor}
                    onChange={(e) => setFontColor(e.target.value)}
                  />
                  <input
                    type="text"
                    className="form-input color-hex-input"
                    value={fontColor}
                    onChange={(e) => {
                      const val = e.target.value
                      if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                        setFontColor(val.length === 7 ? val : fontColor)
                      }
                    }}
                    onBlur={(e) => {
                      const val = e.target.value
                      if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                        setFontColor(val)
                      }
                    }}
                  />
                </div>
              </div>
            </div>
          </>
        )}

        {sceneType === SceneType.CHARACTER && (
          <div className="section">
            <h3 className="section-title">拼音显示</h3>
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showCharacterPinyin}
                  onChange={(e) => setShowCharacterPinyin(e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkbox-text">显示拼音（开启后在生字框上方显示）</span>
              </label>
            </div>

            {showCharacterPinyin && (
              <div className="form-group">
                <h3 className="section-title" style={{ marginTop: '12px', marginBottom: '8px' }}>拼音颜色</h3>
                <div className="color-input-row">
                  <input
                    type="color"
                    className="color-picker-input"
                    value={pinyinColor}
                    onChange={(e) => setPinyinColor(e.target.value)}
                  />
                  <input
                    type="text"
                    className="form-input color-hex-input"
                    value={pinyinColor}
                    onChange={(e) => {
                      const val = e.target.value
                      if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                        setPinyinColor(val.length === 7 ? val : pinyinColor)
                      }
                    }}
                    onBlur={(e) => {
                      const val = e.target.value
                      if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                        setPinyinColor(val)
                      }
                    }}
                  />
                </div>
              </div>
            )}

            <h3 className="section-title" style={{ marginTop: '16px' }}>生字颜色</h3>
            <div className="form-group">
              <div className="color-input-row">
                <input
                  type="color"
                  className="color-picker-input"
                  value={characterColor}
                  onChange={(e) => setCharacterColor(e.target.value)}
                />
                <input
                  type="text"
                  className="form-input color-hex-input"
                  value={characterColor}
                  onChange={(e) => {
                    const val = e.target.value
                    if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                      setCharacterColor(val.length === 7 ? val : characterColor)
                    }
                  }}
                  onBlur={(e) => {
                    const val = e.target.value
                    if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                      setCharacterColor(val)
                    }
                  }}
                />
              </div>
            </div>

            <h3 className="section-title" style={{ marginTop: '16px' }}>右侧格子类型</h3>
            <div className="form-group">
              <select
                className="form-select"
                value={rightGridType}
                onChange={(e) => setRightGridType(e.target.value)}
              >
                {gridTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <h3 className="section-title" style={{ marginTop: '16px' }}>右侧格子颜色</h3>
            <div className="form-group">
              <div className="color-input-row">
                <input
                  type="color"
                  className="color-picker-input"
                  value={rightGridColor}
                  onChange={(e) => setRightGridColor(e.target.value)}
                />
                <input
                  type="text"
                  className="form-input color-hex-input"
                  value={rightGridColor}
                  onChange={(e) => {
                    const val = e.target.value
                    if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                      setRightGridColor(val.length === 7 ? val : rightGridColor)
                    }
                  }}
                  onBlur={(e) => {
                    const val = e.target.value
                    if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                      setRightGridColor(val)
                    }
                  }}
                />
              </div>
            </div>

            <h3 className="section-title" style={{ marginTop: '16px' }}>左侧生字框颜色</h3>
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

            <h3 className="section-title" style={{ marginTop: '16px' }}>笔顺颜色</h3>
            <div className="form-group">
              <div className="color-input-row">
                <input
                  type="color"
                  className="color-picker-input"
                  value={strokeOrderColor}
                  onChange={(e) => setStrokeOrderColor(e.target.value)}
                />
                <input
                  type="text"
                  className="form-input color-hex-input"
                  value={strokeOrderColor}
                  onChange={(e) => {
                    const val = e.target.value
                    if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                      setStrokeOrderColor(val.length === 7 ? val : strokeOrderColor)
                    }
                  }}
                  onBlur={(e) => {
                    const val = e.target.value
                    if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                      setStrokeOrderColor(val)
                    }
                  }}
                />
              </div>
            </div>
          </div>
        )}

        <div className="section">
          <h3 className="section-title">页面大小</h3>
          <div className="form-group">
            <select
              className="form-select"
              value={pageSize}
              onChange={(e) => setPageSize(e.target.value)}
            >
              {Object.entries(PageSize).map(([key, size]) => (
                <option key={key} value={key}>
                  {size.name} ({size.width}×{size.height}mm)
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
        <div className="preview-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 className="section-title">预览</h3>
          <div className="pagination-controls" style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px' }}>
            <button
              className="pagination-btn"
              onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
              disabled={currentPage === 0}
              style={{ 
                padding: '4px 8px', 
                fontSize: '12px', 
                cursor: currentPage === 0 ? 'not-allowed' : 'pointer',
                opacity: currentPage === 0 ? 0.5 : 1
              }}
            >
              上一页
            </button>
            <span>第 {currentPage + 1} 页 / 共 {totalPages} 页</span>
            <button
              className="pagination-btn"
              onClick={() => setCurrentPage(Math.min(currentPage + 1, Math.max(0, totalPages - 1)))}
              disabled={currentPage >= totalPages - 1 || totalPages <= 1}
              style={{ 
                padding: '4px 8px', 
                fontSize: '12px',
                cursor: currentPage >= totalPages - 1 || totalPages <= 1 ? 'not-allowed' : 'pointer',
                opacity: currentPage >= totalPages - 1 || totalPages <= 1 ? 0.5 : 1
              }}
            >
              下一页
            </button>
          </div>
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
