import React, { useState, useEffect } from 'react';

const FilePreview = ({ file, className = "" }) => {
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!file) return;

    // Create preview URL for different file types
    if (file instanceof File) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      
      return () => {
        URL.revokeObjectURL(url);
      };
    }
  }, [file]);

  const getFileIcon = (mimeType) => {
    if (!mimeType) return '📄';
    
    if (mimeType.startsWith('image/')) return '🖼️';
    if (mimeType.startsWith('video/')) return '🎥';
    if (mimeType.startsWith('audio/')) return '🎵';
    if (mimeType.includes('pdf')) return '📕';
    if (mimeType.includes('word') || mimeType.includes('document')) return '📝';
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '📊';
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return '📈';
    if (mimeType.includes('zip') || mimeType.includes('archive')) return '🗜️';
    if (mimeType.includes('text')) return '📄';
    
    return '📄';
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const renderPreview = () => {
    if (!file) return null;

    const mimeType = file.type || '';
    
    // Image preview
    if (mimeType.startsWith('image/') && previewUrl) {
      return (
        <div className="relative">
          <img
            src={previewUrl}
            alt={file.name}
            className="max-w-full max-h-64 object-contain rounded-lg"
            onError={() => setError('Failed to load image')}
          />
        </div>
      );
    }
    
    // Video preview
    if (mimeType.startsWith('video/') && previewUrl) {
      return (
        <video
          src={previewUrl}
          controls
          className="max-w-full max-h-64 rounded-lg"
          onError={() => setError('Failed to load video')}
        >
          Your browser does not support video playback.
        </video>
      );
    }
    
    // Audio preview
    if (mimeType.startsWith('audio/') && previewUrl) {
      return (
        <div className="w-full">
          <audio
            src={previewUrl}
            controls
            className="w-full"
            onError={() => setError('Failed to load audio')}
          >
            Your browser does not support audio playback.
          </audio>
        </div>
      );
    }
    
    // Text preview (for small text files)
    if (mimeType.startsWith('text/') && file.size < 1024 * 1024) { // 1MB limit
      return (
        <div className="bg-gray-100 p-4 rounded-lg max-h-64 overflow-auto">
          <TextFilePreview file={file} />
        </div>
      );
    }
    
    // Default file icon
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-gray-50 rounded-lg">
        <div className="text-6xl mb-2">{getFileIcon(mimeType)}</div>
        <p className="text-gray-600 text-sm">Preview not available</p>
      </div>
    );
  };

  if (error) {
    return (
      <div className={`file-preview-error ${className}`}>
        <div className="flex flex-col items-center justify-center p-8 bg-red-50 rounded-lg">
          <div className="text-4xl mb-2">⚠️</div>
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`file-preview ${className}`}>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        {/* File info header */}
        <div className="flex items-center gap-3 mb-4 pb-3 border-b border-gray-100">
          <div className="text-2xl">{getFileIcon(file.type)}</div>
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-gray-900 truncate">{file.name}</h3>
            <p className="text-sm text-gray-500">
              {formatFileSize(file.size)} • {file.type || 'Unknown type'}
            </p>
          </div>
        </div>
        
        {/* Preview content */}
        <div className="preview-content">
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            renderPreview()
          )}
        </div>
      </div>
    </div>
  );
};

// Text file preview component
const TextFilePreview = ({ file }) => {
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      setContent(e.target.result);
      setIsLoading(false);
    };
    reader.onerror = () => {
      setContent('Error reading file');
      setIsLoading(false);
    };
    reader.readAsText(file);
  }, [file]);

  if (isLoading) {
    return <div className="text-gray-500">Loading...</div>;
  }

  return (
    <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
      {content.length > 2000 ? content.substring(0, 2000) + '...' : content}
    </pre>
  );
};

// File preview modal for full-screen viewing
const FilePreviewModal = ({ file, isOpen, onClose }) => {
  if (!isOpen || !file) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] w-full mx-4 overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold truncate">{file.name}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ✕
          </button>
        </div>
        
        <div className="p-4 overflow-auto max-h-[calc(90vh-80px)]">
          <FilePreview file={file} />
        </div>
      </div>
    </div>
  );
};

export { FilePreview, FilePreviewModal };
export default FilePreview;

