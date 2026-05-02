import React, { useState, useEffect, useCallback } from 'react'
import { exportHistoryApi } from '../services/api'

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

const SceneTypeLabels = {
  normal: '普通练字场景',
  character: '生字场景',
}

const PageSizeLabels = {
  A4: 'A4',
  SIZE_16K: '16开',
  A5: 'A5',
  B5: 'B5',
}

function ExportHistory({ onEditHistory }) {
  const [historyList, setHistoryList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [exportingId, setExportingId] = useState(null)
  const [searchKeyword, setSearchKeyword] = useState('')

  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 10,
    total: 0,
    total_pages: 1,
  })

  const fetchHistory = useCallback(async (page = 1, size = pageSize, keyword = searchKeyword) => {
    setLoading(true)
    setError(null)
    try {
      const result = await exportHistoryApi.getPaginated(page, size, keyword)
      setHistoryList(result.data || [])
      setPagination(result.pagination)
      setCurrentPage(result.pagination.page)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [pageSize, searchKeyword])

  useEffect(() => {
    fetchHistory(currentPage, pageSize)
  }, [fetchHistory, currentPage, pageSize])

  const handleSearchChange = useCallback((e) => {
    const value = e.target.value
    setSearchKeyword(value)
    setCurrentPage(1)
  }, [])

  const handlePageSizeChange = (newSize) => {
    setPageSize(newSize)
    setCurrentPage(1)
  }

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      setCurrentPage(newPage)
    }
  }

  const handleReExport = async (historyItem) => {
    setExportingId(historyItem.history_id)
    try {
      await exportHistoryApi.reExport(historyItem.history_id)
      fetchHistory(currentPage, pageSize)
    } catch (err) {
      alert(`导出失败: ${err.message}`)
    } finally {
      setExportingId(null)
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
          共 <strong>{total}</strong> 条记录
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

  const handleEditHistory = (historyItem) => {
    if (onEditHistory) {
      onEditHistory(historyItem)
    }
  }

  return (
    <div className="export-history">
      <div className="history-header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <h2>导出历史</h2>
          {pagination.total > 0 && (
            <span style={{ fontSize: '13px', color: '#666', marginLeft: '12px' }}>
              共 {pagination.total} 条记录
            </span>
          )}
        </div>
        <div className="search-box" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <span style={{ fontSize: '13px', color: '#666' }}>🔍</span>
          <input
            type="text"
            placeholder="搜索姓名或学号..."
            value={searchKeyword}
            onChange={handleSearchChange}
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontSize: '14px',
              width: '200px',
              outline: 'none',
            }}
            onFocus={(e) => {
              e.target.style.borderColor = '#1890ff'
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#ddd'
            }}
          />
        </div>
      </div>

      {loading ? (
        <div className="loading">加载中...</div>
      ) : error ? (
        <div className="error-message">
          {error}
          <button className="btn btn-secondary" onClick={() => fetchHistory(1, pageSize)}>
            重试
          </button>
        </div>
      ) : historyList.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📜</div>
          <h3>暂无导出记录</h3>
          <p>在字帖编辑页面点击「导出PDF字帖」按钮后，导出记录将显示在这里</p>
        </div>
      ) : (
        <>
          <div className="history-table-container">
            <table className="history-table">
              <thead>
                <tr>
                  <th className="col-scene-type">场景类型</th>
                  <th className="col-name">姓名</th>
                  <th className="col-student-id">学号</th>
                  <th className="col-content">文字内容</th>
                  <th className="col-page-size">页面大小</th>
                  <th className="col-export-time">导出时间</th>
                  <th className="col-export-count">导出次数</th>
                  <th className="col-action">操作</th>
                </tr>
              </thead>
              <tbody>
                {historyList.map((item) => (
                  <tr key={item.history_id}>
                    <td>
                      <span className="scene-type-tag">
                        {SceneTypeLabels[item.scene_type] || item.scene_type}
                      </span>
                    </td>
                    <td>{item.student_name || '-'}</td>
                    <td>{item.student_id || '-'}</td>
                    <td className="content-cell">
                      <div
                        className="content-text"
                        title={item.input_text}
                      >
                        {item.input_text || '-'}
                      </div>
                    </td>
                    <td>{PageSizeLabels[item.page_size] || item.page_size || '-'}</td>
                    <td>{formatDateTime(item.updated_at)}</td>
                    <td>
                      <span className="export-count">{item.export_count}</span>
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-export-action"
                        onClick={() => handleEditHistory(item)}
                        title="编辑此配置"
                        style={{
                          marginRight: '8px',
                        }}
                      >
                        ✏️
                      </button>
                      <button
                        className="btn btn-sm btn-export-action"
                        onClick={() => handleReExport(item)}
                        disabled={exportingId === item.history_id}
                        title="再次导出"
                      >
                        {exportingId === item.history_id ? '导出中...' : '📥'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {renderPagination()}
        </>
      )}
    </div>
  )
}

export default ExportHistory
