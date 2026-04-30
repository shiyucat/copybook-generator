const API_BASE = '/api'

export const templateApi = {
  async getAll() {
    const response = await fetch(`${API_BASE}/templates`)
    if (!response.ok) throw new Error('获取模版列表失败')
    const data = await response.json()
    if (!data.success) throw new Error(data.error || '获取模版列表失败')
    return data.data || []
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

export default templateApi
