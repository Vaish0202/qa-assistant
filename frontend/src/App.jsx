import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Analyze from './pages/Analyze'
import History from './pages/History'

function App() {
  const isLoggedIn = !!localStorage.getItem('user_id')

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-white">
        <Navbar />
        <Routes>
          <Route path="/" element={<Navigate to={isLoggedIn ? "/analyze" : "/login"} />} />
          <Route path="/login" element={<Login />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App