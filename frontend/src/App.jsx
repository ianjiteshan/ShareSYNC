import React from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth.jsx";
import { ThemeProvider } from "./components/ThemeProvider";

// Pages
import HomePage from "./components/HomePage";
import UploadPage from "./components/UploadPage";
import P2PPage from "./components/P2PPage";
import AuthPage from "./components/AuthPage";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import FilesPage from "./components/FilesPage";
import DownloadPage from "./components/DownloadPage";
import TermsOfService from "./components/TermsOfService";
import PrivacyPolicy from "./components/PrivacyPolicy";
import Footer from "./components/Footer";
import ProtectedRoute from "./components/ProtectedRoute";
import CloudQuickNav from "./components/CloudQuickNav";

import "./App.css";

function Layout({ children }) {
  const location = useLocation();

  // Pages where footer should NOT show
  const hideFooterPaths = [
    "/terms",
    "/privacy",
    "/auth",
    "/dashboard",
    "/files",
  ];

  // Match share/ANY_ID
  const hideFooter =
    hideFooterPaths.includes(location.pathname) ||
    location.pathname.startsWith("/share/");

  return (
    <>
      {children}
      {!hideFooter && <Footer />}
    </>
  );
}

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <AuthProvider>
        <Router>
          <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex flex-col">

            {/* Background Effects */}
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

            <div className="flex-1">
              <Layout>
                <Routes>
                  {/* Public */}
                  <Route path="/" element={<HomePage />} />
                  <Route path="/auth" element={<AuthPage />} />
                  <Route path="/terms" element={<TermsOfService />} />
                  <Route path="/privacy" element={<PrivacyPolicy />} />

                  {/* ⭐ PUBLIC SHARE/DOWNLOAD PAGE */}
                  <Route path="/share/:fileId" element={<DownloadPage />} />

                  {/* Protected */}
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

                  <Route path="/p2p" element={<P2PPage />} />
                </Routes>
              </Layout>
            </div>

          </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
