import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  ArrowLeft, 
  Wifi, 
  Users, 
  Upload, 
  Download, 
  File, 
  X, 
  Loader2,
  WifiOff,
  RefreshCw
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { cn } from '@/lib/utils'

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export default function P2PPage() {
  const navigate = useNavigate()
  const [isConnected, setIsConnected] = useState(false)
  const [peers, setPeers] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [transferProgress, setTransferProgress] = useState(0)
  const [isTransferring, setIsTransferring] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('connecting')

  // Simulate connection process
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsConnected(true)
      setConnectionStatus('connected')
      // Simulate some peers
      setPeers([
        { id: '1', name: 'John\'s iPhone', type: 'mobile', status: 'online' },
        { id: '2', name: 'Sarah\'s MacBook', type: 'desktop', status: 'online' },
        { id: '3', name: 'Office PC', type: 'desktop', status: 'idle' }
      ])
    }, 2000)

    return () => clearTimeout(timer)
  }, [])

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

  const handleSendFile = async (peerId) => {
    if (!selectedFile) return

    setIsTransferring(true)
    setTransferProgress(0)

    // Simulate file transfer
    const interval = setInterval(() => {
      setTransferProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setTimeout(() => {
            setIsTransferring(false)
            setSelectedFile(null)
            setTransferProgress(0)
            alert('File sent successfully! (This is a demo)')
          }, 500)
          return 100
        }
        return prev + 5
      })
    }, 100)
  }

  const reconnect = () => {
    setConnectionStatus('connecting')
    setIsConnected(false)
    setPeers([])
    
    setTimeout(() => {
      setIsConnected(true)
      setConnectionStatus('connected')
      setPeers([
        { id: '1', name: 'John\'s iPhone', type: 'mobile', status: 'online' },
        { id: '2', name: 'Sarah\'s MacBook', type: 'desktop', status: 'online' }
      ])
    }, 2000)
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

      <div className="relative z-10 max-w-4xl w-full mx-auto p-6 pt-12">
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
            <h1 className="text-3xl font-light text-white mb-2">P2P File Sharing</h1>
            <p className="text-gray-400 text-sm">
              Share files directly with nearby devices
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Connection Status */}
          <Card className="bg-black/40 border-gray-700/50 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">Connection Status</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={reconnect}
                  className="text-gray-400 hover:text-white hover:bg-gray-800/50"
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>

              <div className="flex items-center gap-3 mb-4">
                {connectionStatus === 'connecting' ? (
                  <>
                    <Loader2 className="w-5 h-5 text-yellow-400 animate-spin" />
                    <span className="text-yellow-400">Connecting to network...</span>
                  </>
                ) : isConnected ? (
                  <>
                    <Wifi className="w-5 h-5 text-green-400" />
                    <span className="text-green-400">Connected to local network</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-5 h-5 text-red-400" />
                    <span className="text-red-400">Not connected</span>
                  </>
                )}
              </div>

              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-gray-400" />
                <span className="text-gray-300 text-sm">
                  {peers.length} device{peers.length !== 1 ? 's' : ''} found
                </span>
              </div>
            </CardContent>
          </Card>

          {/* File Selection */}
          <Card className="bg-black/40 border-gray-700/50 backdrop-blur-sm">
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Select File</h2>
              
              <div
                className={cn(
                  'border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 cursor-pointer',
                  isDragOver
                    ? 'border-pink-400 bg-pink-500/10'
                    : 'border-gray-600 hover:border-gray-500',
                  selectedFile && 'border-pink-500 bg-pink-500/10'
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById('p2pFileInput')?.click()}
              >
                <input
                  id="p2pFileInput"
                  type="file"
                  className="hidden"
                  onChange={handleFileSelect}
                  disabled={isTransferring}
                />

                {selectedFile ? (
                  <div className="space-y-3">
                    <div className="w-10 h-10 bg-pink-500/20 rounded-lg flex items-center justify-center mx-auto">
                      <File className="w-5 h-5 text-pink-400" />
                    </div>
                    <div>
                      <p className="font-medium text-white text-sm">
                        {selectedFile.name}
                      </p>
                      <p className="text-gray-400 text-xs mt-1">
                        {formatFileSize(selectedFile.size)}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedFile(null)
                      }}
                      disabled={isTransferring}
                      className="text-gray-400 hover:text-white hover:bg-gray-800/50"
                    >
                      <X className="w-3 h-3 mr-1" />
                      Remove
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="w-10 h-10 bg-gray-700/50 rounded-lg flex items-center justify-center mx-auto">
                      <Upload className="w-5 h-5 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-white text-sm mb-1">
                        Drop file here
                      </p>
                      <p className="text-gray-400 text-xs">
                        or click to browse
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Transfer Progress */}
        {isTransferring && (
          <Card className="bg-black/40 border-gray-700/50 backdrop-blur-sm mt-6">
            <CardContent className="p-6">
              <div className="flex justify-between items-center mb-3">
                <span className="text-gray-400 text-sm">Transferring file...</span>
                <span className="text-white text-sm font-medium">
                  {Math.round(transferProgress)}%
                </span>
              </div>
              <Progress value={transferProgress} className="h-2 bg-gray-700/50" />
            </CardContent>
          </Card>
        )}

        {/* Available Devices */}
        <Card className="bg-black/40 border-gray-700/50 backdrop-blur-sm mt-6">
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Available Devices</h2>
            
            {peers.length === 0 ? (
              <div className="text-center py-8">
                <Users className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                <p className="text-gray-400">
                  {connectionStatus === 'connecting' 
                    ? 'Searching for devices...' 
                    : 'No devices found on the network'
                  }
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {peers.map((peer) => (
                  <div
                    key={peer.id}
                    className="flex items-center justify-between p-4 bg-gray-800/30 rounded-lg border border-gray-700/50"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-700/50 rounded-lg flex items-center justify-center">
                        {peer.type === 'mobile' ? (
                          <div className="w-5 h-5 bg-gray-400 rounded-sm"></div>
                        ) : (
                          <div className="w-5 h-5 bg-gray-400 rounded"></div>
                        )}
                      </div>
                      <div>
                        <p className="text-white font-medium">{peer.name}</p>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={peer.status === 'online' ? 'default' : 'secondary'}
                            className={cn(
                              'text-xs',
                              peer.status === 'online' 
                                ? 'bg-green-500/20 text-green-400 border-green-500/30' 
                                : 'bg-gray-500/20 text-gray-400 border-gray-500/30'
                            )}
                          >
                            {peer.status}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    
                    <Button
                      size="sm"
                      onClick={() => handleSendFile(peer.id)}
                      disabled={!selectedFile || isTransferring || peer.status !== 'online'}
                      className={cn(
                        'bg-pink-500/10 text-pink-400 border border-pink-500/30 hover:bg-pink-500/20',
                        'disabled:opacity-50 disabled:cursor-not-allowed'
                      )}
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Send
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

