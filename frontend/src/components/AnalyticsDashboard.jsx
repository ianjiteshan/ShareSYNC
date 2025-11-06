import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  TrendingUp,
  FileText,
  Download,
  Link as LinkIcon,
  Calendar,
  Loader2
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function AnalyticsDashboard() {
  const [stats, setStats] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
  try {
    setIsLoading(true)
    setError(null)
    
    const response = await fetch('/api/analytics/dashboard', {
      credentials: 'include'
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch analytics')
    }
    
    const dashboardData = await response.json()  // ✅ FIXED: Only ONE declaration, renamed
    
    // Map backend response to frontend format
    setStats({
      total_files: dashboardData.upload_stats?.total_files || 0,
      total_downloads: dashboardData.upload_stats?.total_downloads || 0,
      active_links: dashboardData.upload_stats?.active_files || 0,
      storage_used: dashboardData.upload_stats?.total_storage || 0,
      files_trend: dashboardData.upload_stats?.files_trend,
      downloads_trend: dashboardData.upload_stats?.downloads_trend,
      recent_files: dashboardData.recent_files || []
    })
  } catch (err) {
    console.error('Error fetching analytics:', err)
    setError(err.message)
  } finally {
    setIsLoading(false)
  }
}


  const StatCard = ({ icon: Icon, label, value, trend, color }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {label}
          </CardTitle>
          <div className={`p-2 rounded-lg ${color}`}>
            <Icon className="w-4 h-4 text-white" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-gray-900 dark:text-white">
            {value}
          </div>
          {trend && (
            <p className="text-sm text-green-600 dark:text-green-400 mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {trend}
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading analytics...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <Link 
            to="/" 
            className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
          
          <Card className="border-red-200 dark:border-red-800">
            <CardContent className="p-8 text-center">
              <p className="text-red-600 dark:text-red-400">{error}</p>
            </CardContent>
          </Card>
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
          
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Analytics Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Track your file sharing activity and performance
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={FileText}
            label="Total Files"
            value={stats?.total_files || 0}
            trend={stats?.files_trend ? `${stats.files_trend} this week` : null}
            color="bg-blue-500"
          />
          
          <StatCard
            icon={Download}
            label="Total Downloads"
            value={stats?.total_downloads || 0}
            trend={stats?.downloads_trend ? `${stats.downloads_trend} this week` : null}
            color="bg-green-500"
          />
          
          <StatCard
            icon={LinkIcon}
            label="Active Links"
            value={stats?.active_links || 0}
            color="bg-purple-500"
          />
          
          <StatCard
            icon={Calendar}
            label="Storage Used"
            value={stats?.storage_used ? formatBytes(stats.storage_used) : '0 MB'}
            color="bg-orange-500"
          />
        </div>

        {/* Recent Activity */}
        {stats?.recent_files && stats.recent_files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
          >
            <Card>
              <CardHeader>
                <CardTitle>Recent Files</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {stats.recent_files.map((file, index) => (
                    <div
                      key={file.id || index}
                      className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                          <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">
                            {file.original_name}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {formatBytes(file.file_size)} • {file.download_count || 0} downloads
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(file.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Empty State */}
        {stats && stats.total_files === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <TrendingUp className="w-16 h-16 text-gray-300 dark:text-gray-700 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No analytics data yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Upload some files to start tracking your analytics
              </p>
              <Link to="/upload">
                <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  Upload Your First File
                </button>
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days} days ago`
  
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  })
}