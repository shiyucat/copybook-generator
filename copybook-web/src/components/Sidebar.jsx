import React from 'react'

function Sidebar({ activePage, onPageChange }) {
  const menuItems = [
    { id: 'editor', label: '字帖编辑', icon: '✏️' },
    { id: 'templates', label: '模版管理', icon: '📁' },
    { id: 'history', label: '导出历史', icon: '📜' },
  ]

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>字帖生成器</h2>
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
