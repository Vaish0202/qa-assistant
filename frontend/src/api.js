import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

export const API = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' }
})

// Send the login token with every request
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Token missing or expired -> back to the login page
API.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !err.config.url.startsWith('/auth/')) {
      localStorage.clear()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const loginUser = (username, password) =>
  API.post('/auth/login', { username, password })

export const registerUser = (username, password) =>
  API.post('/auth/register', { username, password })

export const analyzeTestcase = (data) => API.post('/analyze', data)

export const getHistory = () => API.get('/history')

export const sendFollowup = (session_id, message) =>
  API.post('/chat/followup', { session_id, message })

export const getChatSession = (sessionId) => API.get(`/chat/session/${sessionId}`)

export const createJiraTicket = (data) => API.post('/jira/create', data)

export const healthCheck = () => API.get('/health')