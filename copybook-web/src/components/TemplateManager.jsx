import React, { useState, useEffect, useCallback } from 'react'
import templateApi from '../services/api'

function TemplateManager({ onApplyTemplate, currentConfig }) {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [newTemplateName, setNewTemplateName] = useState('')
  const [saving, setSaving] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState(null)

  const fetchTemplates = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await templateApi.getAll()
      setTemplates(data || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  const handleSaveTemplate = async () => {
    if (!newTemplateName.trim()) {
      alert('请输入模版名称')
      return
    }

    setSaving(true)
    try {
      const { input_text, ...templateConfig } = currentConfig
      const templateData = {
        template_name: newTemplateName.trim(),
        config_data: templateConfig,
      }
      await templateApi.create(templateData)
      setNewTemplateName('')
      setShowSaveDialog(false)
      fetchTemplates()
      alert('模版保存成功')
    } catch (err) {
      alert(`保存失败: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteTemplate = async (template) => {
    if (!window.confirm(`确定要删除模版「${template.template_name}」吗？\n此操作不可恢复。`)) {
      return
    }

    try {
      await templateApi.delete(template.template_id)
      fetchTemplates()
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

  return (
    <div className="template-manager">
      <div className="template-header">
        <h2>模版管理</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowSaveDialog(true)}
        >
          保存当前配置为模版
        </button>
      </div>

      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error-message">
          {error}
          <button className="btn btn-secondary" onClick={fetchTemplates}>
            重试
          </button>
        </div>
      ) : templates.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📂</div>
          <h3>暂无保存的模版</h3>
          <p>点击上方按钮保存当前配置为模版</p>
        </div>
      ) : (
        <div className="template-list">
          {templates.map((template) => (
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
                    <div className="config-item">
                      <span className="config-label">格子大小:</span>
                      <span className="config-value">
                        {template.config_data?.grid_size || '60'}px
                      </span>
                    </div>
                    <div className="config-item">
                      <span className="config-label">格子类型:</span>
                      <span className="config-value">
                        {template.config_data?.grid_type || '田字格'}
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
                            backgroundColor: template.config_data?.grid_color || '#000000',
                            marginRight: '6px',
                            verticalAlign: 'middle',
                            border: '1px solid #ddd',
                          }}
                        />
                        {template.config_data?.grid_color || '#000000'}
                      </span>
                    </div>
                    <div className="config-item">
                      <span className="config-label">字体样式:</span>
                      <span className="config-value">
                        {template.config_data?.font_style === 'xingkai' ? '行楷' : '正楷'}
                      </span>
                    </div>
                    {template.config_data?.student_name && (
                      <div className="config-item">
                        <span className="config-label">姓名:</span>
                        <span className="config-value">
                          {template.config_data.student_name}
                        </span>
                      </div>
                    )}
                    {template.config_data?.student_id && (
                      <div className="config-item">
                        <span className="config-label">学号:</span>
                        <span className="config-value">
                          {template.config_data.student_id}
                        </span>
                      </div>
                    )}
                    {template.config_data?.class_name && (
                      <div className="config-item">
                        <span className="config-label">班级:</span>
                        <span className="config-value">
                          {template.config_data.class_name}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

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
    </div>
  )
}

export default TemplateManager
