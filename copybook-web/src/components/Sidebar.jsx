import React from 'react'

const USER_MODE_TEACHER = 'teacher'
const USER_MODE_STUDENT = 'student'

function Sidebar({ 
  activePage, 
  onPageChange, 
  userMode, 
  currentStudent,
  onSwitchToStudent,
  onSwitchToTeacher 
}) {
  const teacherMenuItems = [
    { id: 'editor', label: '字帖编辑', icon: '✏️' },
    { id: 'templates', label: '模版管理', icon: '📁' },
    { id: 'students', label: '学生管理', icon: '👥' },
    { id: 'tasks', label: '作业管理', icon: '📋' },
    { id: 'history', label: '导出历史', icon: '📜' },
  ]

  const studentMenuItems = [
    { id: 'editor', label: '字帖编辑', icon: '✏️' },
    { id: 'my-assignments', label: '我的作业', icon: '📋' },
  ]

  const menuItems = userMode === USER_MODE_STUDENT ? studentMenuItems : teacherMenuItems
  const title = userMode === USER_MODE_STUDENT ? '学生端' : '字帖生成器'

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>{title}</h2>
      </div>
      
      {userMode === USER_MODE_STUDENT && currentStudent && (
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 12px',
            backgroundColor: 'rgba(227, 242, 253, 0.2)',
            borderRadius: '8px',
            marginBottom: '10px',
          }}>
            <span style={{ fontSize: '18px' }}>👤</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ 
                fontSize: '14px', 
                fontWeight: '600', 
                color: '#fff',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}>
                {currentStudent.name}
              </div>
              <div style={{ 
                fontSize: '12px', 
                color: 'rgba(236, 240, 241, 0.7)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}>
                {currentStudent.student_no}
                {currentStudent.class_name && ` · ${currentStudent.class_name}班`}
              </div>
            </div>
          </div>
          <button
            onClick={onSwitchToTeacher}
            style={{
              width: '100%',
              padding: '8px 16px',
              backgroundColor: '#ff9800',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'background-color 0.2s',
            }}
          >
            切换为老师
          </button>
        </div>
      )}

      {userMode === USER_MODE_TEACHER && (
        <div style={{
          padding: '12px 16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        }}>
          <button
            onClick={onSwitchToStudent}
            style={{
              width: '100%',
              padding: '10px 16px',
              backgroundColor: '#2196f3',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'background-color 0.2s',
            }}
          >
            切换为学生
          </button>
        </div>
      )}

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activePage === item.id ? 'active' : ''}`}
            onClick={() => onPageChange(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}

export default Sidebar
