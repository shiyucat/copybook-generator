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
  grid_size_cm: 2.0,
  lines_per_char: 1,
  show_pinyin: false,
  font_style: 'zhenkai',
  font_color: '#000000',
  student_name: '',
  student_id: '',
  class_name: '',
  page_size: 'A4',
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
      grid_size_cm: safeConfig.grid_size_cm ?? DEFAULT_CONFIG.grid_size_cm,
      lines_per_char: safeConfig.lines_per_char ?? DEFAULT_CONFIG.lines_per_char,
      show_pinyin: safeConfig.show_pinyin ?? DEFAULT_CONFIG.show_pinyin,
      font_style: safeConfig.font_style ?? DEFAULT_CONFIG.font_style,
      font_color: safeConfig.font_color ?? DEFAULT_CONFIG.font_color,
      student_name: String(safeConfig.student_name ?? DEFAULT_CONFIG.student_name),
      student_id: String(safeConfig.student_id ?? DEFAULT_CONFIG.student_id),
      class_name: String(safeConfig.class_name ?? DEFAULT_CONFIG.class_name),
      page_size: safeConfig.page_size ?? DEFAULT_CONFIG.page_size,
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
