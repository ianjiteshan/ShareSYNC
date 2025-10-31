import React, { useEffect, useRef } from 'react';

// Simple QR Code generator using QR Server API
const QRCodeGenerator = ({ value, size = 200, className = "" }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!value) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, size, size);
    
    // Create QR code using QR Server API
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(value)}`;
    
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      ctx.drawImage(img, 0, 0, size, size);
    };
    img.onerror = () => {
      // Fallback: draw a simple pattern
      drawFallbackQR(ctx, size, value);
    };
    img.src = qrUrl;
  }, [value, size]);

  const drawFallbackQR = (ctx, size, text) => {
    // Simple fallback pattern
    ctx.fillStyle = '#000000';
    ctx.fillRect(0, 0, size, size);
    
    ctx.fillStyle = '#ffffff';
    const cellSize = size / 25;
    
    // Draw a simple pattern
    for (let i = 0; i < 25; i++) {
      for (let j = 0; j < 25; j++) {
        if ((i + j) % 2 === 0) {
          ctx.fillRect(i * cellSize, j * cellSize, cellSize, cellSize);
        }
      }
    }
    
    // Add text in center
    ctx.fillStyle = '#000000';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('QR Code', size / 2, size / 2);
  };

  return (
    <div className={`qr-code-container ${className}`}>
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        className="border border-gray-300 rounded-lg"
        style={{ maxWidth: '100%', height: 'auto' }}
      />
    </div>
  );
};

// QR Code Modal Component
const QRCodeModal = ({ isOpen, onClose, title, value, description }) => {
  if (!isOpen) return null;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(value);
    // You could add a toast notification here
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        
        <div className="text-center">
          <QRCodeGenerator value={value} size={200} className="mx-auto mb-4" />
          
          {description && (
            <p className="text-gray-600 mb-4">{description}</p>
          )}
          
          <div className="bg-gray-100 p-3 rounded-lg mb-4">
            <code className="text-sm break-all">{value}</code>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={copyToClipboard}
              className="flex-1 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
            >
              Copy Link
            </button>
            <button
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// QR Code Share Button Component
const QRShareButton = ({ url, title = "Share File", description = "Scan to access file" }) => {
  const [showModal, setShowModal] = React.useState(false);

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="inline-flex items-center gap-2 bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors"
      >
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M3 4a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm2 2V5h1v1H5zM3 13a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1v-3zm2 2v-1h1v1H5zM13 3a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1V3zm2 2V4h1v1h-1zM11 4a1 1 0 100-2 1 1 0 000 2zM11 7a1 1 0 100-2 1 1 0 000 2zM11 10a1 1 0 100-2 1 1 0 000 2zM11 13a1 1 0 100-2 1 1 0 000 2zM11 16a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
        </svg>
        QR Code
      </button>
      
      <QRCodeModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title={title}
        value={url}
        description={description}
      />
    </>
  );
};

export { QRCodeGenerator, QRCodeModal, QRShareButton };
export default QRCodeGenerator;

