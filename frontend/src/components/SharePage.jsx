import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Loader2, Download, Lock, AlertCircle, File, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default function SharePage() {
  const { fileId } = useParams()
  const navigate = useNavigate()
  const [fileInfo, setFileInfo] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [password, setPassword] = useState('')
  const [isDownloading, setIsDownloading] = useState(false)
  const [passwordRequired, setPasswordRequired] = useState(false)

  const fetchFileInfo = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/share/${fileId}`)
      const data = await response.json()

      if (data.success) {
        setFileInfo(data)
        setPasswordRequired(data.has_password)
      } else {
        setError(data.error || 'File not found or has expired.')
      }
    } catch (err) {
      setError('Network error or server is unreachable.')
    } finally {
      setIsLoading(false)
    }
  }, [fileId])

  useEffect(() => {
    fetchFileInfo()
  }, [fetchFileInfo])

  const handleDownload = async (e) => {
    e.preventDefault()
    if (passwordRequired && !password) {
      setError('Please enter the password to download this file.')
      return
    }

    setIsDownloading(true)
    setError(null)

    try {
      const objectKey = fileInfo.object_key
      const query = password ? `?password=${encodeURIComponent(password)}` : ''
      
      const response = await fetch(`/api/download/${objectKey}${query}`)
      const data = await response.json()

      if (data.success) {
        // Redirect to the presigned download URL
        window.location.href = data.download_url
      } else {
        if (data.password_required) {
          setPasswordRequired(true)
          setError(data.error || 'Password required.')
        } else {
          setError(data.error || 'Download failed.')
        }
      }
    } catch (err) {
      setError('Network error during download initiation.')
    } finally {
      setIsDownloading(false)
    }
  }

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-48">
          <Loader2 className="w-8 h-8 text-pink-500 animate-spin" />
          <p className="mt-4 text-gray-400">Loading file information...</p>
        </div>
      )
    }

    if (error && !fileInfo) {
      return (
        <div className="flex flex-col items-center justify-center h-48">
          <AlertCircle className="w-8 h-8 text-red-500" />
          <p className="mt-4 text-red-400 font-medium">{error}</p>
          <Button variant="link" onClick={() => navigate('/')} className="mt-4 text-white">
            Go to Home
          </Button>
        </div>
      )
    }

    const isExpired = fileInfo.expiry_time && new Date(fileInfo.expiry_time) < new Date()
    
    if (isExpired) {
      return (
        <div className="flex flex-col items-center justify-center h-48">
          <Clock className="w-8 h-8 text-yellow-500" />
          <p className="mt-4 text-yellow-400 font-medium">This file has expired and is no longer available.</p>
          <Button variant="link" onClick={() => navigate('/')} className="mt-4 text-white">
            Go to Home
          </Button>
        </div>
      )
    }

    return (
      <form onSubmit={handleDownload} className="space-y-6">
        <div className="flex items-center justify-center space-x-4">
          <File className="w-10 h-10 text-pink-500" />
          <div>
            <h2 className="text-xl font-medium text-white">{fileInfo.filename}</h2>
            <p className="text-gray-400 text-sm">
              {formatFileSize(fileInfo.size)}
              {fileInfo.has_password && <span className="ml-2 text-yellow-500 flex items-center"><Lock className="w-3 h-3 mr-1" /> Password Protected</span>}
            </p>
            <p className="text-gray-500 text-xs mt-1">
              Expires: {new Date(fileInfo.expiry_time).toLocaleString()}
            </p>
          </div>
        </div>

        {passwordRequired && (
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium text-gray-300 flex items-center">
              <Lock className="w-4 h-4 mr-2" /> Enter Password
            </label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="File Password"
              className="bg-gray-800 border-gray-700 text-white"
              required
            />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        <Button
          type="submit"
          className={cn(
            'w-full h-12 bg-pink-500 hover:bg-pink-600 text-white font-medium',
            isDownloading && 'opacity-70 cursor-not-allowed'
          )}
          disabled={isDownloading}
        >
          {isDownloading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Initiating Download...
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              Download File
            </div>
          )}
        </Button>
      </form>
    )
  }

  return (
    <div className="min-h-screen w-full relative flex items-center justify-center p-6">
      {/* Background Effects */}
      <div className="fixed inset-0 -z-50">
        <div className="absolute inset-0 opacity-40" 
             style={{ 
               backgroundImage: "radial-gradient(closest-corner at 120px 36px, rgba(255, 1, 111, 0.19), rgba(255, 1, 111, 0.08)), linear-gradient(rgb(63, 51, 69) 15%, rgb(7, 3, 9))" 
             }}>
        </div>
        <div className="absolute inset-0 bg-noise"></div>
        <div className="absolute inset-0 bg-black/40"></div>
      </div>

      <Card className="relative z-10 max-w-md w-full bg-black/40 border-gray-700/50 backdrop-blur-sm">
        <CardContent className="p-8">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-light text-white mb-1">Secure File Share</h1>
            <p className="text-gray-400 text-sm">Download your file from the cloud</p>
          </div>
          {renderContent()}
        </CardContent>
      </Card>
    </div>
  )
}
