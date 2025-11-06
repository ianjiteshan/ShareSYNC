import { ThemeProvider } from './components/ThemeProvider'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth.jsx'
import HomePage from './components/HomePage'
import UploadPage from './components/UploadPage'
import P2PPage from './components/P2PPage'
import AuthPage from './components/AuthPage'
import AnalyticsDashboard from './components/AnalyticsDashboard'
import FilesPage from './components/FilesPage' // Added FilesPage
import DownloadPage from './components/DownloadPage' // Added DownloadPage
import TermsOfService from './components/TermsOfService'
import PrivacyPolicy from './components/PrivacyPolicy'
import Footer from './components/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import './App.css'
function App() {
return (
<ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
<AuthProvider>
<Router>
<div className="min-h-screen flex flex-col">
{/* Background Effects */}
<div className="fixed inset-0 -z-50">
<div className="absolute inset-0 opacity-40"
style={{
backgroundImage: "radial-gradient(closest-corner at 120px 36px, rgba(255, 1, 111, 0.19), rgba(255, 1, 111, 0.08)), linear-gradient(rgb(63, 51, 69) 15%, rgb(7, 3, 9))"
}}>
</div>
</div>
      {/* Main Content */}
      <div className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/terms" element={<TermsOfService />} />
          <Route path="/privacy" element={<PrivacyPolicy />} />
          
          {/* Public Download Route */}
          <Route path="/share/:fileId" element={<DownloadPage />} /> 

          {/* Protected Routes */}
          <Route 
            path="/upload" 
            element={
              <ProtectedRoute>
                <UploadPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/p2p" 
            element={<P2PPage />}
          />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <AnalyticsDashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/files" 
            element={
              <ProtectedRoute>
                <FilesPage />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </div>

      {/* Footer - conditionally rendered */}
      <Routes>
        <Route path="/terms" element={null} />
        <Route path="/privacy" element={null} />
        <Route path="/auth" element={null} />
        <Route path="/dashboard" element={null} />
        <Route path="/files" element={null} /> {/* Hide footer on files page */}
        <Route path="/share/:fileId" element={null} /> {/* Hide footer on download page */}
        <Route path="*" element={<Footer />} />
      </Routes>
    </div>
  </Router>
</AuthProvider>
</ThemeProvider>
)
}

export default App