import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Upload, 
  Zap, 
  Shield, 
  Clock,
  ArrowRight,
  FileText,
  BarChart3,
  Users
} from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import Footer from '@/components/Footer'
import { ModeToggle } from '@/components/ModeToggle';

export default function HomePage() {
  const { isAuthenticated, user } = useAuth()

  const features = [
    {
      icon: Upload,
      title: 'Easy File Sharing',
      description: 'Upload files up to 100MB and share them instantly with a simple link.',
      link: isAuthenticated ? '/upload' : '/auth'
    },
    {
      icon: Zap,
      title: 'P2P Transfer',
      description: 'Direct peer-to-peer file transfer with no server storage required.',
      link: isAuthenticated ? '/p2p' : '/auth'
    },
    {
      icon: Shield,
      title: 'Password Protection',
      description: 'Secure your files with password protection for sensitive content.',
      link: isAuthenticated ? '/upload' : '/auth'
    },
    {
      icon: Clock,
      title: 'Auto Expiry',
      description: 'Set custom expiration times for your shared links (2h, 5h, 24h).',
      link: isAuthenticated ? '/upload' : '/auth'
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Navigation */}
      <nav className="border-b border-gray-200 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 backdrop-blur-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Upload className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">
                ShareSync
              </span>
            </Link>

            <div className="flex items-center gap-4">
              <ModeToggle />
              
              {isAuthenticated ? (
                <>
                  <Link to="/files">
                    <Button variant="ghost" size="sm">
                      <FileText className="w-4 h-4 mr-2" />
                      My Files
                    </Button>
                  </Link>
                  <Link to="/analytics">
                    <Button variant="ghost" size="sm">
                      <BarChart3 className="w-4 h-4 mr-2" />
                      Analytics
                    </Button>
                  </Link>
                  <Link to="/upload">
                    <Button>Upload</Button>
                  </Link>
                </>
              ) : (
                <Link to="/auth">
                  <Button>Sign In</Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
            Share Files
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {' '}Instantly
            </span>
          </h1>
          
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
            Fast, secure, and temporary file sharing. Upload, share via link or P2P, 
            and let files auto-delete after expiry.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {isAuthenticated ? (
              <>
                <Link to="/upload">
                  <Button size="lg" className="px-8">
                    <Upload className="w-5 h-5 mr-2" />
                    Upload File
                  </Button>
                </Link>
                <Link to="/p2p">
                  <Button size="lg" variant="outline" className="px-8">
                    <Zap className="w-5 h-5 mr-2" />
                    P2P Transfer
                  </Button>
                </Link>
              </>
            ) : (
              <>
                <Link to="/auth">
                  <Button size="lg" className="px-8">
                    Get Started
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
                <Link to="/auth">
                  <Button size="lg" variant="outline" className="px-8">
                    Sign In
                  </Button>
                </Link>
              </>
            )}
          </div>

          {isAuthenticated && user && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="mt-6 text-gray-600 dark:text-gray-400"
            >
              Welcome back, <span className="font-semibold">{user.name}</span>!
            </motion.p>
          )}
        </motion.div>

        {/* Features Grid */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Link to={feature.link}>
                <Card className="h-full hover:shadow-lg transition-all duration-300 hover:-translate-y-1 cursor-pointer">
                  <CardContent className="p-6">
                    <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mb-4">
                      <feature.icon className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Stats Section */}
        {isAuthenticated && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="mt-24"
          >
            <Card className="bg-gradient-to-br from-blue-500 to-purple-600 text-white">
              <CardContent className="p-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
                  <div>
                    <FileText className="w-8 h-8 mx-auto mb-2 opacity-80" />
                    <p className="text-3xl font-bold mb-1">Fast</p>
                    <p className="opacity-80">Upload & Share</p>
                  </div>
                  <div>
                    <Shield className="w-8 h-8 mx-auto mb-2 opacity-80" />
                    <p className="text-3xl font-bold mb-1">Secure</p>
                    <p className="opacity-80">Password Protected</p>
                  </div>
                  <div>
                    <Clock className="w-8 h-8 mx-auto mb-2 opacity-80" />
                    <p className="text-3xl font-bold mb-1">Temporary</p>
                    <p className="opacity-80">Auto-Delete</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* How It Works */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="mt-24"
        >
          <h2 className="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
            How It Works
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">1</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Upload
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Select and upload your file (up to 100MB)
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">2</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Share
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Get an instant shareable link or QR code
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600 dark:text-green-400">3</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Auto-Delete
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Files automatically expire after set time
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      <Footer />
    </div>
  )
}