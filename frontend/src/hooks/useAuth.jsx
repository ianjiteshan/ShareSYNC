import { useState, useEffect, createContext, useContext } from 'react'

const AuthContext = createContext()

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [token, setToken] = useState(null)

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/auth/status', {
        credentials: 'include'
      })
      const data = await response.json()
      
      if (data.authenticated) {
        const userResponse = await fetch('/api/auth/user', {
          credentials: 'include'
        })
        const userData = await userResponse.json()
        
        if (userData.user) {
          setUser(userData.user)
          // CRITICAL FIX: Assume the backend returns the token with user data
          // If the backend is session-based, this token will be null, and we'll rely on cookies.
          // If the backend is JWT-based, this is where we get the token.
          setToken(userData.token || null) 
          setIsAuthenticated(true)
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async () => {
    window.location.href = '/api/auth/login'
  }

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      })
      setUser(null)
      setToken(null)
      setIsAuthenticated(false)
      window.location.href = '/'
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const value = {
    user,
    isLoading,
    isAuthenticated,
    token, // CRITICAL FIX: Expose the token
    login,
    logout,
    checkAuthStatus
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

