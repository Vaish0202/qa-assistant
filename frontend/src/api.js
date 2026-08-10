import axios from 'axios'

const API = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' }
})

export const loginUser = (username, password) =>
  API.post('/auth/login', { username, password })

export const registerUser = (username, password) =>
  API.post('/auth/register', { username, password })

export const analyzeTestcase = (data) =>
  API.post('/analyze', data)

export const getHistory = (user_id) =>
  API.get(`/history?user_id=${user_id}`)

export const healthCheck = () =>
  API.get('/health')