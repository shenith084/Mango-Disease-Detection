import React, { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api'

function App() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({ name: '', email: '' })
  const [editingUser, setEditingUser] = useState(null)

  // Fetch users on component mount
  useEffect(() => {
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`${API_BASE_URL}/users`)
      setUsers(response.data.users)
      setError('')
    } catch (err) {
      setError('Failed to fetch users: ' + (err.response?.data?.error || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.name || !formData.email) {
      setError('Both name and email are required')
      return
    }

    try {
      if (editingUser) {
        // Update existing user
        await axios.put(`${API_BASE_URL}/users/${editingUser.id}`, formData)
        setEditingUser(null)
      } else {
        // Create new user
        await axios.post(`${API_BASE_URL}/users`, formData)
      }
      
      setFormData({ name: '', email: '' })
      fetchUsers()
      setError('')
    } catch (err) {
      setError('Failed to save user: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleEdit = (user) => {
    setEditingUser(user)
    setFormData({ name: user.name, email: user.email })
  }

  const handleDelete = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return

    try {
      await axios.delete(`${API_BASE_URL}/users/${userId}`)
      fetchUsers()
      setError('')
    } catch (err) {
      setError('Failed to delete user: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleCancel = () => {
    setEditingUser(null)
    setFormData({ name: '', email: '' })
  }

  return (
    <div className="container">
      <h1>Flask + React + Vite App</h1>
      
      {error && <div className="error">{error}</div>}

      {/* User Form */}
      <form onSubmit={handleSubmit} className="user-form">
        <h2>{editingUser ? 'Edit User' : 'Add New User'}</h2>
        
        <div className="form-group">
          <label htmlFor="name">Name:</label>
          <input
            type="text"
            id="name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="Enter name"
          />
        </div>

        <div className="form-group">
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="Enter email"
          />
        </div>

        <button type="submit">
          {editingUser ? 'Update User' : 'Add User'}
        </button>
        
        {editingUser && (
          <button type="button" onClick={handleCancel}>
            Cancel
          </button>
        )}
      </form>

      {/* Users List */}
      <div>
        <h2>Users ({users.length})</h2>
        
        {loading ? (
          <div className="loading">Loading users...</div>
        ) : users.length === 0 ? (
          <p>No users found. Add some users above!</p>
        ) : (
          users.map(user => (
            <div key={user.id} className="user-card">
              <h3>{user.name}</h3>
              <p>Email: {user.email}</p>
              <p>ID: {user.id}</p>
              <button onClick={() => handleEdit(user)}>
                Edit
              </button>
              <button 
                className="danger" 
                onClick={() => handleDelete(user.id)}
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>

      <button onClick={fetchUsers}>Refresh Users</button>
    </div>
  )
}

export default App