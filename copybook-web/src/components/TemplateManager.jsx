import React, { useState, useEffect, useCallback } from 'react'
import templateApi from '../services/api'

const DEFAULT_SHOW_PINYIN = false
const DEFAULT_LINES_PER_CHAR = 1

const PAGE_SIZE_OPTIONS = [10, 20, 40, 100]

const GridType = {
  TIANZI: '田字格',
  MIZI: '米字格',
  HUIGONG: '回宫格',
  FANGGE: '方格',
}

const PageSize = {
  A4: { name: 'A4', width: 210, height: 297 },
  SIZE_16K: { name: '16开', width: 185, height: 260 },
  A5: { name: 'A5', width: 148, height: 210 },
  B5: { name: 'B5', width: 176, height: 250 },
}

const GridSizeOptions = [
  { value: 2.0, label: '2.0 cm (幼小衔接)', isDefault: true },
  { value: 1.8, label: '1.8 cm (小学 1-2 年级 推荐)' },
  { value: 1.5, label: '1.5 cm (小学 3-6 年级)' },
  { value: 1.2, label: '1.2 cm (初中 / 成人行楷)' },
  { value: 1.0, label: '1.0 cm (小楷密集版)' },
]

const DEFAULT_GRID_COLOR = '#000000'
const DEFAULT_FONT_COLOR = '#000000'
const DEFAULT_PINYIN_COLOR = '#000000'
const DEFAULT_CHARACTER_COLOR = '#000000'
const DEFAULT_RIGHT_GRID_COLOR = '#000000'
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

function TemplateManager({ onApplyTemplate }) {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedTemplate, setSelectedTemplate] = useState(null)

  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 10,
    total: 0,
    total_pages: 1,
  })

  const [showEditDialog, setShowEditDialog] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState(null)
  const [editForm, setEditForm] = useState({
    template_name: '',
    scene_type: SceneType.NORMAL,
    grid_type: GridType.TIANZI,
    grid_color: DEFAULT_GRID_COLOR,
    grid_size_cm: 2.0,
    lines_per_char: 1,
    show_pinyin: false,
    pinyin_color: DEFAULT_PINYIN_COLOR,
    font_style: 'zhenkai',
    font_color: DEFAULT_FONT_COLOR,
    student_name: '',
    student_id: '',
    class_name: '',
    page_size: 'A4',
    show_character_pinyin: DEFAULT_SHOW_CHARACTER_PINYIN,
    character_color: DEFAULT_CHARACTER_COLOR,
    right_grid_color: DEFAULT_RIGHT_GRID_COLOR,
    right_grid_type: DEFAULT_RIGHT_GRID_TYPE,
  })
  const [savingEdit, setSavingEdit] = useState(false)

  const fetchTemplates = useCallback(async (page = 1, size = pageSize) => {
    setLoading(true)
    setError(null)
    try {
      const result = await templateApi.getPaginated(page, size)
      setTemplates(result.data || [])
      setPagination(result.pagination)
      setCurrentPage(result.pagination.page)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [pageSize])

  useEffect(() => {
    fetchTemplates(currentPage, pageSize)
  }, [fetchTemplates, currentPage, pageSize])

  const handlePageSizeChange = (newSize) => {
    setPageSize(newSize)
    setCurrentPage(1)
  }

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      setCurrentPage(newPage)
    }
  }

  const handleDeleteTemplate = async (template) => {
    if (!window.confirm(`确定要删除模版「${template.template_name}」吗？\n此操作不可恢复。`)) {
      return
    }

    try {
      await templateApi.delete(template.template_id)
      const remainingOnPage = templates.length - 1
      if (remainingOnPage === 0 && currentPage > 1) {
        setCurrentPage(Math.max(1, currentPage - 1))
      } else {
        fetchTemplates(currentPage, pageSize)
      }
      if (selectedTemplate?.template_id === template.template_id) {
        setSelectedTemplate(null)
      }
    } catch (err) {
      alert(`删除失败: ${err.message}`)
    }
  }

  const handleApplyTemplate = (template) => {
    if (onApplyTemplate) {
      onApplyTemplate(template)
    }
  }

  const handleEditTemplate = (template) => {
    setEditingTemplate(template)
    const configData = template.config_data || {}
    setEditForm({
      template_name: template.template_name,
      scene_type: configData.scene_type ?? SceneType.NORMAL,
      grid_type: configData.grid_type ?? GridType.TIANZI,
      grid_color: /^#[0-9A-Fa-f]{6}$/.test(configData.grid_color) ? configData.grid_color : DEFAULT_GRID_COLOR,
      grid_size_cm: configData.grid_size_cm ?? 2.0,
      lines_per_char: configData.lines_per_char ?? DEFAULT_LINES_PER_CHAR,
      show_pinyin: configData.show_pinyin ?? DEFAULT_SHOW_PINYIN,
      pinyin_color: /^#[0-9A-Fa-f]{6}$/.test(configData.pinyin_color) ? configData.pinyin_color : DEFAULT_PINYIN_COLOR,
      font_style: configData.font_style ?? 'zhenkai',
      font_color: /^#[0-9A-Fa-f]{6}$/.test(configData.font_color) ? configData.font_color : DEFAULT_FONT_COLOR,
      student_name: String(configData.student_name ?? ''),
      student_id: String(configData.student_id ?? ''),
      class_name: String(configData.class_name ?? ''),
      page_size: configData.page_size ?? 'A4',
      show_character_pinyin: configData.show_character_pinyin !== undefined 
        ? configData.show_character_pinyin 
        : DEFAULT_SHOW_CHARACTER_PINYIN,
      character_color: /^#[0-9A-Fa-f]{6}$/.test(configData.character_color) 
        ? configData.character_color 
        : DEFAULT_CHARACTER_COLOR,
      right_grid_color: /^#[0-9A-Fa-f]{6}$/.test(configData.right_grid_color) 
        ? configData.right_grid_color 
        : DEFAULT_RIGHT_GRID_COLOR,
      right_grid_type: configData.right_grid_type ?? DEFAULT_RIGHT_GRID_TYPE,
    })
    setShowEditDialog(true)
  }

  const handleSaveEdit = async () => {
    if (!editForm.template_name.trim()) {
      alert('请输入模版名称')
      return
    }

    setSavingEdit(true)
    try {
      const updateData = {
        template_name: editForm.template_name.trim(),
        config_data: {
          scene_type: editForm.scene_type,
          grid_type: editForm.grid_type,
          grid_color: editForm.grid_color,
          grid_size_cm: editForm.grid_size_cm,
          lines_per_char: editForm.lines_per_char,
          show_pinyin: editForm.show_pinyin,
          pinyin_color: editForm.pinyin_color,
          font_style: editForm.font_style,
          font_color: editForm.font_color,
          grid_size: 60,
          student_name: editForm.student_name,
          student_id: editForm.student_id,
          class_name: editForm.class_name,
          page_size: editForm.page_size,
          show_character_pinyin: editForm.show_character_pinyin,
          character_color: editForm.character_color,
          right_grid_color: editForm.right_grid_color,
          right_grid_type: editForm.right_grid_type,
        },
      }

      await templateApi.update(editingTemplate.template_id, updateData)
      setShowEditDialog(false)
      setEditingTemplate(null)
      alert('模版保存成功')
      fetchTemplates(currentPage, pageSize)
    } catch (err) {
      alert(`保存失败: ${err.message}`)
    } finally {
      setSavingEdit(false)
    }
  }

  const handleEditFormChange = (field, value) => {
    setEditForm((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const formatDateTime = (dateStr) => {
    if (!dateStr) return ''
    try {
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    } catch {
      return dateStr.replace('T', ' ').split('.')[0]
    }
  }

  const renderPagination = () => {
    if (pagination.total <= 0) return null

    const { page, total_pages, total } = pagination
    const hasPrev = page > 1
    const hasNext = page < total_pages

    return (
      <div className="pagination-wrapper" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 0',
        borderTop: '1px solid #e0e0e0',
        marginTop: '16px',
      }}>
        <div className="pagination-info" style={{ fontSize: '13px', color: '#666' }}>
          共 <strong>{total}</strong> 条模版
        </div>

        <div className="pagination-controls" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', color: '#666' }}>每页:</span>
            <select
              value={pageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              style={{
                padding: '4px 8px',
                borderRadius: '4px',
                border: '1px solid #ccc',
                fontSize: '13px',
              }}
            >
              {PAGE_SIZE_OPTIONS.map((size) => (
                <option key={size} value={size}>{size} 条</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <button
              className="pagination-btn"
              onClick={() => handlePageChange(1)}
              disabled={!hasPrev}
              style={{
                padding: '6px 10px',
                fontSize: '12px',
                borderRadius: '4px',
                border: '1px solid #ddd',
                backgroundColor: hasPrev ? '#fff' : '#f5f5f5',
                color: hasPrev ? '#333' : '#999',
                cursor: hasPrev ? 'pointer' : 'not-allowed',
              }}
            >
              首页
            </button>
            <button
              className="pagination-btn"
              onClick={() => handlePageChange(page - 1)}
              disabled={!hasPrev}
              style={{
                padding: '6px 10px',
                fontSize: '12px',
                borderRadius: '4px',
                border: '1px solid #ddd',
                backgroundColor: hasPrev ? '#fff' : '#f5f5f5',
                color: hasPrev ? '#333' : '#999',
                cursor: hasPrev ? 'pointer' : 'not-allowed',
              }}
            >
              上一页
            </button>

            <span style={{ padding: '0 12px', fontSize: '13px', color: '#333' }}>
              第 <strong>{page}</strong> 页 / 共 {total_pages} 页
            </span>

            <button
              className="pagination-btn"
              onClick={() => handlePageChange(page + 1)}
              disabled={!hasNext}
              style={{
                padding: '6px 10px',
                fontSize: '12px',
                borderRadius: '4px',
                border: '1px solid #ddd',
                backgroundColor: hasNext ? '#fff' : '#f5f5f5',
                color: hasNext ? '#333' : '#999',
                cursor: hasNext ? 'pointer' : 'not-allowed',
              }}
            >
              下一页
            </button>
            <button
              className="pagination-btn"
              onClick={() => handlePageChange(total_pages)}
              disabled={!hasNext}
              style={{
                padding: '6px 10px',
                fontSize: '12px',
                borderRadius: '4px',
                border: '1px solid #ddd',
                backgroundColor: hasNext ? '#fff' : '#f5f5f5',
                color: hasNext ? '#333' : '#999',
                cursor: hasNext ? 'pointer' : 'not-allowed',
              }}
            >
              末页
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="template-manager">
      <div className="template-header">
        <h2>模版管理</h2>
        {pagination.total > 0 && (
          <span style={{ fontSize: '13px', color: '#666', marginLeft: '12px' }}>
            共 {pagination.total} 条记录
          </span>
        )}
      </div>

      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error-message">
          {error}
          <button className="btn btn-secondary" onClick={() => fetchTemplates(1, pageSize)}>
            重试
          </button>
        </div>
      ) : templates.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📂</div>
          <h3>暂无保存的模版</h3>
          <p>在字帖编辑页面点击「保存模版」按钮创建新模版</p>
        </div>
      ) : (
        <>
          <div className="template-list">
            {templates.map((template) => {
              const configData = template.config_data || {}
              const showPinyin = configData.show_pinyin ?? DEFAULT_SHOW_PINYIN
              const linesPerChar = configData.lines_per_char ?? DEFAULT_LINES_PER_CHAR

              return (
                <div
                  key={template.template_id}
                  className={`template-card ${selectedTemplate?.template_id === template.template_id ? 'selected' : ''}`}
                  onClick={() => setSelectedTemplate(template)}
                >
                  <div className="template-card-header">
                    <h3 className="template-name">{template.template_name}</h3>
                    <div className="template-actions">
                      <button
                        className="btn btn-sm btn-apply"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleApplyTemplate(template)
                        }}
                        title="应用此模版"
                      >
                        应用
                      </button>
                      <button
                        className="btn btn-sm btn-apply"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleEditTemplate(template)
                        }}
                        title="编辑此模版"
                        style={{ backgroundColor: '#4caf50' }}
                      >
                        编辑
                      </button>
                      <button
                        className="btn btn-sm btn-delete"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteTemplate(template)
                        }}
                        title="删除此模版"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                  <div className="template-meta">
                    <span>创建时间: {formatDateTime(template.created_at)}</span>
                    {template.updated_at !== template.created_at && (
                      <span>更新时间: {formatDateTime(template.updated_at)}</span>
                    )}
                  </div>
                  {selectedTemplate?.template_id === template.template_id && (
                    <div className="template-detail">
                      <h4>配置详情</h4>
                      <div className="config-grid">
                        <div className="config-item">
                          <span className="config-label">场景类型:</span>
                          <span className="config-value">
                            {SceneTypeLabels[configData.scene_type] || '普通练字场景'}
                          </span>
                        </div>
                        {configData.input_text && (
                          <div className="config-item" style={{ gridColumn: 'span 2' }}>
                            <span className="config-label">文字内容:</span>
                            <span className="config-value" style={{
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              maxWidth: '200px',
                            }}>
                              {configData.input_text.length > 20 
                                ? configData.input_text.substring(0, 20) + '...' 
                                : configData.input_text}
                            </span>
                          </div>
                        )}
                        {configData.scene_type === SceneType.CHARACTER && (
                          <>
                            <div className="config-item">
                              <span className="config-label">拼音显示:</span>
                              <span className="config-value">
                                {configData.show_character_pinyin !== false ? '开启' : '关闭'}
                              </span>
                            </div>
                            {configData.show_character_pinyin !== false && (
                              <div className="config-item">
                                <span className="config-label">拼音颜色:</span>
                                <span className="config-value">
                                  <span
                                    className="color-swatch-small"
                                    style={{
                                      display: 'inline-block',
                                      width: '16px',
                                      height: '16px',
                                      borderRadius: '3px',
                                      backgroundColor: configData.pinyin_color || '#000000',
                                      marginRight: '6px',
                                      verticalAlign: 'middle',
                                      border: '1px solid #ddd',
                                    }}
                                  />
                                  {configData.pinyin_color || '#000000'}
                                </span>
                              </div>
                            )}
                            <div className="config-item">
                              <span className="config-label">生字颜色:</span>
                              <span className="config-value">
                                <span
                                  className="color-swatch-small"
                                  style={{
                                    display: 'inline-block',
                                    width: '16px',
                                    height: '16px',
                                    borderRadius: '3px',
                                    backgroundColor: configData.character_color || '#000000',
                                    marginRight: '6px',
                                    verticalAlign: 'middle',
                                    border: '1px solid #ddd',
                                  }}
                                />
                                {configData.character_color || '#000000'}
                              </span>
                            </div>
                            <div className="config-item">
                              <span className="config-label">右侧格子类型:</span>
                              <span className="config-value">
                                {configData.right_grid_type || '米字格'}
                              </span>
                            </div>
                            <div className="config-item">
                              <span className="config-label">右侧格子颜色:</span>
                              <span className="config-value">
                                <span
                                  className="color-swatch-small"
                                  style={{
                                    display: 'inline-block',
                                    width: '16px',
                                    height: '16px',
                                    borderRadius: '3px',
                                    backgroundColor: configData.right_grid_color || '#000000',
                                    marginRight: '6px',
                                    verticalAlign: 'middle',
                                    border: '1px solid #ddd',
                                  }}
                                />
                                {configData.right_grid_color || '#000000'}
                              </span>
                            </div>
                            <div className="config-item">
                              <span className="config-label">左侧生字框颜色:</span>
                              <span className="config-value">
                                <span
                                  className="color-swatch-small"
                                  style={{
                                    display: 'inline-block',
                                    width: '16px',
                                    height: '16px',
                                    borderRadius: '3px',
                                    backgroundColor: configData.grid_color || '#000000',
                                    marginRight: '6px',
                                    verticalAlign: 'middle',
                                    border: '1px solid #ddd',
                                  }}
                                />
                                {configData.grid_color || '#000000'}
                              </span>
                            </div>
                          </>
                        )}
                        {configData.scene_type !== SceneType.CHARACTER && (
                          <>
                            <div className="config-item">
                              <span className="config-label">格子大小:</span>
                              <span className="config-value">
                                {configData.grid_size_cm || '2.0'} cm
                              </span>
                            </div>
                            <div className="config-item">
                              <span className="config-label">格子类型:</span>
                              <span className="config-value">
                                {configData.grid_type || '田字格'}
                              </span>
                            </div>
                            <div className="config-item">
                              <span className="config-label">每个字的行数:</span>
                              <span className="config-value">
                                {linesPerChar} 行
                              </span>
                            </div>
                            <div className="config-item">
                              <span className="config-label">拼音显示:</span>
                              <span className="config-value">
                                {showPinyin ? '开启' : '关闭'}
                              </span>
                            </div>
                            {showPinyin && (
                              <div className="config-item">
                                <span className="config-label">拼音颜色:</span>
                                <span className="config-value">
                                  <span
                                    className="color-swatch-small"
                                    style={{
                                      display: 'inline-block',
                                      width: '16px',
                                      height: '16px',
                                      borderRadius: '3px',
                                      backgroundColor: configData.pinyin_color || '#000000',
                                      marginRight: '6px',
                                      verticalAlign: 'middle',
                                      border: '1px solid #ddd',
                                    }}
                                  />
                                  {configData.pinyin_color || '#000000'}
                                </span>
                              </div>
                            )}
                            <div className="config-item">
                              <span className="config-label">格子颜色:</span>
                              <span className="config-value">
                                <span
                                  className="color-swatch-small"
                                  style={{
                                    display: 'inline-block',
                                    width: '16px',
                                    height: '16px',
                                    borderRadius: '3px',
                                    backgroundColor: configData.grid_color || '#000000',
                                    marginRight: '6px',
                                    verticalAlign: 'middle',
                                    border: '1px solid #ddd',
                                  }}
                                />
                                {configData.grid_color || '#000000'}
                              </span>
                            </div>
                            <div className="config-item">
                              <span className="config-label">字体样式:</span>
                              <span className="config-value">
                                {configData.font_style === 'xingkai' ? '行楷' : '正楷'}
                              </span>
                            </div>
                          </>
                        )}
                        {configData.page_size && (
                          <div className="config-item">
                            <span className="config-label">页面大小:</span>
                            <span className="config-value">
                              {configData.page_size === 'SIZE_16K' ? '16开' : configData.page_size}
                            </span>
                          </div>
                        )}
                        {configData.student_name && (
                          <div className="config-item">
                            <span className="config-label">姓名:</span>
                            <span className="config-value">
                              {configData.student_name}
                            </span>
                          </div>
                        )}
                        {configData.student_id && (
                          <div className="config-item">
                            <span className="config-label">学号:</span>
                            <span className="config-value">
                              {configData.student_id}
                            </span>
                          </div>
                        )}
                        {configData.class_name && (
                          <div className="config-item">
                            <span className="config-label">班级:</span>
                            <span className="config-value">
                              {configData.class_name}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
          {renderPagination()}
        </>
      )}

      {showEditDialog && (
        <div className="modal-overlay" onClick={() => setShowEditDialog(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px', maxHeight: '90vh', overflow: 'auto' }}>
            <div className="modal-header">
              <h3>编辑模版</h3>
              <button
                className="modal-close"
                onClick={() => setShowEditDialog(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body" style={{ padding: '16px' }}>
              <div className="form-group">
                <label className="form-label">模版名称</label>
                <input
                  type="text"
                  className="form-input"
                  value={editForm.template_name}
                  onChange={(e) => handleEditFormChange('template_name', e.target.value)}
                  placeholder="请输入模版名称"
                />
              </div>

              <div className="form-group">
                <label className="form-label">场景类型</label>
                <select
                  className="form-select"
                  value={editForm.scene_type}
                  disabled
                  style={{ backgroundColor: '#f5f5f5', cursor: 'not-allowed' }}
                >
                  {Object.entries(SceneTypeLabels).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              {editForm.scene_type === SceneType.CHARACTER && (
                <>
                  <div className="form-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={editForm.show_character_pinyin}
                        onChange={(e) => handleEditFormChange('show_character_pinyin', e.target.checked)}
                        className="checkbox-input"
                      />
                      <span className="checkbox-text">显示拼音（开启后在生字框上方显示）</span>
                    </label>
                  </div>

                  {editForm.show_character_pinyin && (
                    <div className="form-group">
                      <label className="form-label">拼音颜色</label>
                      <div className="color-input-row">
                        <input
                          type="color"
                          className="color-picker-input"
                          value={editForm.pinyin_color}
                          onChange={(e) => handleEditFormChange('pinyin_color', e.target.value)}
                        />
                        <input
                          type="text"
                          className="form-input color-hex-input"
                          value={editForm.pinyin_color}
                          onChange={(e) => {
                            const val = e.target.value
                            if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                              handleEditFormChange('pinyin_color', val.length === 7 ? val : editForm.pinyin_color)
                            }
                          }}
                          onBlur={(e) => {
                            const val = e.target.value
                            if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                              handleEditFormChange('pinyin_color', val)
                            }
                          }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="form-group">
                    <label className="form-label">生字颜色</label>
                    <div className="color-input-row">
                      <input
                        type="color"
                        className="color-picker-input"
                        value={editForm.character_color}
                        onChange={(e) => handleEditFormChange('character_color', e.target.value)}
                      />
                      <input
                        type="text"
                        className="form-input color-hex-input"
                        value={editForm.character_color}
                        onChange={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                            handleEditFormChange('character_color', val.length === 7 ? val : editForm.character_color)
                          }
                        }}
                        onBlur={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                            handleEditFormChange('character_color', val)
                          }
                        }}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">右侧格子类型</label>
                    <select
                      className="form-select"
                      value={editForm.right_grid_type}
                      onChange={(e) => handleEditFormChange('right_grid_type', e.target.value)}
                    >
                      <option value={GridType.TIANZI}>田字格</option>
                      <option value={GridType.MIZI}>米字格</option>
                      <option value={GridType.HUIGONG}>回宫格</option>
                      <option value={GridType.FANGGE}>方格</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">右侧格子颜色</label>
                    <div className="color-input-row">
                      <input
                        type="color"
                        className="color-picker-input"
                        value={editForm.right_grid_color}
                        onChange={(e) => handleEditFormChange('right_grid_color', e.target.value)}
                      />
                      <input
                        type="text"
                        className="form-input color-hex-input"
                        value={editForm.right_grid_color}
                        onChange={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                            handleEditFormChange('right_grid_color', val.length === 7 ? val : editForm.right_grid_color)
                          }
                        }}
                        onBlur={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                            handleEditFormChange('right_grid_color', val)
                          }
                        }}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">左侧生字框颜色</label>
                    <div className="color-input-row">
                      <input
                        type="color"
                        className="color-picker-input"
                        value={editForm.grid_color}
                        onChange={(e) => handleEditFormChange('grid_color', e.target.value)}
                      />
                      <input
                        type="text"
                        className="form-input color-hex-input"
                        value={editForm.grid_color}
                        onChange={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                            handleEditFormChange('grid_color', val.length === 7 ? val : editForm.grid_color)
                          }
                        }}
                        onBlur={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                            handleEditFormChange('grid_color', val)
                          }
                        }}
                      />
                    </div>
                  </div>
                </>
              )}

              {editForm.scene_type !== SceneType.CHARACTER && (
                <>
                  <div className="form-group">
                    <label className="form-label">格子类型</label>
                    <select
                      className="form-select"
                      value={editForm.grid_type}
                      onChange={(e) => handleEditFormChange('grid_type', e.target.value)}
                    >
                      <option value={GridType.TIANZI}>田字格</option>
                      <option value={GridType.MIZI}>米字格</option>
                      <option value={GridType.HUIGONG}>回宫格</option>
                      <option value={GridType.FANGGE}>方格</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">格子大小</label>
                    <select
                      className="form-select"
                      value={editForm.grid_size_cm}
                      onChange={(e) => handleEditFormChange('grid_size_cm', parseFloat(e.target.value))}
                    >
                      {GridSizeOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">每个字的行数</label>
                    <input
                      type="number"
                      className="form-input"
                      value={editForm.lines_per_char}
                      onChange={(e) => {
                        const val = parseInt(e.target.value, 10)
                        if (!isNaN(val) && val >= 1 && val <= 50) {
                          handleEditFormChange('lines_per_char', val)
                        } else if (e.target.value === '') {
                          handleEditFormChange('lines_per_char', 1)
                        }
                      }}
                      min={1}
                      max={50}
                      placeholder="请输入行数（1-50）"
                    />
                  </div>

                  <div className="form-group">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={editForm.show_pinyin}
                        onChange={(e) => handleEditFormChange('show_pinyin', e.target.checked)}
                        className="checkbox-input"
                      />
                      <span className="checkbox-text">显示拼音</span>
                    </label>
                  </div>

                  {editForm.show_pinyin && (
                    <div className="form-group">
                      <label className="form-label">拼音颜色</label>
                      <div className="color-input-row">
                        <input
                          type="color"
                          className="color-picker-input"
                          value={editForm.pinyin_color}
                          onChange={(e) => handleEditFormChange('pinyin_color', e.target.value)}
                        />
                        <input
                          type="text"
                          className="form-input color-hex-input"
                          value={editForm.pinyin_color}
                          onChange={(e) => {
                            const val = e.target.value
                            if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                              handleEditFormChange('pinyin_color', val.length === 7 ? val : editForm.pinyin_color)
                            }
                          }}
                          onBlur={(e) => {
                            const val = e.target.value
                            if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                              handleEditFormChange('pinyin_color', val)
                            }
                          }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="form-group">
                    <label className="form-label">格子颜色</label>
                    <div className="color-input-row">
                      <input
                        type="color"
                        className="color-picker-input"
                        value={editForm.grid_color}
                        onChange={(e) => handleEditFormChange('grid_color', e.target.value)}
                      />
                      <input
                        type="text"
                        className="form-input color-hex-input"
                        value={editForm.grid_color}
                        onChange={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                            handleEditFormChange('grid_color', val.length === 7 ? val : editForm.grid_color)
                          }
                        }}
                        onBlur={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                            handleEditFormChange('grid_color', val)
                          }
                        }}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">字体样式</label>
                    <select
                      className="form-select"
                      value={editForm.font_style}
                      onChange={(e) => handleEditFormChange('font_style', e.target.value)}
                    >
                      <option value="zhenkai">正楷</option>
                      <option value="xingkai">行楷</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">字体颜色</label>
                    <div className="color-input-row">
                      <input
                        type="color"
                        className="color-picker-input"
                        value={editForm.font_color}
                        onChange={(e) => handleEditFormChange('font_color', e.target.value)}
                      />
                      <input
                        type="text"
                        className="form-input color-hex-input"
                        value={editForm.font_color}
                        onChange={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                            handleEditFormChange('font_color', val.length === 7 ? val : editForm.font_color)
                          }
                        }}
                        onBlur={(e) => {
                          const val = e.target.value
                          if (/^#[0-9A-Fa-f]{6}$/.test(val)) {
                            handleEditFormChange('font_color', val)
                          }
                        }}
                      />
                    </div>
                  </div>
                </>
              )}

              <div className="form-group">
                <label className="form-label">页面大小</label>
                <select
                  className="form-select"
                  value={editForm.page_size}
                  onChange={(e) => handleEditFormChange('page_size', e.target.value)}
                >
                  {Object.entries(PageSize).map(([key, size]) => (
                    <option key={key} value={key}>
                      {size.name} ({size.width}×{size.height}mm)
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">学生信息（可选）</label>
                <input
                  type="text"
                  className="form-input"
                  style={{ marginBottom: '8px' }}
                  value={editForm.student_name}
                  onChange={(e) => handleEditFormChange('student_name', e.target.value)}
                  placeholder="姓名（可选）"
                />
                <input
                  type="text"
                  className="form-input"
                  style={{ marginBottom: '8px' }}
                  value={editForm.student_id}
                  onChange={(e) => {
                    const value = e.target.value
                    if (/^[a-zA-Z0-9]*$/.test(value)) {
                      handleEditFormChange('student_id', value)
                    }
                  }}
                  placeholder="学号（仅支持数字和英文，可选）"
                />
                <input
                  type="text"
                  className="form-input"
                  value={editForm.class_name}
                  onChange={(e) => handleEditFormChange('class_name', e.target.value)}
                  placeholder="班级（可选）"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowEditDialog(false)}
              >
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSaveEdit}
                disabled={savingEdit || !editForm.template_name.trim()}
              >
                {savingEdit ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TemplateManager
