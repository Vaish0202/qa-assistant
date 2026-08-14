import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginUser, registerUser } from '../api'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async () => {
    if (!username || !password) { setError('Please fill in all fields'); return }
    setLoading(true); setError('')
    try {
      if (isRegister) {
        await registerUser(username, password)
        setIsRegister(false)
        setError('success:Registered successfully! Please login.')
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
    <div className="min-h-screen bg-[#0f0f1a] flex">

      {/* Left side — form */}
      <div className="flex-1 flex items-center justify-center px-8">
        <div className="w-full max-w-md">

          {/* Logo */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center text-3xl mx-auto mb-4">
              🤖
            </div>
            <h1 className="text-2xl font-bold text-white">QA Assistant</h1>
            <p className="text-[#6b7280] text-sm mt-1">
              Agentic AI for intelligent test failure analysis
            </p>
          </div>

          {/* Card */}
          <div className="bg-[#13131f] border border-[#2a2a3d] rounded-2xl p-8">
            <h2 className="text-xl font-semibold text-white mb-1">
              {isRegister ? 'Create Account 🚀' : 'Welcome Back! 👋'}
            </h2>
            <p className="text-[#6b7280] text-sm mb-6">
              {isRegister ? 'Sign up to get started' : 'Sign in to continue'}
            </p>

            {error && (
              <div className={`text-sm px-4 py-3 rounded-lg mb-4 ${
                error.startsWith('success:')
                  ? 'bg-green-900/30 border border-green-700 text-green-400'
                  : 'bg-red-900/30 border border-red-700 text-red-400'
              }`}>
                {error.startsWith('success:') ? error.replace('success:', '') : error}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[#9ca3af] mb-1.5">
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-3 text-white placeholder-[#4b5563] focus:outline-none focus:border-indigo-500 text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[#9ca3af] mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                    placeholder="Enter your password"
                    className="w-full bg-[#1e1e30] border border-[#2a2a3d] rounded-lg px-4 py-3 text-white placeholder-[#4b5563] focus:outline-none focus:border-indigo-500 text-sm pr-10"
                  />
                  <button
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3.5 text-[#6b7280] hover:text-white"
                  >
                    {showPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              {!isRegister && (
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-[#9ca3af]">
                    <input type="checkbox" className="rounded border-[#2a2a3d]" />
                    Remember me
                  </label>
                  <button className="text-sm text-indigo-400 hover:text-indigo-300">
                    Forgot password?
                  </button>
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-900 text-white font-semibold py-3 rounded-lg transition flex items-center justify-center gap-2"
              >
                {loading ? (
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>
                ) : (
                  <>
                    <span>🤖</span>
                    <span>{isRegister ? 'Create Account' : 'Sign In'}</span>
                    <span>→</span>
                  </>
                )}
              </button>
            </div>

            <p className="text-center text-sm text-[#6b7280] mt-6">
              {isRegister ? 'Already have an account?' : "Don't have an account?"}
              {' '}
              <button
                onClick={() => { setIsRegister(!isRegister); setError('') }}
                className="text-indigo-400 hover:text-indigo-300 font-medium"
              >
                {isRegister ? 'Login' : 'Register'}
              </button>
            </p>
          </div>

          <p className="text-center text-xs text-[#4b5563] mt-6">
            © 2026 QA Assistant. All rights reserved.
          </p>
        </div>
      </div>

      {/* Right side — features */}
      <div className="hidden lg:flex flex-col justify-center px-16 bg-[#13131f] border-l border-[#2a2a3d] w-80">
        <h3 className="text-lg font-semibold text-white mb-8">
          Why QA Assistant?
        </h3>
        <div className="space-y-6">
          {[
            {
              icon: '🧠',
              title: 'AI-Powered Analysis',
              desc: 'Detect root cause and get smart recommendations'
            },
            {
              icon: '⚡',
              title: 'Faster Resolution',
              desc: 'Fix issues faster with actionable solutions'
            },
            {
              icon: '🎫',
              title: 'Seamless Reporting',
              desc: 'Create Jira tickets in one click'
            },
            {
              icon: '🔒',
              title: 'Secure & Reliable',
              desc: 'Enterprise-grade security for your data'
            }
          ].map((f, i) => (
            <div key={i} className="flex items-start gap-4">
              <div className="w-10 h-10 bg-indigo-900/50 border border-indigo-700 rounded-lg flex items-center justify-center text-lg flex-shrink-0">
                {f.icon}
              </div>
              <div>
                <p className="text-sm font-semibold text-white">{f.title}</p>
                <p className="text-xs text-[#6b7280] mt-0.5">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}