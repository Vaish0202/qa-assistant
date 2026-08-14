import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Analyze from './pages/Analyze'
import History from './pages/History'

function App() {
  const isLoggedIn = !!localStorage.getItem('user_id')

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#0f0f1a] text-white">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            isLoggedIn ? (
              <div className="flex min-h-screen">
                <Sidebar />
                <div className="flex-1 ml-64">
                  <Routes>
                    <Route path="/analyze" element={<Analyze />} />
                    <Route path="/history" element={<History />} />
                    <Route path="/" element={<Navigate to="/analyze" />} />
                  </Routes>
                </div>
              </div>
            ) : (
              <Navigate to="/login" />
            )
          } />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App