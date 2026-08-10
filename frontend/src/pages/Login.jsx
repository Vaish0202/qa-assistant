import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginUser, registerUser } from '../api'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async () => {
    if (!username || !password) {
      setError('Please fill in all fields')
      return
    }
    setLoading(true)
    setError('')
    try {
      if (isRegister) {
        await registerUser(username, password)
        setIsRegister(false)
        setError('Registered! Please login.')
      } else {
        const res = await loginUser(username, password)
        localStorage.setItem('user_id', res.data.user_id)
        localStorage.setItem('username', res.data.username)
        navigate('/analyze')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md">

        {/* Header */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">🤖</div>
          <h1 className="text-3xl font-bold text-white">QA Assistant</h1>
          <p className="text-gray-400 mt-2">Agentic AI for intelligent test failure analysis</p>
        </div>

        {/* Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 space-y-4">
          <h2 className="text-xl font-semibold text-white">
            {isRegister ? 'Create Account' : 'Sign In'}
          </h2>

          {error && (
            <div className={`text-sm px-3 py-2 rounded ${
              error.includes('Registered') 
                ? 'bg-green-900 text-green-300' 
                : 'bg-red-900 text-red-300'
            }`}>
              {error}
            </div>
          )}

          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 text-white font-semibold py-3 rounded-lg transition"
          >
            {loading ? 'Please wait...' : isRegister ? 'Register' : 'Login'}
          </button>

          <p className="text-center text-sm text-gray-400">
            {isRegister ? 'Already have an account?' : "Don't have an account?"}
            {' '}
            <button
              onClick={() => { setIsRegister(!isRegister); setError('') }}
              className="text-blue-400 hover:underline"
            >
              {isRegister ? 'Login' : 'Register'}
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}