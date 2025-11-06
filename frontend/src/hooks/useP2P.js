import { useState, useEffect, useRef, useCallback } from 'react';
import io from 'socket.io-client';
import { uniqueNamesGenerator, adjectives, colors, animals } from 'unique-names-generator';

const getPersistentDeviceName = () => {
  let name = localStorage.getItem('deviceName');
  if (!name) {
    name = uniqueNamesGenerator({
      dictionaries: [adjectives, colors, animals],
      separator: ' ',
      style: 'capital'
    });
    localStorage.setItem('deviceName', name);
  }
  return name;
};

const useP2P = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [peers, setPeers] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [transferProgress, setTransferProgress] = useState({});
  const fileChunksRef = useRef({}); // To store incoming file chunks
  const fileInfoRef = useRef({}); // To store incoming file metadata
  const [error, setError] = useState(null);

  const socketRef = useRef(null);
  const peerConnectionsRef = useRef({});
  const dataChannelsRef = useRef({});
  const deviceNameRef = useRef(getPersistentDeviceName());
  const connectPromiseResolversRef = useRef({});
 

  // WebRTC configuration
  // Using a public STUN server and a placeholder TURN server for demonstration.
  // Replace with your actual TURN server credentials.
  const rtcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
      // Placeholder for TURN server (replace with your own)
      {
      urls: 'turn:192.168.0.104:3478', 
      username: 'sharesync',
      credential: 'secretpass'
    }
    ]
  };

  // Initialize socket connection
  const initializeSocket = useCallback(() => {
    if (socketRef.current) return;

    try {
      socketRef.current = io('http://localhost:5001', {
        transports: ['websocket', 'polling']
      } );

      socketRef.current.on('connect', () => {
        console.log('Connected to signaling server');
        setConnectionStatus('connected');
        joinP2PNetwork();
      });

      socketRef.current.on('disconnect', () => {
        console.log('Disconnected from signaling server');
        setConnectionStatus('disconnected');
        setIsConnected(false);
        setPeers([]);
      });

      socketRef.current.on('p2p_joined', (data) => {
        console.log('Successfully joined P2P network:', data);
        setSessionId(data.session_id);
        setPeers(data.peers || []);
        setIsConnected(true);
        setError(null);
      });

      socketRef.current.on('peer_joined', (data) => {
        console.log('New peer joined:', data);
        setPeers(prev => [...prev.filter(p => p.session_id !== data.session_id), data]);
      });

      socketRef.current.on('peer_left', (data) => {
        console.log('Peer left:', data);
        setPeers(prev => prev.filter(p => p.session_id !== data.session_id));
        
        // Clean up peer connection
        if (peerConnectionsRef.current[data.session_id]) {
          peerConnectionsRef.current[data.session_id].close();
          delete peerConnectionsRef.current[data.session_id];
        }
        if (dataChannelsRef.current[data.session_id]) {
          delete dataChannelsRef.current[data.session_id];
        }
      });

      socketRef.current.on('webrtc_offer', async (data) => {
        console.log('Received WebRTC offer from:', data.sender_session);
        await handleWebRTCOffer(data);
      });

      socketRef.current.on('webrtc_answer', async (data) => {
        console.log('Received WebRTC answer from:', data.sender_session);
        await handleWebRTCAnswer(data);
      });

      socketRef.current.on('ice_candidate', async (data) => {
        console.log('Received ICE candidate from:', data.sender_session);
        await handleICECandidate(data);
      });

      socketRef.current.on('error', (data) => {
        console.error('Socket error:', data);
        setError(data.message);
      });

    } catch (err) {
      console.error('Failed to initialize socket:', err);
      setError('Failed to connect to signaling server');
    }
  }, []);

  // Join P2P network
  const joinP2PNetwork = useCallback(() => {
    if (!socketRef.current) return;

    socketRef.current.emit('join_p2p', {
      device_name: deviceNameRef.current,
      room_id: 'default'
    });
  }, []);

  // Helper function to trigger file download
  const downloadFile = useCallback((file, fileName) => {
    const url = URL.createObjectURL(file);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, []);

  // Handle data channel messages
  const handleDataChannelMessage = useCallback((event, senderId) => {
    // WebRTC DataChannel can send ArrayBuffer directly, so we check the type
    if (event.data instanceof ArrayBuffer) {
      // This is a file chunk
      const chunk = event.data;
      const fileInfo = fileInfoRef.current[senderId];

      if (!fileInfo) {
        console.warn('Received file chunk before file info from', senderId);
        return;
      }

      // Store the chunk
      if (!fileChunksRef.current[senderId]) {
        fileChunksRef.current[senderId] = [];
      }
      fileChunksRef.current[senderId].push(chunk);

      // Update progress
      setTransferProgress(prev => {
        const currentReceived = (prev[senderId]?.received || 0) + chunk.byteLength;
        const total = fileInfo.fileSize;
        return {
          ...prev,
          [senderId]: {
            ...prev[senderId],
            received: currentReceived,
            progress: (currentReceived / total) * 100
          }
        };
      });

      return;
    }

    // Otherwise, it's a JSON message (file info, complete, etc.)
    try {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'file_info':
          console.log('Receiving file:', data.fileName, 'size:', data.fileSize, 'from', senderId);
          fileInfoRef.current[senderId] = data;
          fileChunksRef.current[senderId] = []; // Clear any previous chunks
          setTransferProgress(prev => ({
            ...prev,
            [senderId]: {
              fileName: data.fileName,
              total: data.fileSize,
              received: 0,
              progress: 0
            }
          }));
          break;
          
        case 'file_complete':
          console.log('File transfer complete from', senderId, '. Reassembling file...');
          
          const info = fileInfoRef.current[senderId];
          const chunks = fileChunksRef.current[senderId];

          if (info && chunks) {
            // Reassemble the file
            const file = new Blob(chunks, { type: info.fileType });
            
            // Trigger download
            downloadFile(file, info.fileName);

            // Clean up
            delete fileInfoRef.current[senderId];
            delete fileChunksRef.current[senderId];
            setTransferProgress(prev => {
              const newProgress = { ...prev };
              delete newProgress[senderId];
              return newProgress;
            });

          } else {
            console.error('Missing file info or chunks for completion from', senderId);
          }
          break;
          
        default:
          console.log('Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('Failed to handle data channel message:', error);
    }
  }, [downloadFile]);

  // Create peer connection
  // ADDED isInitiator flag
  const createPeerConnection = useCallback((targetSessionId, isInitiator = false) => {
    try {
      const peerConnection = new RTCPeerConnection(rtcConfig);
      
      // Handle ICE candidates
      peerConnection.onicecandidate = (event) => {
        if (event.candidate && socketRef.current) {
          socketRef.current.emit('ice_candidate', {
            target_session: targetSessionId,
            sender_session: sessionId,
            candidate: event.candidate
          });
        }
      };

      // Handle connection state changes
      peerConnection.onconnectionstatechange = () => {
        console.log(`Connection state with ${targetSessionId}:`, peerConnection.connectionState);
        
        if (peerConnection.connectionState === 'connected') {
          setPeers(prev => prev.map(peer => 
            peer.session_id === targetSessionId 
              ? { ...peer, connectionState: 'connected' }
              : peer
          ));
        }
      };

      // ADDED if(isInitiator) block
      if (isInitiator) {
        // Create data channel for file transfer
        const dataChannel = peerConnection.createDataChannel('fileTransfer', {
          ordered: true
        });

        dataChannel.onopen = () => {
          console.log(`Data channel opened with ${targetSessionId}`);
          dataChannelsRef.current[targetSessionId] = dataChannel;
          setPeers(prev => prev.map(p => 
            p.session_id === targetSessionId ? { ...p, dataChannelReady: true } : p
          ));
          // Resolve the connect promise if it exists
          if (connectPromiseResolversRef.current[targetSessionId]) {
            connectPromiseResolversRef.current[targetSessionId](true);
            delete connectPromiseResolversRef.current[targetSessionId];
          }
        };

        dataChannel.onmessage = (event) => {
          handleDataChannelMessage(event, targetSessionId);
        };

        dataChannel.onerror = (error) => {
          console.error(`Data channel error with ${targetSessionId}:`, error);
        };
      }

      // Handle incoming data channels
      peerConnection.ondatachannel = (event) => {
        const channel = event.channel;
        channel.onmessage = (event) => {
          handleDataChannelMessage(event, targetSessionId);
        };
        // This handles the *other* person's channel opening
        channel.onopen = () => {
          console.log(`Incoming data channel opened from ${targetSessionId}`);
          setPeers(prev => prev.map(p => 
            p.session_id === targetSessionId ? { ...p, dataChannelReady: true } : p
          ));
          // ADDED promise resolver for receiver
          if (connectPromiseResolversRef.current[targetSessionId]) {
            connectPromiseResolversRef.current[targetSessionId](true);
            delete connectPromiseResolversRef.current[targetSessionId];
          }
        };
        
        dataChannelsRef.current[targetSessionId] = channel;
      };

      peerConnectionsRef.current[targetSessionId] = peerConnection;
      return peerConnection;

    } catch (error) {
      console.error('Failed to create peer connection:', error);
      setError('Failed to create peer connection');
      return null;
    }
  // UPDATED dependency array
  }, [sessionId, setPeers, handleDataChannelMessage]);

  // Handle WebRTC offer
  const handleWebRTCOffer = useCallback(async (data) => {
    try {
      // ADDED false flag
      const peerConnection = createPeerConnection(data.sender_session, false);
      if (!peerConnection) return;

      await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
      const answer = await peerConnection.createAnswer();
      await peerConnection.setLocalDescription(answer);

      if (socketRef.current) {
        socketRef.current.emit('webrtc_answer', {
          target_session: data.sender_session,
          sender_session: sessionId,
          answer: answer
        });
      }
    } catch (error) {
      console.error('Failed to handle WebRTC offer:', error);
      setError('Failed to handle connection offer');
    }
  }, [createPeerConnection, sessionId]);

  // Handle WebRTC answer
  const handleWebRTCAnswer = useCallback(async (data) => {
    try {
      const peerConnection = peerConnectionsRef.current[data.sender_session];
      if (peerConnection) {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
      }
    } catch (error) {
      console.error('Failed to handle WebRTC answer:', error);
      setError('Failed to handle connection answer');
    }
  }, []);

  // Handle ICE candidate
  const handleICECandidate = useCallback(async (data) => {
    try {
      const peerConnection = peerConnectionsRef.current[data.sender_session];
      if (peerConnection) {
        await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
      }
    } catch (error) {
      console.error('Failed to handle ICE candidate:', error);
    }
  }, []);

  // Connect to a specific peer
  // Connect to a specific peer
  const connectToPeer = useCallback(async (targetSessionId) => {
    return new Promise(async (resolve, reject) => {
      try {
        // 1. If channel is already open, resolve immediately
        const existingChannel = dataChannelsRef.current[targetSessionId];
        if (existingChannel && existingChannel.readyState === 'open') {
          console.log('Data channel already open.');
          resolve(true);
          return;
        }

        // 2. Store the resolver function to be called later (in 'onopen')
        // This will be called by EITHER the outgoing or incoming 'onopen' handler
        connectPromiseResolversRef.current[targetSessionId] = resolve;
        
        // 3. Check if a connection *object* already exists
        if (peerConnectionsRef.current[targetSessionId]) {
          // A connection object exists. This means a connection is already
          // in progress (either we started it or they did).
          // We don't need to do anything else. The 'onopen'
          // handler for that connection will find our resolver and call it.
          console.log('Connection already in progress, waiting for data channel...');
          return;
        }

        // 4. No connection exists. Create a new one as the initiator.
        console.log('Creating new connection as initiator');
        const peerConnection = createPeerConnection(targetSessionId, true); // We are the initiator
        if (!peerConnection) {
          reject('Failed to create peer connection');
          return;
        }

        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);

        if (socketRef.current) {
          socketRef.current.emit('webrtc_offer', {
            target_session: targetSessionId,
            sender_session: sessionId,
            offer: offer
          });
        }
      } catch (error) {
        console.error('Failed to connect to peer:', error);
        setError('Failed to connect to peer');
        reject(error);
      }
    });
    
  }, [createPeerConnection, sessionId]);

 
  // Send file to peer
  const sendFileToPeer = useCallback(async (targetSessionId, file) => {
    try {
      const dataChannel = dataChannelsRef.current[targetSessionId];
      if (!dataChannel || dataChannel.readyState !== 'open') {
        throw new Error('Data channel not ready');
      }

      // Send file info first
      const fileInfo = {
        type: 'file_info',
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type
      };
      
      dataChannel.send(JSON.stringify(fileInfo));

      // Initialize progress tracking
      setTransferProgress(prev => ({
        ...prev,
        [targetSessionId]: {
          fileName: file.name,
          total: file.size,
          sent: 0,
          progress: 0
        }
      }));

      // Send file in chunks
      const chunkSize = 16384; // 16KB chunks
      const reader = new FileReader();
      let offset = 0;

      const sendNextChunk = () => {
        const slice = file.slice(offset, offset + chunkSize);
        reader.readAsArrayBuffer(slice);
      };

      reader.onload = (event) => {
        const chunk = event.target.result;
        
        // Send the raw ArrayBuffer directly, which is more efficient and reliable
        dataChannel.send(chunk);
        
        offset += chunk.byteLength;
        
        // Update progress
        setTransferProgress(prev => ({
          ...prev,
          [targetSessionId]: {
            ...prev[targetSessionId],
            sent: offset,
            progress: (offset / file.size) * 100
          }
        }));

        if (offset < file.size) {
          sendNextChunk();
        } else {
          // Send completion message
          dataChannel.send(JSON.stringify({ type: 'file_complete' }));
          console.log('File transfer complete to', targetSessionId);
        }
      };

      reader.onerror = (error) => {
        console.error('File reading error:', error);
        setError('Failed to read file');
      };

      sendNextChunk();
      return true;

    } catch (error) {
      console.error('Failed to send file:', error);
      setError('Failed to send file');
      return false;
    }
  }, []);

  // Disconnect from P2P network
  const disconnect = useCallback(() => {
    // Close all peer connections
    Object.values(peerConnectionsRef.current).forEach(pc => pc.close());
    peerConnectionsRef.current = {};
    dataChannelsRef.current = {};

    // Disconnect socket
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }

    setIsConnected(false);
    setPeers([]);
    setSessionId(null);
    setConnectionStatus('disconnected');
    setTransferProgress({});
    setError(null);
  }, []);

  // Initialize on mount
  useEffect(() => {
    initializeSocket();
    
    return () => {
      disconnect();
    };
  }, [initializeSocket, disconnect]);

  return {
    isConnected,
    peers,
    sessionId,
    connectionStatus,
    transferProgress,
    error,
    connectToPeer,
    sendFileToPeer,
    disconnect,
    deviceName: deviceNameRef.current
  };
};

export default useP2P;
