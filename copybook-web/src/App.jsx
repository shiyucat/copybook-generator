import React, { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import CopybookEditor from './components/CopybookEditor'
import TemplateManager from './components/TemplateManager'
import ExportHistory from './components/ExportHistory'
import './App.css'

const DEFAULT_CONFIG = {
  input_text: '',
  scene_type: 'normal',
  grid_type: '田字格',
  grid_color: '#000000',
  grid_size: 60,
  grid_size_cm: 2.0,
  lines_per_char: 1,
  show_pinyin: false,
  pinyin_color: '#000000',
  font_style: 'zhenkai',
  font_color: '#000000',
  student_name: '',
  student_id: '',
  class_name: '',
  page_size: 'A4',
  show_character_pinyin: true,
  character_color: '#000000',
  right_grid_color: '#000000',
  right_grid_type: '米字格',
}

function App() {
  const [activePage, setActivePage] = useState('editor')
  const [currentConfig, setCurrentConfig] = useState({ ...DEFAULT_CONFIG })
  const [selectedTemplateId, setSelectedTemplateId] = useState(null)

  const handleConfigChange = useCallback((newConfig) => {
    setCurrentConfig(newConfig)
  }, [])

  const handleApplyTemplate = useCallback((template) => {
    if (!template || !template.config_data) {
      alert('模版数据无效')
      return
    }
    
    const safeConfig = template.config_data && typeof template.config_data === 'object' 
      ? template.config_data 
      : {}
    
    const mergedConfig = {
      ...currentConfig,
      scene_type: safeConfig.scene_type ?? DEFAULT_CONFIG.scene_type,
      grid_type: safeConfig.grid_type ?? DEFAULT_CONFIG.grid_type,
      grid_color: safeConfig.grid_color ?? DEFAULT_CONFIG.grid_color,
      grid_size: safeConfig.grid_size ?? DEFAULT_CONFIG.grid_size,
      grid_size_cm: safeConfig.grid_size_cm ?? DEFAULT_CONFIG.grid_size_cm,
      lines_per_char: safeConfig.lines_per_char ?? DEFAULT_CONFIG.lines_per_char,
      show_pinyin: safeConfig.show_pinyin ?? DEFAULT_CONFIG.show_pinyin,
      pinyin_color: safeConfig.pinyin_color ?? DEFAULT_CONFIG.pinyin_color,
      font_style: safeConfig.font_style ?? DEFAULT_CONFIG.font_style,
      font_color: safeConfig.font_color ?? DEFAULT_CONFIG.font_color,
      student_name: String(safeConfig.student_name ?? DEFAULT_CONFIG.student_name),
      student_id: String(safeConfig.student_id ?? DEFAULT_CONFIG.student_id),
      class_name: String(safeConfig.class_name ?? DEFAULT_CONFIG.class_name),
      page_size: safeConfig.page_size ?? DEFAULT_CONFIG.page_size,
      show_character_pinyin: safeConfig.show_character_pinyin !== undefined 
        ? safeConfig.show_character_pinyin 
        : DEFAULT_CONFIG.show_character_pinyin,
      character_color: safeConfig.character_color ?? DEFAULT_CONFIG.character_color,
      right_grid_color: safeConfig.right_grid_color ?? DEFAULT_CONFIG.right_grid_color,
      right_grid_type: safeConfig.right_grid_type ?? DEFAULT_CONFIG.right_grid_type,
    }
    setCurrentConfig(mergedConfig)
    setSelectedTemplateId(template.template_id)
    setActivePage('editor')
    alert('模版已应用')
  }, [currentConfig])

  const handleApplyExportHistory = useCallback((historyItem) => {
    if (!historyItem || !historyItem.config_data) {
      alert('历史记录数据无效')
      return
    }
    
    const safeConfig = historyItem.config_data && typeof historyItem.config_data === 'object' 
      ? historyItem.config_data 
      : {}
    
    const mergedConfig = {
      ...currentConfig,
      input_text: safeConfig.input_text ?? DEFAULT_CONFIG.input_text,
      scene_type: safeConfig.scene_type ?? DEFAULT_CONFIG.scene_type,
      grid_type: safeConfig.grid_type ?? DEFAULT_CONFIG.grid_type,
      grid_color: safeConfig.grid_color ?? DEFAULT_CONFIG.grid_color,
      grid_size: safeConfig.grid_size ?? DEFAULT_CONFIG.grid_size,
      grid_size_cm: safeConfig.grid_size_cm ?? DEFAULT_CONFIG.grid_size_cm,
      lines_per_char: safeConfig.lines_per_char ?? DEFAULT_CONFIG.lines_per_char,
      show_pinyin: safeConfig.show_pinyin ?? DEFAULT_CONFIG.show_pinyin,
      pinyin_color: safeConfig.pinyin_color ?? DEFAULT_CONFIG.pinyin_color,
      font_style: safeConfig.font_style ?? DEFAULT_CONFIG.font_style,
      font_color: safeConfig.font_color ?? DEFAULT_CONFIG.font_color,
      student_name: String(safeConfig.student_name ?? DEFAULT_CONFIG.student_name),
      student_id: String(safeConfig.student_id ?? DEFAULT_CONFIG.student_id),
      class_name: String(safeConfig.class_name ?? DEFAULT_CONFIG.class_name),
      page_size: safeConfig.page_size ?? DEFAULT_CONFIG.page_size,
      show_character_pinyin: safeConfig.show_character_pinyin !== undefined 
        ? safeConfig.show_character_pinyin 
        : DEFAULT_CONFIG.show_character_pinyin,
      character_color: safeConfig.character_color ?? DEFAULT_CONFIG.character_color,
      right_grid_color: safeConfig.right_grid_color ?? DEFAULT_CONFIG.right_grid_color,
      right_grid_type: safeConfig.right_grid_type ?? DEFAULT_CONFIG.right_grid_type,
    }
    setCurrentConfig(mergedConfig)
    setSelectedTemplateId(null)
    setActivePage('editor')
    alert('已加载历史配置，可在编辑页面修改')
  }, [currentConfig])

  return (
    <div className="app">
      <Sidebar activePage={activePage} onPageChange={setActivePage} />
      <main className="main-content">
        {activePage === 'editor' && (
          <CopybookEditor 
            config={currentConfig} 
            onConfigChange={handleConfigChange}
            selectedTemplateId={selectedTemplateId}
            onTemplateIdChange={setSelectedTemplateId}
          />
        )}
        {activePage === 'templates' && (
          <TemplateManager
            currentConfig={currentConfig}
            onApplyTemplate={handleApplyTemplate}
          />
        )}
        {activePage === 'history' && (
          <ExportHistory 
            onEditHistory={handleApplyExportHistory}
          />
        )}
      </main>
    </div>
  )
}

export default App
