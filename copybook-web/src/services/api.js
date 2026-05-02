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

export default templateApi
