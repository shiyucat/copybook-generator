import React from 'react'

const USER_MODE_TEACHER = 'teacher'
const USER_MODE_STUDENT = 'student'

function Sidebar({ activePage, onPageChange, userMode }) {
  const teacherMenuItems = [
    { id: 'editor', label: '字帖编辑', icon: '✏️' },
    { id: 'templates', label: '模版管理', icon: '📁' },
    { id: 'students', label: '学生管理', icon: '👥' },
    { id: 'tasks', label: '当前任务', icon: '📋' },
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
