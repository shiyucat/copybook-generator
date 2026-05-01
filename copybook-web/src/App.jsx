import React, { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import CopybookEditor from './components/CopybookEditor'
import TemplateManager from './components/TemplateManager'
import './App.css'

const DEFAULT_CONFIG = {
  input_text: '',
  grid_type: '田字格',
  grid_color: '#000000',
  grid_size: 60,
  font_style: 'zhenkai',
  student_name: '',
  student_id: '',
  class_name: '',
}

function App() {
  const [activePage, setActivePage] = useState('editor')
  const [currentConfig, setCurrentConfig] = useState({ ...DEFAULT_CONFIG })

  const handleConfigChange = useCallback((newConfig) => {
    setCurrentConfig(newConfig)
  }, [])

  const handleApplyTemplate = useCallback((templateConfig) => {
    const safeConfig = templateConfig && typeof templateConfig === 'object' ? templateConfig : {}
    const mergedConfig = {
      ...DEFAULT_CONFIG,
      input_text: safeConfig.input_text ?? DEFAULT_CONFIG.input_text,
      grid_type: safeConfig.grid_type ?? DEFAULT_CONFIG.grid_type,
      grid_color: safeConfig.grid_color ?? DEFAULT_CONFIG.grid_color,
      grid_size: safeConfig.grid_size ?? DEFAULT_CONFIG.grid_size,
      font_style: safeConfig.font_style ?? DEFAULT_CONFIG.font_style,
      student_name: String(safeConfig.student_name ?? DEFAULT_CONFIG.student_name),
      student_id: String(safeConfig.student_id ?? DEFAULT_CONFIG.student_id),
      class_name: String(safeConfig.class_name ?? DEFAULT_CONFIG.class_name),
    }
    setCurrentConfig(mergedConfig)
    setActivePage('editor')
    alert('模版已应用')
  }, [])

  return (
    <div className="app">
      <Sidebar activePage={activePage} onPageChange={setActivePage} />
      <main className="main-content">
        {activePage === 'editor' && (
          <CopybookEditor config={currentConfig} onConfigChange={handleConfigChange} />
        )}
        {activePage === 'templates' && (
          <TemplateManager
            currentConfig={currentConfig}
            onApplyTemplate={handleApplyTemplate}
          />
        )}
      </main>
    </div>
  )
}

export default App
