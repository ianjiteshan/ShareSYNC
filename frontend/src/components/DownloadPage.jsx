import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Download,
  Lock,
  Clock,
  FileText,
  AlertCircle,
  Loader2,
  CheckCircle,
  Home
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatTimeRemaining(expiryDate) {
  const now = new Date()
  const expiry = new Date(expiryDate)
  const diff = expiry - now
  
  if (diff <= 0) return null
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)
  
  if (days > 0) return `Expires in ${days} day${days > 1 ? 's' : ''}`
  if (hours > 0) return `Expires in ${hours} hour${hours > 1 ? 's' : ''}`
  return 'Expires in less than 1 hour'
}

export default function DownloadPage() {
  const { fileId } = useParams()
  const [fileInfo, setFileInfo] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [password, setPassword] = useState('')
  const [showPasswordInput, setShowPasswordInput] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState(null)

  useEffect(() => {
    fetchFileInfo()
  }, [fileId])

  const fetchFileInfo = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await fetch(`/api/share/${fileId}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('File not found or has expired')
        }
        throw new Error('Failed to fetch file information')
      }
      
      const data = await response.json()
      setFileInfo(data)
      setShowPasswordInput(data.has_password || false)
    } catch (err) {
      console.error('Error fetching file info:', err)
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
      setIsDownloading(true)
      setDownloadError(null)
      
      const url = `/api/download/${fileInfo.storage_key || fileId}`
      const params = new URLSearchParams()
      
      if (password) {
        params.append('password', password)
      }
      
      const downloadUrl = params.toString() ? `${url}?${params}` : url
      
      const response = await fetch(downloadUrl, {
        credentials: 'include'
      })
      
      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Incorrect password')
        }
        if (response.status === 404) {
          throw new Error('File not found')
        }
        throw new Error('Download failed')
      }
      
      // Get filename from Content-Disposition header or use original name
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = fileInfo.original_name || 'download'
      
      if (contentDisposition) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition)
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '')
        }
      }
      
      // Download the file
      const blob = await response.blob()
      const blobUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(blobUrl)
      document.body.removeChild(a)
    } catch (err) {
      console.error('Download error:', err)
      setDownloadError(err.message)
    } finally {
      setIsDownloading(false)
    }
  }

  // Check if file is expired
  const isExpired = fileInfo && new Date(fileInfo.expires_at) < new Date()
  const timeRemaining = fileInfo ? formatTimeRemaining(fileInfo.expires_at) : null

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-12 text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
            <p className="text-gray-600 dark:text-gray-400">Loading file information...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="w-full max-w-md border-red-200 dark:border-red-800">
            <CardContent className="p-12 text-center">
              <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                File Not Available
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {error}
              </p>
              <Link to="/">
                <Button>
                  <Home className="w-4 h-4 mr-2" />
                  Go to Homepage
                </Button>
              </Link>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  if (isExpired) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Card className="w-full max-w-md">
            <CardContent className="p-12 text-center">
              <Clock className="w-16 h-16 text-orange-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Link Expired
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                This file link has expired and is no longer available for download.
              </p>
              <Link to="/">
                <Button>
                  <Home className="w-4 h-4 mr-2" />
                  Go to Homepage
                </Button>
              </Link>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-6 h-6 text-blue-500" />
              Download File
            </CardTitle>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* File Information */}
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                  Filename
                </p>
                <p className="font-semibold text-gray-900 dark:text-white break-all">
                  {fileInfo.original_name}
                </p>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                    File Size
                  </p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {formatFileSize(fileInfo.file_size)}
                  </p>
                </div>
                
                {timeRemaining && (
                  <div className="text-right">
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                      Availability
                    </p>
                    <p className="text-sm font-medium text-orange-600 dark:text-orange-400 flex items-center gap-1">
                      <Clock className="w-4 h-4" />
                      {timeRemaining}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Password Input */}
            {showPasswordInput && (
              <div className="space-y-2">
                <Label htmlFor="password" className="flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Password Required
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && password) {
                      handleDownload()
                    }
                  }}
                />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  This file is password protected
                </p>
              </div>
            )}

            {/* Download Error */}
            {downloadError && (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-600 dark:text-red-400 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  {downloadError}
                </p>
              </div>
            )}

            {/* Download Button */}
            <Button
              onClick={handleDownload}
              disabled={isDownloading || (showPasswordInput && !password)}
              className="w-full"
              size="lg"
            >
              {isDownloading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Downloading...
                </>
              ) : (
                <>
                  <Download className="w-5 h-5 mr-2" />
                  Download File
                </>
              )}
            </Button>

            {/* Success Message */}
            {!isDownloading && downloadError === null && (
              <div className="text-center">
                <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Click the button above to download
                </p>
              </div>
            )}

            {/* Footer */}
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700 text-center">
              <Link
                to="/"
                className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                Create your own shareable link →
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}