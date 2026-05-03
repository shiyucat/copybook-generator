import React, { useState, useEffect, useCallback } from 'react'
import templateApi from '../services/api'

const SceneType = {
  NORMAL: 'normal',
  CHARACTER: 'character',
}

const SceneTypeLabels = {
  [SceneType.NORMAL]: '普通练字场景',
  [SceneType.CHARACTER]: '生字场景',
}

function AssignmentDialog({ student, onClose, onAssign }) {
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [characters, setCharacters] = useState('')
  const [assigning, setAssigning] = useState(false)

  const fetchTemplates = useCallback(async () => {
    setLoading(true)
    try {
      const result = await templateApi.getPaginated(1, 100)
      setTemplates(result.data || [])
    } catch (err) {
      console.error('获取模版失败:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  const handleAssign = async () => {
    if (!selectedTemplate) {
      alert('请选择一个模版')
      return
    }
    if (!characters.trim()) {
      alert('请输入需要练习的字')
      return
    }

    setAssigning(true)
    try {
      if (onAssign) {
        await onAssign({
          student,
          template: selectedTemplate,
          characters: characters.trim(),
        })
      }
      onClose && onClose()
    } catch (err) {
      alert(`布置作业失败: ${err.message}`)
    } finally {
      setAssigning(false)
    }
  }

  const getSceneTypeLabel = (template) => {
    const configData = template.config_data || {}
    return SceneTypeLabels[configData.scene_type] || '普通练字场景'
  }

  const getTemplatePreview = (template) => {
    const configData = template.config_data || {}
    const gridType = configData.grid_type || '田字格'
    const gridSize = configData.grid_size_cm || 2.0
    const fontStyle = configData.font_style === 'xingkai' ? '行楷' : '正楷'
    return `${gridType} · ${gridSize}cm · ${fontStyle}`
  }

  return (
    <div className="modal-overlay" onClick={() => onClose && onClose()}>
      <div 
        className="modal" 
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '700px', width: '90vw', maxHeight: '90vh', overflow: 'auto' }}
      >
        <div className="modal-header">
          <h3>布置作业</h3>
          {student && (
            <div style={{ fontSize: '14px', color: '#666' }}>
              学生: <strong>{student.name}</strong> ({student.student_no})
              {student.class_name && ` · ${student.class_name}班`}
            </div>
          )}
          <button
            className="modal-close"
            onClick={() => onClose && onClose()}
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="form-group">
            <label className="form-label">选择模版 *</label>
            {loading ? (
              <div className="loading" style={{ padding: '40px' }}>加载模版中...</div>
            ) : templates.length === 0 ? (
              <div className="empty-state" style={{ padding: '30px', background: '#f9f9f9', borderRadius: '8px' }}>
                <p>暂无保存的模版</p>
                <p style={{ fontSize: '12px', color: '#888' }}>请先在模版管理中创建模版</p>
              </div>
            ) : (
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                gap: '12px',
                maxHeight: '300px',
                overflow: 'auto',
                padding: '4px',
              }}>
                {templates.map((template) => {
                  const isSelected = selectedTemplate?.template_id === template.template_id
                  return (
                    <div
                      key={template.template_id}
                      onClick={() => setSelectedTemplate(template)}
                      style={{
                        padding: '12px',
                        border: isSelected ? '2px solid #4CAF50' : '1px solid #e0e0e0',
                        borderRadius: '8px',
                        backgroundColor: isSelected ? '#f1f8e9' : '#fff',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                    >
                      <div style={{ 
                        fontWeight: 'bold', 
                        fontSize: '14px',
                        marginBottom: '6px',
                        color: isSelected ? '#2e7d32' : '#333',
                      }}>
                        {template.template_name}
                      </div>
                      <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                        {getSceneTypeLabel(template)}
                      </div>
                      <div style={{ fontSize: '12px', color: '#888' }}>
                        {getTemplatePreview(template)}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {selectedTemplate && (
            <div style={{ 
              padding: '12px', 
              background: '#e8f5e9', 
              borderRadius: '8px', 
              marginBottom: '16px',
              border: '1px solid #c8e6c9',
            }}>
              <div style={{ fontWeight: 'bold', color: '#2e7d32', marginBottom: '4px' }}>
                已选择: {selectedTemplate.template_name}
              </div>
              <div style={{ fontSize: '12px', color: '#558b2f' }}>
                {getSceneTypeLabel(selectedTemplate)} · {getTemplatePreview(selectedTemplate)}
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">练习文字 *</label>
            <textarea
              className="form-input"
              value={characters}
              onChange={(e) => setCharacters(e.target.value)}
              placeholder="请输入需要练习的汉字，例如：一二三四五"
              rows={4}
              style={{ resize: 'vertical', minHeight: '100px' }}
            />
            <div style={{ 
              marginTop: '8px', 
              fontSize: '12px', 
              color: '#888',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}>
              <span>建议每行输入 10-15 个汉字</span>
              <span>已输入 <strong style={{ color: characters.length > 0 ? '#4CAF50' : '#888' }}>
                {characters.length}
              </strong> 个字</span>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button
            className="btn btn-secondary"
            onClick={() => onClose && onClose()}
            disabled={assigning}
          >
            取消
          </button>
          <button
            className="btn btn-primary"
            onClick={handleAssign}
            disabled={assigning || !selectedTemplate || !characters.trim()}
          >
            {assigning ? '布置中...' : '确认布置'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default AssignmentDialog
