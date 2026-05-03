import React, { useState, useEffect, useCallback, useRef } from 'react'
import { assignmentApi } from '../services/api'

const PAGE_SIZE_OPTIONS = [10, 20, 40, 100]

const StatusLabels = {
  pending: '未完成',
  completed: '已完成',
  submitted: '已提交',
  reviewed: '已通过',
  rejected: '已驳回',
}

const StatusStyles = {
  pending: { color: '#ff9800', backgroundColor: '#fff3e0' },
  completed: { color: '#4caf50', backgroundColor: '#e8f5e9' },
  submitted: { color: '#2196f3', backgroundColor: '#e3f2fd' },
  reviewed: { color: '#4caf50', backgroundColor: '#e8f5e9' },
  rejected: { color: '#f44336', backgroundColor: '#ffebee' },
}

const ReviewStatusLabels = {
  approved: '通过',
  rejected: '驳回',
}

const SceneTypeLabels = {
  normal: '普通练字',
  character: '生字练习',
}

function MyAssignments({ studentNo, onImportAssignment }) {
  const [assignments, setAssignments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 10,
    total: 0,
    total_pages: 1,
  })
  const [statusFilter, setStatusFilter] = useState('')

  const [submittingId, setSubmittingId] = useState(null)
  const [showSubmitDialog, setShowSubmitDialog] = useState(false)
  const [selectedAssignment, setSelectedAssignment] = useState(null)
  const [previewImage, setPreviewImage] = useState(null)
  const [submitImage, setSubmitImage] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  
  const fileInputRef = useRef(null)

  const fetchAssignments = useCallback(async (page = 1, size = pageSize, status = statusFilter) => {
    if (!studentNo) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    try {
      const result = await assignmentApi.getPaginated(page, size, studentNo, status || undefined)
      setAssignments(result.data || [])
      setPagination(result.pagination)
      setCurrentPage(result.pagination.page)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [studentNo, pageSize, statusFilter])

  useEffect(() => {
    fetchAssignments(currentPage, pageSize, statusFilter)
  }, [fetchAssignments, currentPage, pageSize, statusFilter, studentNo])

  const handlePageSizeChange = (newSize) => {
    setPageSize(newSize)
    setCurrentPage(1)
  }

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      setCurrentPage(newPage)
    }
  }

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件')
      return
    }

    const reader = new FileReader()
    reader.onload = (event) => {
      setSubmitImage(event.target?.result)
    }
    reader.readAsDataURL(file)
  }

  const handleSubmitAssignment = async () => {
    if (!selectedAssignment) return

    if (!submitImage) {
      alert('请先上传作业图片')
      return
    }

    if (!window.confirm('确定要提交该作业吗？')) {
      return
    }

    setIsUploading(true)
    setSubmittingId(selectedAssignment.assignment_id)
    
    try {
      const updated = await assignmentApi.submit(selectedAssignment.assignment_id, submitImage)
      
      setAssignments((prev) =>
        prev.map((a) =>
          a.assignment_id === selectedAssignment.assignment_id ? updated : a
        )
      )
      
      alert('作业提交成功！')
      setShowSubmitDialog(false)
      setSubmitImage(null)
      setSelectedAssignment(null)
    } catch (err) {
      alert(`提交失败: ${err.message}`)
    } finally {
      setIsUploading(false)
      setSubmittingId(null)
    }
  }

  const handleResubmitAssignment = async () => {
    if (!selectedAssignment) return

    if (!submitImage) {
      alert('请先上传新的作业图片')
      return
    }

    if (!window.confirm('确定要重新提交该作业吗？')) {
      return
    }

    setIsUploading(true)
    setSubmittingId(selectedAssignment.assignment_id)
    
    try {
      const updated = await assignmentApi.resubmit(selectedAssignment.assignment_id, submitImage)
      
      setAssignments((prev) =>
        prev.map((a) =>
          a.assignment_id === selectedAssignment.assignment_id ? updated : a
        )
      )
      
      alert('作业重新提交成功！')
      setShowSubmitDialog(false)
      setSubmitImage(null)
      setSelectedAssignment(null)
    } catch (err) {
      alert(`重新提交失败: ${err.message}`)
    } finally {
      setIsUploading(false)
      setSubmittingId(null)
    }
  }

  const openSubmitDialog = (assignment) => {
    setSelectedAssignment(assignment)
    setSubmitImage(null)
    setShowSubmitDialog(true)
  }

  const openDetailDialog = (assignment) => {
    setSelectedAssignment(assignment)
    setShowDetailDialog(true)
  }

  const handleImport = (assignment) => {
    if (onImportAssignment) {
      onImportAssignment(assignment)
    }
  }

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-'
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

  const getSceneTypeLabel = (sceneType) => {
    return SceneTypeLabels[sceneType] || '练字'
  }

  const canSubmit = (status) => {
    return status === 'pending' || status === 'completed'
  }

  const canResubmit = (status) => {
    return status === 'rejected'
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
          共 <strong>{total}</strong> 条作业记录
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

  const renderSubmitDialog = () => {
    if (!showSubmitDialog || !selectedAssignment) return null

    const isResubmit = selectedAssignment.status === 'rejected'

    return (
      <div className="modal-overlay" onClick={() => {
        setShowSubmitDialog(false)
        setSelectedAssignment(null)
        setSubmitImage(null)
      }}>
        <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px', width: '90vw' }}>
          <div className="modal-header">
            <h3>{isResubmit ? '重新提交作业' : '提交作业'}</h3>
            <button
              className="modal-close"
              onClick={() => {
                setShowSubmitDialog(false)
                setSelectedAssignment(null)
                setSubmitImage(null)
              }}
            >
              ✕
            </button>
          </div>
          <div className="modal-body">
            <div style={{ marginBottom: '16px' }}>
              <label className="form-label" style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                作业信息
              </label>
              <div style={{ padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                <p style={{ margin: '0 0 8px 0', fontSize: '14px' }}>
                  <strong>练习文字：</strong>{selectedAssignment.characters}
                </p>
                <p style={{ margin: '0', fontSize: '14px' }}>
                  <strong>场景类型：</strong>{getSceneTypeLabel(selectedAssignment.scene_type)}
                </p>
                {selectedAssignment.review_comments && (
                  <p style={{ margin: '8px 0 0 0', fontSize: '14px', color: '#f44336' }}>
                    <strong>老师评语：</strong>{selectedAssignment.review_comments}
                  </p>
                )}
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label className="form-label" style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                上传作业图片
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageSelect}
                style={{ marginBottom: '12px' }}
              />
              {submitImage && (
                <div style={{ marginTop: '12px' }}>
                  <p style={{ fontSize: '13px', color: '#666', marginBottom: '8px' }}>预览：</p>
                  <img
                    src={submitImage}
                    alt="作业预览"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '300px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                    }}
                  />
                </div>
              )}
            </div>
          </div>
          <div className="modal-footer">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setShowSubmitDialog(false)
                setSelectedAssignment(null)
                setSubmitImage(null)
              }}
              disabled={isUploading}
            >
              取消
            </button>
            <button
              className="btn btn-primary"
              onClick={isResubmit ? handleResubmitAssignment : handleSubmitAssignment}
              disabled={isUploading || !submitImage}
            >
              {isUploading ? '提交中...' : (isResubmit ? '重新提交' : '提交')}
            </button>
          </div>
        </div>
      </div>
    )
  }

  const renderDetailDialog = () => {
    if (!showDetailDialog || !selectedAssignment) return null

    const reviewAnnotations = selectedAssignment.review_annotations
    let annotations = []
    if (reviewAnnotations && typeof reviewAnnotations === 'object') {
      if (Array.isArray(reviewAnnotations)) {
        annotations = reviewAnnotations
      } else if (reviewAnnotations.circles && Array.isArray(reviewAnnotations.circles)) {
        annotations = reviewAnnotations.circles
      }
    }

    return (
      <div className="modal-overlay" onClick={() => {
        setShowDetailDialog(false)
        setSelectedAssignment(null)
      }}>
        <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', width: '95vw', maxHeight: '90vh' }}>
          <div className="modal-header">
            <h3>作业详情</h3>
            <button
              className="modal-close"
              onClick={() => {
                setShowDetailDialog(false)
                setSelectedAssignment(null)
              }}
            >
              ✕
            </button>
          </div>
          <div className="modal-body" style={{ maxHeight: 'calc(90vh - 160px)', overflowY: 'auto' }}>
            <div style={{ marginBottom: '16px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <tbody>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500', width: '100px' }}>练习文字</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{selectedAssignment.characters}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>场景类型</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{getSceneTypeLabel(selectedAssignment.scene_type)}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>布置时间</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{formatDateTime(selectedAssignment.assigned_at)}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>提交时间</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{formatDateTime(selectedAssignment.submitted_at)}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>批改时间</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{formatDateTime(selectedAssignment.reviewed_at)}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>提交次数</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{selectedAssignment.submission_count || 0} 次</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>状态</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                      <span style={{
                        padding: '4px 12px',
                        borderRadius: '20px',
                        fontSize: '12px',
                        fontWeight: '500',
                        whiteSpace: 'nowrap',
                        ...StatusStyles[selectedAssignment.status],
                      }}>
                        {StatusLabels[selectedAssignment.status] || '未知'}
                      </span>
                    </td>
                  </tr>
                  {selectedAssignment.review_status && (
                    <tr>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>批改结果</td>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                        <span style={{
                          color: selectedAssignment.review_status === 'approved' ? '#4caf50' : '#f44336',
                          fontWeight: '500'
                        }}>
                          {ReviewStatusLabels[selectedAssignment.review_status] || selectedAssignment.review_status}
                        </span>
                      </td>
                    </tr>
                  )}
                  {selectedAssignment.review_comments && (
                    <tr>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>老师评语</td>
                      <td style={{ padding: '8px', borderBottom: '1px solid #eee', color: '#f44336' }}>
                        {selectedAssignment.review_comments}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {selectedAssignment.submitted_image && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <p style={{ fontSize: '14px', fontWeight: '500', margin: 0 }}>
                    提交的作业图片
                    {annotations.length > 0 && (
                      <span style={{ fontSize: '12px', color: '#f44336', marginLeft: '8px' }}>
                        （老师已标记 {annotations.length} 个问题）
                      </span>
                    )}
                  </p>
                </div>
                <div style={{ 
                  position: 'relative', 
                  border: '2px solid #ddd', 
                  borderRadius: '4px',
                  minHeight: '200px',
                  backgroundColor: '#fafafa'
                }}>
                  <img
                    src={selectedAssignment.submitted_image}
                    alt="提交的作业"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '400px',
                      display: 'block',
                      margin: '0 auto'
                    }}
                  />
                  {annotations.length > 0 && (
                    <svg style={{ 
                      position: 'absolute', 
                      top: 0, 
                      left: 0, 
                      width: '100%', 
                      height: '100%',
                      pointerEvents: 'none'
                    }}>
                      {annotations.map((circle, index) => (
                        <g key={index}>
                          <circle
                            cx={circle.x}
                            cy={circle.y}
                            r={circle.radius}
                            fill="none"
                            stroke="#f44336"
                            strokeWidth="3"
                          />
                          <text
                            x={circle.x}
                            y={circle.y + 5}
                            textAnchor="middle"
                            fill="#f44336"
                            fontSize="14"
                            fontWeight="bold"
                          >
                            {circle.label || `问题${index + 1}`}
                          </text>
                        </g>
                      ))}
                    </svg>
                  )}
                </div>
                {annotations.length > 0 && (
                  <div style={{ marginTop: '8px' }}>
                    <p style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>
                      老师标记的问题：
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {annotations.map((circle, index) => (
                        <span 
                          key={index}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            padding: '4px 8px',
                            backgroundColor: '#ffebee',
                            borderRadius: '4px',
                            fontSize: '12px',
                            color: '#f44336'
                          }}
                        >
                          {circle.label || `问题${index + 1}`}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="modal-footer">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setShowDetailDialog(false)
                setSelectedAssignment(null)
              }}
            >
              关闭
            </button>
            {canResubmit(selectedAssignment.status) && (
              <button
                className="btn btn-primary"
                onClick={() => {
                  setShowDetailDialog(false)
                  openSubmitDialog(selectedAssignment)
                }}
                style={{ backgroundColor: '#ff9800' }}
              >
                重新提交
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  if (!studentNo) {
    return (
      <div className="empty-state">
        <div className="empty-icon">👤</div>
        <h3>请先登录</h3>
        <p>请点击右上角「切换为学生」按钮，输入学号登录</p>
      </div>
    )
  }

  return (
    <div className="template-manager">
      <div className="template-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h2>我的作业</h2>
          {pagination.total > 0 && (
            <span style={{ fontSize: '13px', color: '#666' }}>
              共 {pagination.total} 条记录
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', color: '#666' }}>状态筛选:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value)
                setCurrentPage(1)
              }}
              style={{
                padding: '6px 12px',
                borderRadius: '4px',
                border: '1px solid #ddd',
                fontSize: '14px',
              }}
            >
              <option value="">全部</option>
              <option value="pending">未完成</option>
              <option value="completed">已完成</option>
              <option value="submitted">已提交</option>
              <option value="reviewed">已通过</option>
              <option value="rejected">已驳回</option>
            </select>
          </div>
          <button
            className="btn btn-secondary"
            onClick={() => fetchAssignments(1, pageSize, statusFilter)}
          >
            刷新
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error-message">
          {error}
          <button className="btn btn-secondary" onClick={() => fetchAssignments(1, pageSize, statusFilter)}>
            重试
          </button>
        </div>
      ) : assignments.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>暂无作业</h3>
          <p>老师尚未给您布置作业</p>
        </div>
      ) : (
        <>
          <div className="history-table-container">
            <table className="history-table">
              <thead>
                <tr>
                  <th style={{ width: '120px' }}>场景类型</th>
                  <th style={{ width: '160px' }}>布置时间</th>
                  <th style={{ width: '160px' }}>提交时间</th>
                  <th style={{ width: '100px' }}>状态</th>
                  <th style={{ width: '300px' }}>练习文字</th>
                  <th style={{ width: '300px', textAlign: 'right' }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((assignment) => {
                  const statusStyle = StatusStyles[assignment.status] || StatusStyles.pending
                  const statusLabel = StatusLabels[assignment.status] || '未完成'
                  const canSubmitNow = canSubmit(assignment.status)
                  const canResubmitNow = canResubmit(assignment.status)
                  const hasSubmitted = assignment.status === 'submitted' || assignment.status === 'reviewed' || assignment.status === 'rejected'

                  return (
                    <tr key={assignment.assignment_id}>
                      <td>{getSceneTypeLabel(assignment.scene_type)}</td>
                      <td>{formatDateTime(assignment.assigned_at)}</td>
                      <td style={{ color: assignment.submitted_at ? '#2196f3' : '#999' }}>
                        {formatDateTime(assignment.submitted_at)}
                      </td>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <span style={{
                          padding: '4px 12px',
                          borderRadius: '20px',
                          fontSize: '12px',
                          fontWeight: '500',
                          whiteSpace: 'nowrap',
                          ...statusStyle,
                        }}>
                          {statusLabel}
                        </span>
                      </td>
                      <td>
                        <div style={{
                          fontSize: '13px',
                          color: '#666',
                          maxWidth: '280px',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }} title={assignment.characters}>
                          {assignment.characters}
                        </div>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                          <button
                            className="btn btn-sm btn-apply"
                            onClick={() => handleImport(assignment)}
                            title="导入作业到字帖编辑器"
                            style={{ backgroundColor: '#2196f3' }}
                          >
                            导入作业
                          </button>
                          {hasSubmitted && (
                            <button
                              className="btn btn-sm"
                              onClick={() => openDetailDialog(assignment)}
                              title="查看作业详情"
                              style={{ backgroundColor: '#9c27b0' }}
                            >
                              查看详情
                            </button>
                          )}
                          {canSubmitNow && (
                            <button
                              className="btn btn-sm btn-apply"
                              onClick={() => openSubmitDialog(assignment)}
                              disabled={submittingId === assignment.assignment_id}
                              title="提交作业"
                              style={{ backgroundColor: '#4caf50' }}
                            >
                              {submittingId === assignment.assignment_id ? '处理中...' : '提交作业'}
                            </button>
                          )}
                          {canResubmitNow && (
                            <button
                              className="btn btn-sm"
                              onClick={() => openSubmitDialog(assignment)}
                              disabled={submittingId === assignment.assignment_id}
                              title="重新提交作业"
                              style={{ backgroundColor: '#ff9800' }}
                            >
                              {submittingId === assignment.assignment_id ? '处理中...' : '重新提交'}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {renderPagination()}
        </>
      )}
      {renderSubmitDialog()}
      {renderDetailDialog()}
    </div>
  )
}

export default MyAssignments
