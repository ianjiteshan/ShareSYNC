import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  File as FileIcon,
  Clock,
  Download,
  Trash2,
  Copy,
  Check,
  ExternalLink,
  Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatTimeRemaining(expiryDate) {
  const now = new Date()
  const expiry = new Date(expiryDate)
  const diff = expiry - now
  
  if (diff <= 0) return 'Expired'
  
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)
  
  if (days > 0) return `${days}d remaining`
  if (hours > 0) return `${hours}h remaining`
  return 'Less than 1h'
}

export default function FilesPage() {
  const [files, setFiles] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [copiedId, setCopiedId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    fetchFiles()
  }, [])

  const fetchFiles = async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await fetch('/api/files', {
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch files')
      }
      
      const data = await response.json()
      setFiles(data.files || [])
    } catch (err) {
      console.error('Error fetching files:', err)
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCopyLink = (fileId) => {
    const shareUrl = `${window.location.origin}/share/${fileId}`
    navigator.clipboard.writeText(shareUrl)
    setCopiedId(fileId)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const handleDelete = async (fileId) => {
    if (!confirm('Are you sure you want to delete this file? This action cannot be undone.')) {
      return
    }

    try {
      setDeletingId(fileId)
      
      const response = await fetch(`/api/files/${fileId}/delete`, {
        method: 'DELETE',
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to delete file')
      }
      
      // Remove file from list
      setFiles(files.filter(file => file.id !== fileId))
    } catch (err) {
      console.error('Error deleting file:', err)
      alert('Failed to delete file. Please try again.')
    } finally {
      setDeletingId(null)
    }
  }

  const getExpiryStatus = (expiryDate) => {
    const now = new Date()
    const expiry = new Date(expiryDate)
    const diff = expiry - now
    const hours = diff / (1000 * 60 * 60)
    
    if (hours <= 0) return 'expired'
    if (hours <= 2) return 'expiring-soon'
    return 'active'
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading your files...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                My Files
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                {files.length} {files.length === 1 ? 'file' : 'files'} uploaded
              </p>
            </div>
            
            <Link to="/upload">
              <Button>
                Upload New File
              </Button>
            </Link>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <Card className="mb-6 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
            <CardContent className="p-4">
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Empty State */}
        {!isLoading && files.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <FileIcon className="w-16 h-16 text-gray-300 dark:text-gray-700 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No files yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Upload your first file to get started
              </p>
              <Link to="/upload">
                <Button>Upload File</Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {/* Files List */}
        {files.length > 0 && (
          <div className="space-y-4">
            {files.map((file, index) => {
              const expiryStatus = getExpiryStatus(file.expires_at)
              const isExpired = expiryStatus === 'expired'
              
              return (
                <motion.div
                  key={file.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className={isExpired ? 'opacity-60' : ''}>
                    <CardContent className="p-6">
                      <div className="flex items-start gap-4">
                        {/* File Icon */}
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                            <FileIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                          </div>
                        </div>

                        {/* File Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-4 mb-2">
                            <div className="flex-1 min-w-0">
                              <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                                {file.original_name}
                              </h3>
                              <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400 mt-1">
                                <span>{formatFileSize(file.file_size)}</span>
                                <span>•</span>
                                <span>{formatDate(file.created_at)}</span>
                                <span>•</span>
                                <span className="flex items-center gap-1">
                                  <Download className="w-3 h-3" />
                                  {file.download_count || 0} downloads
                                </span>
                              </div>
                            </div>

                            {/* Status Badge */}
                            <Badge 
                              variant={
                                expiryStatus === 'expired' ? 'destructive' :
                                expiryStatus === 'expiring-soon' ? 'warning' :
                                'success'
                              }
                              className="flex-shrink-0"
                            >
                              <Clock className="w-3 h-3 mr-1" />
                              {formatTimeRemaining(file.expires_at)}
                            </Badge>
                          </div>

                          {/* Share Link */}
                          <div className="flex items-center gap-2 mb-4">
                            <code className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded text-sm text-gray-700 dark:text-gray-300 truncate">
                              {window.location.origin}/share/{file.id}
                            </code>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleCopyLink(file.id)}
                              disabled={isExpired}
                            >
                              {copiedId === file.id ? (
                                <>
                                  <Check className="w-4 h-4 mr-2" />
                                  Copied!
                                </>
                              ) : (
                                <>
                                  <Copy className="w-4 h-4 mr-2" />
                                  Copy Link
                                </>
                              )}
                            </Button>

                            <a
                              href={`/share/${file.id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={isExpired}
                              >
                                <ExternalLink className="w-4 h-4 mr-2" />
                                Open
                              </Button>
                            </a>

                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleDelete(file.id)}
                              disabled={deletingId === file.id}
                            >
                              {deletingId === file.id ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  Deleting...
                                </>
                              ) : (
                                <>
                                  <Trash2 className="w-4 h-4 mr-2" />
                                  Delete
                                </>
                              )}
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}