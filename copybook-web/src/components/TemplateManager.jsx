import React, { useState, useEffect, useCallback } from 'react'
import templateApi from '../services/api'

const DEFAULT_SHOW_PINYIN = false
const DEFAULT_LINES_PER_CHAR = 1

const PAGE_SIZE_OPTIONS = [10, 20, 40, 100]

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
      onApplyTemplate(template.config_data)
    }
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
    </div>
  )
}

export default TemplateManager
