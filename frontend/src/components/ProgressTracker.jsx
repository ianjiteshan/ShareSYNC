import React, { useState, useEffect } from 'react';

const ProgressTracker = ({ 
  progress = 0, 
  status = 'idle', 
  fileName = '', 
  fileSize = 0,
  speed = 0,
  timeRemaining = 0,
  className = "" 
}) => {
  const [animatedProgress, setAnimatedProgress] = useState(0);

  useEffect(() => {
    // Animate progress changes
    const timer = setTimeout(() => {
      setAnimatedProgress(progress);
    }, 100);
    
    return () => clearTimeout(timer);
  }, [progress]);

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatSpeed = (bytesPerSecond) => {
    if (!bytesPerSecond) return '0 B/s';
    return formatFileSize(bytesPerSecond) + '/s';
  };

  const formatTime = (seconds) => {
    if (!seconds || seconds === Infinity) return '--:--';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'uploading':
      case 'downloading':
        return '⬆️';
      case 'processing':
        return '⚙️';
      case 'completed':
        return '✅';
      case 'error':
        return '❌';
      case 'paused':
        return '⏸️';
      case 'cancelled':
        return '🚫';
      default:
        return '📄';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'uploading':
      case 'downloading':
      case 'processing':
        return 'bg-blue-500';
      case 'completed':
        return 'bg-green-500';
      case 'error':
      case 'cancelled':
        return 'bg-red-500';
      case 'paused':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'uploading':
        return 'Uploading...';
      case 'downloading':
        return 'Downloading...';
      case 'processing':
        return 'Processing...';
      case 'completed':
        return 'Completed';
      case 'error':
        return 'Error';
      case 'paused':
        return 'Paused';
      case 'cancelled':
        return 'Cancelled';
      default:
        return 'Ready';
    }
  };

  return (
    <div className={`progress-tracker bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-3">
        <div className="text-2xl">{getStatusIcon()}</div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900 truncate">{fileName || 'File Transfer'}</h4>
          <p className="text-sm text-gray-500">{getStatusText()}</p>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold text-gray-900">{Math.round(animatedProgress)}%</div>
          {fileSize > 0 && (
            <div className="text-xs text-gray-500">{formatFileSize(fileSize)}</div>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ease-out ${getStatusColor()}`}
            style={{ width: `${animatedProgress}%` }}
          />
        </div>
      </div>

      {/* Details */}
      {(speed > 0 || timeRemaining > 0) && (
        <div className="flex justify-between text-sm text-gray-600">
          <div className="flex gap-4">
            {speed > 0 && (
              <span>Speed: {formatSpeed(speed)}</span>
            )}
            {timeRemaining > 0 && (
              <span>Time remaining: {formatTime(timeRemaining)}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Multi-file progress tracker
const MultiFileProgressTracker = ({ transfers = [], className = "" }) => {
  const totalFiles = transfers.length;
  const completedFiles = transfers.filter(t => t.status === 'completed').length;
  const overallProgress = totalFiles > 0 ? (completedFiles / totalFiles) * 100 : 0;

  return (
    <div className={`multi-file-progress ${className}`}>
      {/* Overall Progress */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-gray-900">Overall Progress</h3>
          <span className="text-sm text-gray-600">{completedFiles}/{totalFiles} files</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="h-3 bg-blue-500 rounded-full transition-all duration-300"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        <div className="text-center mt-2 text-sm text-gray-600">
          {Math.round(overallProgress)}% Complete
        </div>
      </div>

      {/* Individual File Progress */}
      <div className="space-y-3">
        {transfers.map((transfer, index) => (
          <ProgressTracker
            key={transfer.id || index}
            progress={transfer.progress}
            status={transfer.status}
            fileName={transfer.fileName}
            fileSize={transfer.fileSize}
            speed={transfer.speed}
            timeRemaining={transfer.timeRemaining}
          />
        ))}
      </div>
    </div>
  );
};

// Compact progress indicator for small spaces
const CompactProgressIndicator = ({ progress = 0, status = 'idle', size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const getStatusColor = () => {
    switch (status) {
      case 'uploading':
      case 'downloading':
      case 'processing':
        return 'text-blue-500';
      case 'completed':
        return 'text-green-500';
      case 'error':
      case 'cancelled':
        return 'text-red-500';
      case 'paused':
        return 'text-yellow-500';
      default:
        return 'text-gray-500';
    }
  };

  if (status === 'completed') {
    return (
      <div className={`${sizeClasses[size]} ${getStatusColor()}`}>
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
      </div>
    );
  }

  if (status === 'error' || status === 'cancelled') {
    return (
      <div className={`${sizeClasses[size]} ${getStatusColor()}`}>
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
        </svg>
      </div>
    );
  }

  // Circular progress indicator
  const radius = size === 'sm' ? 6 : size === 'md' ? 8 : 12;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className={`${sizeClasses[size]} relative`}>
      <svg className="transform -rotate-90 w-full h-full" viewBox="0 0 24 24">
        <circle
          cx="12"
          cy="12"
          r={radius}
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
          className="text-gray-200"
        />
        <circle
          cx="12"
          cy="12"
          r={radius}
          stroke="currentColor"
          strokeWidth="2"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={`transition-all duration-300 ${getStatusColor()}`}
          strokeLinecap="round"
        />
      </svg>
      {size !== 'sm' && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-medium text-gray-600">
            {Math.round(progress)}
          </span>
        </div>
      )}
    </div>
  );
};

export { ProgressTracker, MultiFileProgressTracker, CompactProgressIndicator };
export default ProgressTracker;

