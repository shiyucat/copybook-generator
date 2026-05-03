import React, { useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import CopybookEditor from './components/CopybookEditor'
import TemplateManager from './components/TemplateManager'
import ExportHistory from './components/ExportHistory'
import StudentManager from './components/StudentManager'
import CurrentTasks from './components/CurrentTasks'
import AssignmentDialog from './components/AssignmentDialog'
import MyAssignments from './components/MyAssignments'
import { assignmentApi, studentApi } from './services/api'
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

const USER_MODE_TEACHER = 'teacher'
const USER_MODE_STUDENT = 'student'

function App() {
  const [activePage, setActivePage] = useState('editor')
  const [currentConfig, setCurrentConfig] = useState({ ...DEFAULT_CONFIG })
  const [selectedTemplateId, setSelectedTemplateId] = useState(null)

  const [userMode, setUserMode] = useState(USER_MODE_TEACHER)
  const [currentStudent, setCurrentStudent] = useState(null)
  const [showStudentLoginDialog, setShowStudentLoginDialog] = useState(false)
  const [loginStudentNo, setLoginStudentNo] = useState('')
  const [loggingIn, setLoggingIn] = useState(false)

  const [showAssignmentDialog, setShowAssignmentDialog] = useState(false)
  const [selectedStudentForAssignment, setSelectedStudentForAssignment] = useState(null)

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

  const handleAddAssignment = useCallback((student) => {
    setSelectedStudentForAssignment(student)
    setShowAssignmentDialog(true)
  }, [])

  const handleAssignTask = useCallback(async (data) => {
    const { student, template, characters } = data
    
    const assignmentData = {
      student_no: student.student_no,
      template_id: template.template_id,
      characters: characters,
      scene_type: template.config_data?.scene_type || 'normal',
      config_data: {
        ...template.config_data,
        input_text: characters,
      },
    }

    try {
      await assignmentApi.create(assignmentData)
      alert('作业布置成功！')
      setShowAssignmentDialog(false)
      setSelectedStudentForAssignment(null)
    } catch (err) {
      alert(`布置作业失败: ${err.message}`)
      throw err
    }
  }, [])

  const handleStudentLogin = useCallback(async () => {
    if (!loginStudentNo.trim()) {
      alert('请输入学号')
      return
    }

    setLoggingIn(true)
    try {
      const student = await studentApi.getByNo(loginStudentNo.trim())
      if (student) {
        setCurrentStudent(student)
        setUserMode(USER_MODE_STUDENT)
        setShowStudentLoginDialog(false)
        setLoginStudentNo('')
        setActivePage('editor')
        alert(`欢迎回来，${student.name}！`)
      } else {
        alert('未找到该学生，请检查学号是否正确')
      }
    } catch (err) {
      alert(`登录失败: ${err.message}`)
    } finally {
      setLoggingIn(false)
    }
  }, [loginStudentNo])

  const handleSwitchToStudent = useCallback(() => {
    setShowStudentLoginDialog(true)
  }, [])

  const handleSwitchToTeacher = useCallback(() => {
    setUserMode(USER_MODE_TEACHER)
    setCurrentStudent(null)
    setActivePage('editor')
  }, [])

  const handleImportAssignment = useCallback((assignment) => {
    if (!assignment || !assignment.config_data) {
      alert('作业数据无效')
      return
    }

    const safeConfig = assignment.config_data && typeof assignment.config_data === 'object' 
      ? assignment.config_data 
      : {}
    
    const mergedConfig = {
      ...currentConfig,
      input_text: assignment.characters || DEFAULT_CONFIG.input_text,
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
      student_name: currentStudent?.name || String(safeConfig.student_name ?? DEFAULT_CONFIG.student_name),
      student_id: currentStudent?.student_no || String(safeConfig.student_id ?? DEFAULT_CONFIG.student_id),
      class_name: currentStudent?.class_name || String(safeConfig.class_name ?? DEFAULT_CONFIG.class_name),
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
    alert('作业已导入字帖编辑器，可进行打印')
  }, [currentConfig, currentStudent])

  const renderStudentLoginDialog = () => {
    if (!showStudentLoginDialog) return null

    return (
      <div className="modal-overlay" onClick={() => setShowStudentLoginDialog(false)}>
        <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '400px', width: '90vw' }}>
          <div className="modal-header">
            <h3>学生登录</h3>
            <button
              className="modal-close"
              onClick={() => setShowStudentLoginDialog(false)}
            >
              ✕
            </button>
          </div>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">请输入学号</label>
              <input
                type="text"
                className="form-input"
                value={loginStudentNo}
                onChange={(e) => setLoginStudentNo(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleStudentLogin()}
                placeholder="请输入您的学号"
                autoFocus
              />
            </div>
            <p style={{ fontSize: '12px', color: '#888', marginTop: '8px' }}>
              请输入老师为您创建的学号进行登录
            </p>
          </div>
          <div className="modal-footer">
            <button
              className="btn btn-secondary"
              onClick={() => setShowStudentLoginDialog(false)}
              disabled={loggingIn}
            >
              取消
            </button>
            <button
              className="btn btn-primary"
              onClick={handleStudentLogin}
              disabled={loggingIn || !loginStudentNo.trim()}
            >
              {loggingIn ? '登录中...' : '登录'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <Sidebar 
        activePage={activePage} 
        onPageChange={setActivePage}
        userMode={userMode}
        currentStudent={currentStudent}
        onSwitchToStudent={handleSwitchToStudent}
        onSwitchToTeacher={handleSwitchToTeacher}
      />
      <main className="main-content">
        {userMode === USER_MODE_TEACHER && (
          <>
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
            {activePage === 'students' && (
              <StudentManager 
                onAddAssignment={handleAddAssignment}
              />
            )}
            {activePage === 'tasks' && (
              <CurrentTasks />
            )}
          </>
        )}
        {userMode === USER_MODE_STUDENT && (
          <>
            {activePage === 'editor' && (
              <CopybookEditor 
                config={currentConfig} 
                onConfigChange={handleConfigChange}
                selectedTemplateId={selectedTemplateId}
                onTemplateIdChange={setSelectedTemplateId}
              />
            )}
            {activePage === 'my-assignments' && (
              <MyAssignments 
                studentNo={currentStudent?.student_no}
                onImportAssignment={handleImportAssignment}
              />
            )}
          </>
        )}
      </main>
      {renderStudentLoginDialog()}
      {showAssignmentDialog && selectedStudentForAssignment && (
        <AssignmentDialog
          student={selectedStudentForAssignment}
          onClose={() => {
            setShowAssignmentDialog(false)
            setSelectedStudentForAssignment(null)
          }}
          onAssign={handleAssignTask}
        />
      )}
    </div>
  )
}

export default App
