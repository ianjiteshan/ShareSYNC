import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Wifi, Users, Upload, Download, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import useP2P from '../hooks/useP2P';

const P2PPage = () => {
  const {
    isConnected,
    peers,
    sessionId,
    connectionStatus,
    transferProgress,
    error,
    connectToPeer,
    sendFileToPeer,
    disconnect,
    deviceName
  } = useP2P();

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const [showTransferModal, setShowTransferModal] = useState(false);
  
  // --- ADDED ---
  // This state tracks which peer we are *currently* trying to connect to
  const [connectingTo, setConnectingTo] = useState(null);

  // Handle file selection
  const handleFileSelect = (files) => {
    const fileArray = Array.from(files);
    setSelectedFiles(fileArray);
  };

  // Handle drag and drop
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  // --- UPDATED ---
  // Send file to selected peer
  const handleSendFile = async (peerId, file) => {
    setConnectingTo(peerId); // Set connecting state
    try {
      // First connect to peer if not already connected
      const connected = await connectToPeer(peerId);
      if (!connected) {
        alert('Failed to connect to peer');
        setConnectingTo(null); // Clear state on failure
        return;
      }

      // Send the file
      const success = await sendFileToPeer(peerId, file);
      if (success) {
        setShowTransferModal(true);
      } else {
        alert('Failed to send file');
      }
    } catch (error) {
      console.error('Error sending file:', error);
      alert('Error sending file');
    }
    setConnectingTo(null); // Clear state on success/finish
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Get connection status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'disconnected': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  // Get connection status text
  const getStatusText = (status) => {
    switch (status) {
      case 'connected': return 'Connected to P2P network';
      case 'connecting': return 'Connecting to P2P network...';
      case 'disconnected': return 'Disconnected from P2P network';
      default: return 'Unknown status';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-dotted-pattern opacity-20"></div>
      
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div className="flex items-center gap-4">
            <Link
              to="/"
              className="flex items-center gap-2 text-white/80 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Back to Home</span>
            </Link>
          </div>
          
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 ${getStatusColor(connectionStatus)}`}>
              <Wifi className="w-5 h-5" />
              <span className="text-sm font-medium">{getStatusText(connectionStatus)}</span>
            </div>
          </div>
        </motion.div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left Column - File Upload */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <Upload className="w-6 h-6" />
                Select Files to Share
              </h2>
              
              {/* File Drop Zone */}
              <div
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
                  dragActive
                    ? 'border-blue-400 bg-blue-400/10'
                    : 'border-white/30 hover:border-white/50'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-12 h-12 text-white/60 mx-auto mb-4" />
                <p className="text-white/80 mb-2">
                  Drag and drop files here, or click to select
                </p>
                <p className="text-white/60 text-sm">
                  Any file type, unlimited size for P2P sharing
                </p>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => handleFileSelect(e.target.files)}
                />
              </div>

              {/* Selected Files */}
              {selectedFiles.length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-white mb-3">Selected Files</h3>
                  <div className="space-y-2">
                    {selectedFiles.map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-white/5 rounded-lg p-3"
                      >
                        <div>
                          <p className="text-white font-medium">{file.name}</p>
                          <p className="text-white/60 text-sm">{formatFileSize(file.size)}</p>
                        </div>
                        <button
                          onClick={() => setSelectedFiles(files => files.filter((_, i) => i !== index))}
                          className="text-red-400 hover:text-red-300 transition-colors"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Device Info */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-semibold text-white mb-3">Your Device</h3>
              <div className="space-y-2">
                <p className="text-white/80">
                  <span className="font-medium">Device Name:</span> {deviceName}
                </p>
                <p className="text-white/80">
                  <span className="font-medium">Session ID:</span> {sessionId || 'Not connected'}
                </p>
                <p className="text-white/80">
                  <span className="font-medium">Status:</span> {isConnected ? 'Online' : 'Offline'}
                </p>
              </div>
            </div>
          </motion.div>

          {/* Right Column - Available Peers */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="space-y-6"
          >
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <Users className="w-6 h-6" />
                Available Devices ({peers.length})
              </h2>

              {/* Error Display */}
              {error && (
                <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-lg flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-400" />
                  <span className="text-red-200">{error}</span>
                </div>
              )}

              {/* Connection Status */}
              {!isConnected && (
                <div className="mb-4 p-3 bg-yellow-500/20 border border-yellow-500/30 rounded-lg flex items-center gap-2">
                  <Clock className="w-5 h-5 text-yellow-400" />
                  <span className="text-yellow-200">Connecting to P2P network...</span>
                </div>
              )}

              {/* Peers List */}
              {isConnected && peers.length === 0 && (
                <div className="text-center py-8">
                  <Users className="w-16 h-16 text-white/30 mx-auto mb-4" />
                  <p className="text-white/60">No other devices found on the network</p>
                  <p className="text-white/40 text-sm mt-2">
                    Make sure other devices are on the same network and have ShareSync open
                  </p>
                </div>
              )}

              {peers.length > 0 && (
                <div className="space-y-3">
                  {peers.map((peer) => {
                    
                    // --- UPDATED ---
                    // Define button states for clarity
                    const isConnecting = connectingTo === peer.session_id;
                    const isSending = !!transferProgress[peer.session_id];
                    const isDisabled = isConnecting || isSending;

                    return (
                      <div
                        key={peer.session_id}
                        className="bg-white/5 rounded-xl p-4 border border-white/10 hover:bg-white/10 transition-all duration-300"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <h3 className="text-white font-semibold">{peer.device_name}</h3>
                            <p className="text-white/60 text-sm">
                              Status: {peer.connectionState || 'Available'}
                            </p>
                            <p className="text-white/40 text-xs">
                              Joined: {new Date(peer.joined_at).toLocaleTimeString()}
                            </p>
                          </div>
                          
                          <div className="flex flex-col gap-2">
                            {selectedFiles.length > 0 ? (
                              <div className="space-y-1">
                                {selectedFiles.map((file, index) => (
                                  <button
                                    key={index}
                                    disabled={isDisabled}
                                    onClick={() => handleSendFile(peer.session_id, file)}
                                    className={`bg-gradient-to-r from-blue-500 to-purple-600 text-white px-3 py-1 rounded-lg text-sm font-medium transition-all duration-300 flex items-center gap-1 ${
                                      isDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:from-blue-600 hover:to-purple-700'
                                    }`}
                                  >
                                    <Upload className="w-3 h-3" />
                                    
                                    {/* --- UPDATED --- */}
                                    {/* This is the new button text logic */}
                                    {isConnecting
                                      ? 'Connecting...'
                                      : isSending
                                      ? 'Sending...'
                                      : peer.dataChannelReady
                                      ? `Send ${file.name.substring(0, 15)}...`
                                      : `Connect & Send`}
                                  
                                  </button>
                                ))}
                              </div>
                            ) : (
                              <span className="text-white/40 text-sm">Select files to send</span>
                            )}
                          </div>
                        </div>

                        {/* Transfer Progress */}
                        {transferProgress[peer.session_id] && (
                          <div className="mt-3 p-2 bg-white/5 rounded-lg">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-white/80 text-sm">
                                {transferProgress[peer.session_id].sent ? 'Sending: ' : 'Receiving: '} 
                                {transferProgress[peer.session_id].fileName}
                              </span>
                              <span className="text-white/60 text-sm">
                                {Math.round(transferProgress[peer.session_id].progress)}%
                              </span>
                            </div>
                            <div className="w-full bg-white/10 rounded-full h-2">
                              <div
                                className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${transferProgress[peer.session_id].progress}%` }}
                              ></div>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Instructions */}
            <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20">
              <h3 className="text-lg font-semibold text-white mb-3">How P2P Sharing Works</h3>
              <div className="space-y-2 text-white/80 text-sm">
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                  <span>Files are sent directly between devices</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                  <span>No file size limits or server storage</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                  <span>End-to-end encrypted connections</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                  <span>Works on the same local network</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                  <span>No registration or login required</span>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Transfer Modal */}
      {showTransferModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 max-w-md w-full mx-4"
          >
            <div className="text-center">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">Transfer Started!</h3>
              <p className="text-white/80 mb-4">
                Your file is being sent via P2P connection. The transfer will continue in the background.
              </p>
              <button
                onClick={() => setShowTransferModal(false)}
                className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 py-2 rounded-lg font-medium hover:from-blue-600 hover:to-purple-700 transition-all duration-300"
              >
                Continue
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default P2PPage;