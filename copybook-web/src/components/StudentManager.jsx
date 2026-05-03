import React, { useState, useEffect, useCallback } from 'react'
import { studentApi } from '../services/api'

const PAGE_SIZE_OPTIONS = [10, 20, 40, 100]

function StudentManager({ onAddAssignment }) {
  const [students, setStudents] = useState([])
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
  const [searchKeyword, setSearchKeyword] = useState('')
  const [searchInput, setSearchInput] = useState('')
  
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [editingStudent, setEditingStudent] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    student_no: '',
    class_name: '',
  })
  const [saving, setSaving] = useState(false)

  const fetchStudents = useCallback(async (page = 1, size = pageSize, keyword = searchKeyword) => {
    setLoading(true)
    setError(null)
    try {
      const result = await studentApi.getPaginated(page, size, keyword)
      setStudents(result.data || [])
      setPagination(result.pagination)
      setCurrentPage(result.pagination.page)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [pageSize, searchKeyword])

  useEffect(() => {
    fetchStudents(currentPage, pageSize, searchKeyword)
  }, [fetchStudents, currentPage, pageSize, searchKeyword])

  const handleSearch = () => {
    setSearchKeyword(searchInput)
    setCurrentPage(1)
  }

  const handlePageSizeChange = (newSize) => {
    setPageSize(newSize)
    setCurrentPage(1)
  }

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      setCurrentPage(newPage)
    }
  }

  const handleOpenAddDialog = () => {
    setFormData({
      name: '',
      student_no: '',
      class_name: '',
    })
    setShowAddDialog(true)
  }

  const handleOpenEditDialog = (student) => {
    setEditingStudent(student)
    setFormData({
      name: student.name,
      student_no: student.student_no,
      class_name: student.class_name,
    })
    setShowEditDialog(true)
  }

  const handleFormChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleAddStudent = async () => {
    if (!formData.name.trim()) {
      alert('请输入学生姓名')
      return
    }
    if (!formData.student_no.trim()) {
      alert('请输入学号')
      return
    }

    setSaving(true)
    try {
      await studentApi.create(formData)
      setShowAddDialog(false)
      alert('学生添加成功')
      fetchStudents(currentPage, pageSize, searchKeyword)
    } catch (err) {
      alert(`添加失败: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleEditStudent = async () => {
    if (!formData.name.trim()) {
      alert('请输入学生姓名')
      return
    }
    if (!formData.student_no.trim()) {
      alert('请输入学号')
      return
    }

    setSaving(true)
    try {
      await studentApi.update(editingStudent.student_id, formData)
      setShowEditDialog(false)
      setEditingStudent(null)
      alert('学生信息更新成功')
      fetchStudents(currentPage, pageSize, searchKeyword)
    } catch (err) {
      alert(`更新失败: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteStudent = async (student) => {
    if (!window.confirm(`确定要删除学生「${student.name}」吗？\n此操作不可恢复。`)) {
      return
    }

    try {
      await studentApi.delete(student.student_id)
      const remainingOnPage = students.length - 1
      if (remainingOnPage === 0 && currentPage > 1) {
        setCurrentPage(Math.max(1, currentPage - 1))
      } else {
        fetchStudents(currentPage, pageSize, searchKeyword)
      }
    } catch (err) {
      alert(`删除失败: ${err.message}`)
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
          共 <strong>{total}</strong> 位学生
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
          <h2>学生管理</h2>
          {pagination.total > 0 && (
            <span style={{ fontSize: '13px', color: '#666' }}>
              共 {pagination.total} 位学生
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder="搜索姓名、学号、班级..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              style={{
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px',
                width: '200px',
              }}
            />
            <button
              className="btn btn-secondary"
              onClick={handleSearch}
            >
              搜索
            </button>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleOpenAddDialog}
          >
            + 添加学生
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error-message">
          {error}
          <button className="btn btn-secondary" onClick={() => fetchStudents(currentPage, pageSize, searchKeyword)}>
            重试
          </button>
        </div>
      ) : students.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">👥</div>
          <h3>暂无学生信息</h3>
          <p>点击「添加学生」按钮创建新学生</p>
        </div>
      ) : (
        <>
          <div className="history-table-container">
            <table className="history-table">
              <thead>
                <tr>
                  <th style={{ width: '120px' }}>学号</th>
                  <th style={{ width: '100px' }}>姓名</th>
                  <th style={{ width: '100px' }}>班级</th>
                  <th style={{ width: '160px' }}>创建时间</th>
                  <th style={{ width: '160px' }}>更新时间</th>
                  <th style={{ width: '200px', textAlign: 'right' }}>操作</th>
                </tr>
              </thead>
              <tbody>
                {students.map((student) => (
                  <tr key={student.student_id}>
                    <td>{student.student_no}</td>
                    <td>{student.name}</td>
                    <td>{student.class_name || '-'}</td>
                    <td>{formatDateTime(student.created_at)}</td>
                    <td>{formatDateTime(student.updated_at)}</td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        <button
                          className="btn btn-sm btn-apply"
                          onClick={() => onAddAssignment && onAddAssignment(student)}
                          title="布置作业"
                        >
                          布置作业
                        </button>
                        <button
                          className="btn btn-sm btn-apply"
                          onClick={() => handleOpenEditDialog(student)}
                          title="编辑"
                          style={{ backgroundColor: '#4caf50' }}
                        >
                          编辑
                        </button>
                        <button
                          className="btn btn-sm btn-delete"
                          onClick={() => handleDeleteStudent(student)}
                          title="删除"
                        >
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {renderPagination()}
        </>
      )}

      {showAddDialog && (
        <div className="modal-overlay" onClick={() => setShowAddDialog(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>添加学生</h3>
              <button
                className="modal-close"
                onClick={() => setShowAddDialog(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">学生姓名 *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  placeholder="请输入学生姓名"
                />
              </div>
              <div className="form-group">
                <label className="form-label">学号 *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.student_no}
                  onChange={(e) => handleFormChange('student_no', e.target.value)}
                  placeholder="请输入学号"
                />
              </div>
              <div className="form-group">
                <label className="form-label">班级</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.class_name}
                  onChange={(e) => handleFormChange('class_name', e.target.value)}
                  placeholder="请输入班级（可选）"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowAddDialog(false)}
                disabled={saving}
              >
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={handleAddStudent}
                disabled={saving}
              >
                {saving ? '保存中...' : '保存'}
              </button>
            </div>
          </div>
        </div>
      )}

      {showEditDialog && (
        <div className="modal-overlay" onClick={() => setShowEditDialog(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>编辑学生</h3>
              <button
                className="modal-close"
                onClick={() => setShowEditDialog(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="form-group">
                <label className="form-label">学生姓名 *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  placeholder="请输入学生姓名"
                />
              </div>
              <div className="form-group">
                <label className="form-label">学号 *</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.student_no}
                  onChange={(e) => handleFormChange('student_no', e.target.value)}
                  placeholder="请输入学号"
                />
              </div>
              <div className="form-group">
                <label className="form-label">班级</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.class_name}
                  onChange={(e) => handleFormChange('class_name', e.target.value)}
                  placeholder="请输入班级（可选）"
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowEditDialog(false)}
                disabled={saving}
              >
                取消
              </button>
              <button
                className="btn btn-primary"
                onClick={handleEditStudent}
                disabled={saving}
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

export default StudentManager