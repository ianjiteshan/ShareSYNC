import { useState, useCallback } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Card, CardContent } from '@/components/ui/card'
import { AlertCircle, Clock, File, Loader2, Upload, X, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'

const EXPIRY_OPTIONS = [
  { label: '2 Hours', value: '2h', hours: 2 },
  { label: '5 Hours', value: '5h', hours: 5 },
  { label: '1 Day', value: '1d', hours: 24 },
]

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default function UploadPage() {
  const navigate = useNavigate()
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [error, setError] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [selectedExpiry, setSelectedExpiry] = useState(EXPIRY_OPTIONS[0])
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadResult, setUploadResult] = useState(null)
  const [qrCodeImage, setQrCodeImage] = useState(null)
  const { token } = useAuth()

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragOver(false)
    setError(null)
    const files = e.dataTransfer.files
    if (files.length > 0) {
      setSelectedFile(files[0])
    }
  }, [])

  const handleFileSelect = (e) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setSelectedFile(files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile || !selectedExpiry) return

    try {
      setIsUploading(true)
      setUploadProgress(0)

      // Removed simulated upload progress, relying solely on xhr.upload.onprogress

      const formData = new FormData()
      formData.append('file', selectedFile)
      formData.append('expiry_hours', selectedExpiry.hours)

      const xhr = new XMLHttpRequest()
      xhr.open('POST', '/api/upload', true)
      xhr.withCredentials = true;

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100)
          setUploadProgress(percentComplete)
        }
      }

      xhr.onload = () => {
        setIsUploading(false)
        setUploadProgress(100)
        
        if (xhr.status === 200) {
          const result = JSON.parse(xhr.responseText)
          setUploadResult(result)
          setSelectedFile(null)
          setError(null)
          
          // Fetch QR code
          fetchQrCode(result.file_id)
        } else {
          const errorResponse = JSON.parse(xhr.responseText)
          setError(errorResponse.error || 'Upload failed due to a server error.')
        }
      }

      xhr.onerror = () => {
        setIsUploading(false)
        setError('Network error or server is unreachable.')
      }

      xhr.send(formData)
      
      // Keep the component waiting for the XHR to complete
      await new Promise((resolve, reject) => {
        xhr.onloadend = () => {
          if (xhr.status === 200) {
            resolve()
          } else {
            reject(new Error(xhr.responseText))
          }
        }
      })

    } catch (error) {
      console.error('Upload error:', error)
      setError('Upload failed. Please try again.')
      setIsUploading(false)
    }
  }

  const fetchQrCode = async (fileId) => {
  try {
    const response = await fetch(`/api/files/${fileId}/qr`);
    if (response.ok) {
      setQrCodeImage(`/api/files/${fileId}/qr`);
    } else {
      console.error('Failed to fetch QR code:', response.statusText);
    }
  } catch (error) {
    console.error('Network error fetching QR code:', error);
  }
}



  return (
    <div className="min-h-screen w-full relative">
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

      <div className="relative z-10 max-w-xl w-full mx-auto p-6 pt-12">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/')}
            className="mb-4 text-white/70 hover:text-white hover:bg-white/10"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Button>
          
          <div className="text-center">
            <h1 className="text-3xl font-light text-white mb-2">Upload to Cloud</h1>
            <p className="text-gray-400 text-sm">
              Share files securely with auto-expiry
            </p>
          </div>
        </div>

        {uploadResult ? (
          <Card className="bg-black/40 border-gray-700/50 backdrop-blur-sm">
            <CardContent className="p-6 space-y-6">
              <h2 className="text-xl font-medium text-white">Upload Successful!</h2>
              
              {qrCodeImage && (
                <div className="flex flex-col items-center space-y-3 p-4 bg-gray-800/50 rounded-lg">
                  <p className="text-sm font-medium text-gray-300">Scan to Download</p>
                  <img src={qrCodeImage} alt="QR Code" className="w-32 h-32 p-2 bg-white rounded-md" />
                </div>
              )}
              <div className="space-y-2">
                <p className="text-gray-400">File: <span className="text-white font-medium">{uploadResult.filename}</span></p>
                <p className="text-gray-400">Size: <span className="text-white font-medium">{formatFileSize(uploadResult.size)}</span></p>
                <p className="text-gray-400">Expires: <span className="text-white font-medium">{new Date(uploadResult.expiry_time).toLocaleString()}</span></p>
              </div>
              
              <div className="space-y-3">
                <label className="text-sm font-medium text-gray-300">Shareable Link:</label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    readOnly
                    value={`${window.location.origin}${uploadResult.share_url}`}
                    className="flex-1 p-2 text-sm bg-gray-800 border border-gray-700 rounded-md text-white truncate"
                  />
                  <Button
                    onClick={() => {
                      navigator.clipboard.writeText(`${window.location.origin}${uploadResult.share_url}`)
                      alert('Link copied to clipboard!')
                    }}
                    className="bg-pink-500 hover:bg-pink-600"
                  >
                    Copy
                  </Button>
                </div>
              </div>

              <Button
                onClick={() => {
                  setUploadResult(null)
                  setQrCodeImage(null)
                }}
                className="w-full bg-gray-700 hover:bg-gray-600 text-white"
              >
                Upload Another File
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-black/40 border-gray-700/50 backdrop-blur-sm">
            <CardContent className="p-6 space-y-6">
              {/* Upload Area */}
              <div
                className={cn(
                  'border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer',
                  isDragOver
                    ? 'border-pink-400 bg-pink-500/10'
                    : 'border-gray-600 hover:border-gray-500',
                  selectedFile && 'border-pink-500 bg-pink-500/10'
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById('fileInput')?.click()}
              >
                <input
                  id="fileInput"
                  type="file"
                  className="hidden"
                  onChange={handleFileSelect}
                  disabled={isUploading}
                />

                {selectedFile ? (
                  <div className="space-y-4">
                    <div className="w-12 h-12 bg-pink-500/20 rounded-lg flex items-center justify-center mx-auto">
                      <File className="w-6 h-6 text-pink-400" />
                    </div>
                    <div>
                      <p className="font-medium text-white">
                        {selectedFile.name}
                      </p>
                      <p className="text-gray-400 text-sm mt-1">
                        {formatFileSize(selectedFile.size)}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedFile(null)
                        setError(null)
                      }}
                      disabled={isUploading}
                      className="text-gray-400 hover:text-white hover:bg-gray-800/50"
                    >
                      <X className="w-4 h-4 mr-2" />
                      Remove
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="w-12 h-12 bg-gray-700/50 rounded-lg flex items-center justify-center mx-auto">
                      <Upload className="w-6 h-6 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-lg font-medium text-white mb-1">
                        Drop files here
                      </p>
                      <p className="text-gray-400 text-sm">
                        or click to browse
                      </p>
                    </div>
                    <Badge
                      variant="secondary"
                      className="bg-gray-700/50 text-gray-300 border-0"
                    >
                      Max 100MB
                    </Badge>
                  </div>
                )}
              </div>

              {/* Error Display */}
              {error && (
                <div className="flex items-center gap-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <AlertCircle className="w-4 h-4 text-red-400" />
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              {/* Expiry Selection */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-pink-400" />
                  <label className="text-sm font-medium text-gray-300">
                    Auto-delete after:
                  </label>
                </div>
                <div className="flex gap-2">
                  {EXPIRY_OPTIONS.map((option) => (
                    <Button
                      key={option.value}
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedExpiry(option)}
                      disabled={isUploading}
                      className={cn(
                        'relative border-2 transition-all duration-200 bg-transparent',
                        selectedExpiry.value === option.value
                          ? 'border-pink-500 text-pink-400 bg-pink-500/10'
                          : 'border-gray-600 text-gray-300 hover:border-gray-500 hover:bg-gray-700/30'
                      )}
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Upload Progress */}
              {isUploading && (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400 text-sm">Uploading...</span>
                    <span className="text-white text-sm font-medium">
                      {Math.round(uploadProgress)}%
                    </span>
                  </div>
                  <Progress value={uploadProgress} className="h-2 bg-gray-700/50" />
                </div>
              )}

              {/* Upload Button */}
              <Button
                className={cn(
                  'w-full relative border-2 transition-all duration-200 h-12',
                  'border-pink-500 bg-pink-500/10 text-pink-400 hover:bg-pink-500/20 hover:border-pink-400',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'font-medium'
                )}
                disabled={!selectedFile || isUploading}
                onClick={handleUpload}
              >
                {isUploading ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    Upload & Generate Link
                  </div>
                )}
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

