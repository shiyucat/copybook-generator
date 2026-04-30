import React, { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import CopybookEditor from './components/CopybookEditor'
import TemplateManager from './components/TemplateManager'
import './App.css'

function App() {
  const [activePage, setActivePage] = useState('editor')
  const [currentConfig, setCurrentConfig] = useState({
    input_text: '',
    grid_type: '田字格',
    grid_size: 60,
    font_style: 'zhenkai',
    student_name: '',
    student_id: '',
    class_name: '',
  })

  const handleConfigChange = useCallback((newConfig) => {
    setCurrentConfig(newConfig)
  }, [])

  const handleApplyTemplate = useCallback((templateConfig) => {
    setCurrentConfig(templateConfig)
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
