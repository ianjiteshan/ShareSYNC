// ✅ FINAL MERGED APP.JSX (Best UI + All Pages Supported)

import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth.jsx";
import { ThemeProvider } from "./components/ThemeProvider";  // <-- from 00App.jsx

// Pages
import HomePage from "./components/HomePage";
import UploadPage from "./components/UploadPage";
import P2PPage from "./components/P2PPage";
import AuthPage from "./components/AuthPage";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import FilesPage from "./components/FilesPage";          // ✅ new
import DownloadPage from "./components/DownloadPage";    // ✅ new
import TermsOfService from "./components/TermsOfService";
import PrivacyPolicy from "./components/PrivacyPolicy";
import Footer from "./components/Footer";
import ProtectedRoute from "./components/ProtectedRoute";
import CloudQuickNav from "./components/CloudQuickNav";


import "./App.css";

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <AuthProvider>
        <Router>
          <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col">

            {/* Background Effects (from your original App.jsx) */}
            <div className="fixed inset-0 -z-50">
              <div
                className="absolute inset-0 opacity-40"
                style={{
                  backgroundImage:
                    "radial-gradient(closest-corner at 120px 36px, rgba(255, 1, 111, 0.19), rgba(255, 1, 111, 0.08)), linear-gradient(rgb(63, 51, 69) 15%, rgb(7, 3, 9))",
                }}
              ></div>
              <div className="absolute inset-0 bg-black/40"></div>
            </div>

            {/* Main Content */}
            <div className="flex-1">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/auth" element={<AuthPage />} />
                <Route path="/terms" element={<TermsOfService />} />
                <Route path="/privacy" element={<PrivacyPolicy />} />

                {/* ✅ PUBLIC DOWNLOAD PAGE SUPPORT */}
                <Route path="/share/:fileId" element={<DownloadPage />} />

                {/* ✅ PROTECTED ROUTES */}
                <Route
                  path="/upload"
                  element={
                    <ProtectedRoute>
                      <UploadPage />
                    </ProtectedRoute>
                  }
                />
                <Route
  path="/cloud"
  element={
    <ProtectedRoute>
      <CloudQuickNav />
    </ProtectedRoute>
  }
/>


                <Route path="/p2p" element={<P2PPage />} />

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

            {/* Conditional Footer rendering */}
            <Routes>
              <Route path="/terms" element={null} />
              <Route path="/privacy" element={null} />
              <Route path="/auth" element={null} />
              <Route path="/dashboard" element={null} />
              <Route path="/files" element={null} />
              <Route path="/share/:fileId" element={null} />
              <Route path="*" element={<Footer />} />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
