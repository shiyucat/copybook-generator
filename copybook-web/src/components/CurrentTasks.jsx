import React, { useState, useEffect, useCallback, useRef } from 'react'
import { assignmentApi, studentApi } from '../services/api'

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

function CurrentTasks() {
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

  const [students, setStudents] = useState({})
  const [showReviewDialog, setShowReviewDialog] = useState(false)
  const [selectedAssignment, setSelectedAssignment] = useState(null)
  const [reviewStatus, setReviewStatus] = useState('approved')
  const [reviewComments, setReviewComments] = useState('')
  const [isSubmittingReview, setIsSubmittingReview] = useState(false)
  
  const [annotations, setAnnotations] = useState([])
  const [isDrawing, setIsDrawing] = useState(false)
  const [startPos, setStartPos] = useState(null)
  const [currentCircle, setCurrentCircle] = useState(null)
  const canvasRef = useRef(null)
  const imageContainerRef = useRef(null)
  const [imageScale, setImageScale] = useState(1)
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 })

  const fetchStudents = useCallback(async () => {
    try {
      const result = await studentApi.getAll()
      const studentMap = {}
      result.forEach((s) => {
        studentMap[s.student_no] = s
      })
      setStudents(studentMap)
    } catch (err) {
      console.error('获取学生列表失败:', err)
    }
  }, [])

  const fetchAssignments = useCallback(async (page = 1, size = pageSize, status = statusFilter) => {
    setLoading(true)
    setError(null)
    try {
      const result = await assignmentApi.getPaginated(page, size, null, status || undefined)
      setAssignments(result.data || [])
      setPagination(result.pagination)
      setCurrentPage(result.pagination.page)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [pageSize, statusFilter])

  useEffect(() => {
    fetchStudents()
  }, [fetchStudents])

  useEffect(() => {
    fetchAssignments(currentPage, pageSize, statusFilter)
  }, [fetchAssignments, currentPage, pageSize, statusFilter])

  const handlePageSizeChange = (newSize) => {
    setPageSize(newSize)
    setCurrentPage(1)
  }

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      setCurrentPage(newPage)
    }
  }

  const handleDeleteAssignment = async (assignment) => {
    const student = students[assignment.student_no]
    const studentName = student ? student.name : assignment.student_no
    if (!window.confirm(`确定要删除「${studentName}」的作业吗？\n此操作不可恢复。`)) {
      return
    }

    try {
      await assignmentApi.delete(assignment.assignment_id)
      const remainingOnPage = assignments.length - 1
      if (remainingOnPage === 0 && currentPage > 1) {
        setCurrentPage(Math.max(1, currentPage - 1))
      } else {
        fetchAssignments(currentPage, pageSize, statusFilter)
      }
    } catch (err) {
      alert(`删除失败: ${err.message}`)
    }
  }

  const openReviewDialog = (assignment) => {
    setSelectedAssignment(assignment)
    setReviewStatus('approved')
    setReviewComments('')
    setAnnotations([])
    setShowReviewDialog(true)
  }

  const getImagePosition = (e) => {
    const rect = imageContainerRef.current?.getBoundingClientRect()
    if (!rect) return null
    
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    return { x, y }
  }

  const handleMouseDown = (e) => {
    if (!selectedAssignment?.submitted_image) return
    
    const pos = getImagePosition(e)
    if (!pos) return
    
    setIsDrawing(true)
    setStartPos(pos)
    setCurrentCircle({
      x: pos.x,
      y: pos.y,
      radius: 0,
      label: `问题${annotations.length + 1}`
    })
  }

  const handleMouseMove = (e) => {
    if (!isDrawing || !startPos) return
    
    const pos = getImagePosition(e)
    if (!pos) return
    
    const dx = pos.x - startPos.x
    const dy = pos.y - startPos.y
    const radius = Math.sqrt(dx * dx + dy * dy)
    
    setCurrentCircle({
      ...currentCircle,
      radius: Math.max(10, radius)
    })
  }

  const handleMouseUp = () => {
    if (isDrawing && currentCircle && currentCircle.radius > 5) {
      setAnnotations([...annotations, currentCircle])
    }
    setIsDrawing(false)
    setStartPos(null)
    setCurrentCircle(null)
  }

  const removeAnnotation = (index) => {
    setAnnotations(annotations.filter((_, i) => i !== index))
  }

  const clearAnnotations = () => {
    setAnnotations([])
  }

  const handleSubmitReview = async () => {
    if (!selectedAssignment) return

    if (!window.confirm(`确定要将该作业标记为「${ReviewStatusLabels[reviewStatus]}」吗？`)) {
      return
    }

    setIsSubmittingReview(true)
    try {
      const reviewAnnotations = {
        circles: annotations.map((a, i) => ({
          x: a.x,
          y: a.y,
          radius: a.radius,
          label: a.label || `问题${i + 1}`
        }))
      }

      const updated = await assignmentApi.review(
        selectedAssignment.assignment_id,
        reviewStatus,
        reviewComments,
        reviewAnnotations
      )

      setAssignments((prev) =>
        prev.map((a) =>
          a.assignment_id === selectedAssignment.assignment_id ? updated : a
        )
      )

      alert(`批改成功！作业已${ReviewStatusLabels[reviewStatus]}`)
      setShowReviewDialog(false)
      setSelectedAssignment(null)
    } catch (err) {
      alert(`批改失败: ${err.message}`)
    } finally {
      setIsSubmittingReview(false)
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

  const getStudentInfo = (studentNo) => {
    const student = students[studentNo]
    if (student) {
      return {
        name: student.name,
        class: student.class_name,
      }
    }
    return {
      name: studentNo,
      class: '-',
    }
  }

  const getSceneTypeLabel = (sceneType) => {
    return SceneTypeLabels[sceneType] || '练字'
  }

  const canReview = (status) => {
    return status === 'submitted'
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

  const renderReviewDialog = () => {
    if (!showReviewDialog || !selectedAssignment) return null

    const studentInfo = getStudentInfo(selectedAssignment.student_no)

    return (
      <div className="modal-overlay" onClick={() => {
        setShowReviewDialog(false)
        setSelectedAssignment(null)
      }}>
        <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '900px', width: '95vw', maxHeight: '90vh' }}>
          <div className="modal-header">
            <h3>批改作业</h3>
            <button
              className="modal-close"
              onClick={() => {
                setShowReviewDialog(false)
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
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500', width: '100px' }}>学生</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{studentInfo.name}</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500', width: '100px' }}>班级</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>{studentInfo.class}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>练习文字</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }} colSpan={3}>{selectedAssignment.characters}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee', fontWeight: '500' }}>提交时间</td>
                    <td style={{ padding: '8px', borderBottom: '1px solid #eee' }} colSpan={3}>{formatDateTime(selectedAssignment.submitted_at)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {selectedAssignment.submitted_image ? (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <p style={{ fontSize: '14px', fontWeight: '500', margin: 0 }}>
                    学生提交的作业图片
                    <span style={{ fontSize: '12px', color: '#666', marginLeft: '8px' }}>
                      （拖拽鼠标画圈标记问题字）
                    </span>
                  </p>
                  {annotations.length > 0 && (
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={clearAnnotations}
                      style={{ fontSize: '12px', padding: '4px 8px' }}
                    >
                      清除标注
                    </button>
                  )}
                </div>
                <div 
                  ref={imageContainerRef}
                  style={{ 
                    position: 'relative', 
                    border: '2px dashed #ccc', 
                    borderRadius: '4px',
                    minHeight: '200px',
                    cursor: 'crosshair',
                    backgroundColor: '#fafafa'
                  }}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                >
                  <img
                    src={selectedAssignment.submitted_image}
                    alt="学生作业"
                    style={{
                      maxWidth: '100%',
                      maxHeight: '400px',
                      display: 'block',
                      margin: '0 auto'
                    }}
                  />
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
                    {currentCircle && (
                      <g>
                        <circle
                          cx={currentCircle.x}
                          cy={currentCircle.y}
                          r={currentCircle.radius}
                          fill="none"
                          stroke="#ff9800"
                          strokeWidth="3"
                          strokeDasharray="5,5"
                        />
                      </g>
                    )}
                  </svg>
                </div>
                {annotations.length > 0 && (
                  <div style={{ marginTop: '8px' }}>
                    <p style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>
                      已标记 {annotations.length} 个问题：
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {annotations.map((circle, index) => (
                        <span 
                          key={index}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '4px 8px',
                            backgroundColor: '#ffebee',
                            borderRadius: '4px',
                            fontSize: '12px'
                          }}
                        >
                          {circle.label || `问题${index + 1}`}
                          <button
                            onClick={() => removeAnnotation(index)}
                            style={{
                              background: 'none',
                              border: 'none',
                              cursor: 'pointer',
                              color: '#f44336',
                              padding: 0,
                              fontSize: '14px'
                            }}
                          >
                            ✕
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ 
                padding: '40px', 
                textAlign: 'center', 
                backgroundColor: '#f5f5f5', 
                borderRadius: '4px',
                marginBottom: '16px'
              }}>
                <p style={{ color: '#999', margin: 0 }}>该学生未提交作业图片</p>
              </div>
            )}

            <div style={{ marginBottom: '16px' }}>
              <label className="form-label" style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                批改结果
              </label>
              <div style={{ display: 'flex', gap: '16px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="reviewStatus"
                    value="approved"
                    checked={reviewStatus === 'approved'}
                    onChange={() => setReviewStatus('approved')}
                  />
                  <span style={{ color: '#4caf50', fontWeight: '500' }}>通过</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name="reviewStatus"
                    value="rejected"
                    checked={reviewStatus === 'rejected'}
                    onChange={() => setReviewStatus('rejected')}
                  />
                  <span style={{ color: '#f44336', fontWeight: '500' }}>驳回（需重新提交）</span>
                </label>
              </div>
            </div>

            <div>
              <label className="form-label" style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                评语（可选）
              </label>
              <textarea
                value={reviewComments}
                onChange={(e) => setReviewComments(e.target.value)}
                placeholder="请输入批改评语..."
                style={{
                  width: '100%',
                  minHeight: '80px',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px',
                  resize: 'vertical'
                }}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button
              className="btn btn-secondary"
              onClick={() => {
                setShowReviewDialog(false)
                setSelectedAssignment(null)
              }}
              disabled={isSubmittingReview}
            >
              取消
            </button>
            <button
              className="btn btn-primary"
              onClick={handleSubmitReview}
              disabled={isSubmittingReview}
              style={{ 
                backgroundColor: reviewStatus === 'approved' ? '#4caf50' : '#ff9800' 
              }}
            >
              {isSubmittingReview ? '提交中...' : `确认${ReviewStatusLabels[reviewStatus]}`}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="template-manager">
      <div className="template-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h2>当前任务</h2>
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
              <option value="submitted">待批改</option>
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
          <h3>暂无作业记录</h3>
          <p>在学生管理中选择学生并点击「布置作业」按钮创建新的作业任务</p>
        </div>
      ) : (
        <>
          <div className="history-table-container">
            <table className="history-table">
              <thead>
                <tr>
                  <th style={{ width: '100px' }}>学号</th>
                  <th style={{ width: '80px' }}>姓名</th>
                  <th style={{ width: '80px' }}>班级</th>
                  <th style={{ width: '100px' }}>场景类型</th>
                  <th style={{ width: '160px' }}>布置时间</th>
                  <th style={{ width: '160px' }}>提交时间</th>
                  <th style={{ width: '80px' }}>状态</th>
                  <th style={{ width: '300px' }}>练习文字</th>
                  <th style={{ width: '200px', textAlign: 'right' }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((assignment) => {
                  const studentInfo = getStudentInfo(assignment.student_no)
                  const statusStyle = StatusStyles[assignment.status] || StatusStyles.pending
                  const statusLabel = StatusLabels[assignment.status] || '未知'
                  const canReviewNow = canReview(assignment.status)
                  const hasSubmitted = assignment.status === 'submitted' || assignment.status === 'reviewed' || assignment.status === 'rejected'

                  return (
                    <tr key={assignment.assignment_id}>
                      <td>{assignment.student_no}</td>
                      <td>{studentInfo.name}</td>
                      <td>{studentInfo.class || '-'}</td>
                      <td>{getSceneTypeLabel(assignment.scene_type)}</td>
                      <td>{formatDateTime(assignment.assigned_at)}</td>
                      <td style={{ color: assignment.submitted_at ? '#2196f3' : '#999' }}>
                        {formatDateTime(assignment.submitted_at)}
                      </td>
                      <td>
                        <span style={{
                          padding: '4px 12px',
                          borderRadius: '20px',
                          fontSize: '12px',
                          fontWeight: '500',
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
                          {hasSubmitted && (
                            <button
                              className="btn btn-sm"
                              onClick={() => openReviewDialog(assignment)}
                              title="查看作业详情"
                              style={{ backgroundColor: '#9c27b0' }}
                            >
                              查看详情
                            </button>
                          )}
                          {canReviewNow && (
                            <button
                              className="btn btn-sm btn-apply"
                              onClick={() => openReviewDialog(assignment)}
                              title="批改作业"
                              style={{ backgroundColor: '#ff9800' }}
                            >
                              批改作业
                            </button>
                          )}
                          <button
                            className="btn btn-sm btn-delete"
                            onClick={() => handleDeleteAssignment(assignment)}
                            title="删除作业"
                          >
                            删除
                          </button>
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
      {renderReviewDialog()}
    </div>
  )
}

export default CurrentTasks
