import React, { useState, useEffect, useCallback } from 'react'
import { assignmentApi, studentApi } from '../services/api'

const PAGE_SIZE_OPTIONS = [10, 20, 40, 100]

const StatusLabels = {
  pending: '未完成',
  completed: '已完成',
}

const StatusStyles = {
  pending: { color: '#ff9800', backgroundColor: '#fff3e0' },
  completed: { color: '#4caf50', backgroundColor: '#e8f5e9' },
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
                  <th style={{ width: '160px' }}>完成时间</th>
                  <th style={{ width: '80px' }}>状态</th>
                  <th style={{ width: '300px' }}>练习文字</th>
                  <th style={{ width: '100px', textAlign: 'right' }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {assignments.map((assignment) => {
                  const studentInfo = getStudentInfo(assignment.student_no)
                  const statusStyle = StatusStyles[assignment.status] || StatusStyles.pending
                  const statusLabel = StatusLabels[assignment.status] || '未完成'

                  return (
                    <tr key={assignment.assignment_id}>
                      <td>{assignment.student_no}</td>
                      <td>{studentInfo.name}</td>
                      <td>{studentInfo.class || '-'}</td>
                      <td>{getSceneTypeLabel(assignment.scene_type)}</td>
                      <td>{formatDateTime(assignment.assigned_at)}</td>
                      <td style={{ color: assignment.completed_at ? '#4caf50' : '#999' }}>
                        {formatDateTime(assignment.completed_at)}
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
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
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
    </div>
  )
}

export default CurrentTasks
