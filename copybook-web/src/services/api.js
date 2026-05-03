const API_BASE = '/api'

export const templateApi = {
  async getAll() {
    const response = await fetch(`${API_BASE}/templates`)
    if (!response.ok) throw new Error('获取模版列表失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取模版列表失败')
    return data.data || []
  },

  async getPaginated(page = 1, pageSize = 10) {
    const response = await fetch(`${API_BASE}/templates?page=${page}&page_size=${pageSize}`)
    if (!response.ok) throw new Error('获取模版列表失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取模版列表失败')
    return {
      data: data.data || [],
      pagination: data.pagination || {
        page: 1,
        page_size: pageSize,
        total: data.data?.length || 0,
        total_pages: 1
      }
    }
  },

  async getById(id) {
    const response = await fetch(`${API_BASE}/templates/${id}`)
    if (!response.ok) throw new Error('获取模版失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取模版失败')
    return data.data
  },

  async create(templateData) {
    const response = await fetch(`${API_BASE}/templates`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(templateData),
    })
    if (!response.ok) throw new Error('保存模版失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '保存模版失败')
    return data
  },

  async update(id, templateData) {
    const response = await fetch(`${API_BASE}/templates/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(templateData),
    })
    if (!response.ok) throw new Error('更新模版失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '更新模版失败')
    return data
  },

  async delete(id) {
    const response = await fetch(`${API_BASE}/templates/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('删除模版失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '删除模版失败')
    return data
  },

  async checkNameExists(name) {
    const encodedName = encodeURIComponent(name)
    const response = await fetch(`${API_BASE}/templates/check-name/${encodedName}`)
    if (!response.ok) throw new Error('检查名称失败')
    const data = await response.json()
    return data.exists
  },
}

export const exportApi = {
  async exportPdf(exportData) {
    const response = await fetch(`${API_BASE}/export/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(exportData),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || '导出失败')
    }

    const blob = await response.blob()
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = '字帖.pdf'
    
    if (contentDisposition) {
      const match = contentDisposition.match(/filename\*=UTF-8''(.+)/)
      if (match) {
        filename = decodeURIComponent(match[1])
      }
    }

    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    return { success: true, filename }
  },
}

export const pinyinApi = {
  async getPinyin(characters) {
    const response = await fetch(`${API_BASE}/pinyin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ characters }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || '获取拼音失败')
    }

    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取拼音失败')
    return data.data || {}
  },
}

export const exportHistoryApi = {
  async getPaginated(page = 1, pageSize = 10, keyword = '') {
    let url = `${API_BASE}/export-history?page=${page}&page_size=${pageSize}`
    if (keyword) {
      url += `&keyword=${encodeURIComponent(keyword)}`
    }
    const response = await fetch(url)
    if (!response.ok) throw new Error('获取导出历史失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取导出历史失败')
    return {
      data: data.data || [],
      pagination: data.pagination || {
        page: 1,
        page_size: pageSize,
        total: data.data?.length || 0,
        total_pages: 1
      }
    }
  },

  async getById(id) {
    const response = await fetch(`${API_BASE}/export-history/${id}`)
    if (!response.ok) throw new Error('获取历史记录失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取历史记录失败')
    return data.data
  },

  async reExport(id) {
    const response = await fetch(`${API_BASE}/export-history/${id}/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || '导出失败')
    }

    const blob = await response.blob()
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = '字帖.pdf'
    
    if (contentDisposition) {
      const match = contentDisposition.match(/filename\*=UTF-8''(.+)/)
      if (match) {
        filename = decodeURIComponent(match[1])
      }
    }

    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    return { success: true, filename }
  },
}

export const studentApi = {
  async getAll() {
    const response = await fetch(`${API_BASE}/students`)
    if (!response.ok) throw new Error('获取学生列表失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取学生列表失败')
    return data.data || []
  },

  async getPaginated(page = 1, pageSize = 10, keyword = '') {
    let url = `${API_BASE}/students?page=${page}&page_size=${pageSize}`
    if (keyword) {
      url += `&keyword=${encodeURIComponent(keyword)}`
    }
    const response = await fetch(url)
    if (!response.ok) throw new Error('获取学生列表失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取学生列表失败')
    return {
      data: data.data || [],
      pagination: data.pagination || {
        page: 1,
        page_size: pageSize,
        total: data.data?.length || 0,
        total_pages: 1
      }
    }
  },

  async getById(id) {
    const response = await fetch(`${API_BASE}/students/${id}`)
    if (!response.ok) throw new Error('获取学生信息失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取学生信息失败')
    return data.data
  },

  async getByNo(studentNo) {
    const encodedNo = encodeURIComponent(studentNo)
    const response = await fetch(`${API_BASE}/students/by-no/${encodedNo}`)
    if (!response.ok) {
      if (response.status === 404) {
        return null
      }
      throw new Error('获取学生信息失败')
    }
    const data = await response.json()
    if (!data.success) {
      return null
    }
    return data.data
  },

  async create(studentData) {
    const response = await fetch(`${API_BASE}/students`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(studentData),
    })
    if (!response.ok) throw new Error('保存学生失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '保存学生失败')
    return data
  },

  async update(id, studentData) {
    const response = await fetch(`${API_BASE}/students/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(studentData),
    })
    if (!response.ok) throw new Error('更新学生失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '更新学生失败')
    return data
  },

  async delete(id) {
    const response = await fetch(`${API_BASE}/students/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('删除学生失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '删除学生失败')
    return data
  },

  async checkNoExists(studentNo) {
    const encodedNo = encodeURIComponent(studentNo)
    const response = await fetch(`${API_BASE}/students/check-no/${encodedNo}`)
    if (!response.ok) throw new Error('检查学号失败')
    const data = await response.json()
    return data.exists
  },
}

export const assignmentApi = {
  async getPaginated(page = 1, pageSize = 10, studentNo = null, status = null) {
    let url = `${API_BASE}/assignments?page=${page}&page_size=${pageSize}`
    if (studentNo) {
      url += `&student_no=${encodeURIComponent(studentNo)}`
    }
    if (status) {
      url += `&status=${encodeURIComponent(status)}`
    }
    const response = await fetch(url)
    if (!response.ok) throw new Error('获取作业列表失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取作业列表失败')
    return {
      data: data.data || [],
      pagination: data.pagination || {
        page: 1,
        page_size: pageSize,
        total: data.data?.length || 0,
        total_pages: 1
      }
    }
  },

  async getById(id) {
    const response = await fetch(`${API_BASE}/assignments/${id}`)
    if (!response.ok) throw new Error('获取作业信息失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取作业信息失败')
    return data.data
  },

  async create(assignmentData) {
    const response = await fetch(`${API_BASE}/assignments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(assignmentData),
    })
    if (!response.ok) throw new Error('创建作业失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '创建作业失败')
    return data
  },

  async update(id, assignmentData) {
    const response = await fetch(`${API_BASE}/assignments/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(assignmentData),
    })
    if (!response.ok) throw new Error('更新作业失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '更新作业失败')
    return data
  },

  async markComplete(id) {
    const response = await fetch(`${API_BASE}/assignments/${id}/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (!response.ok) throw new Error('标记作业完成失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '标记作业完成失败')
    return data
  },

  async delete(id) {
    const response = await fetch(`${API_BASE}/assignments/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('删除作业失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '删除作业失败')
    return data
  },
}

export default templateApi
