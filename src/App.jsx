/**
 * Consensus Gallery - Main App Component
 * Full DApp with GenLayerJS SDK integration
 */

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import * as genLayer from './genLayerClient';
import { 
  CONFIG, ART_COLLECTION, PHASE_LABELS, PHASE_COLORS, STORAGE_KEY,
  generatePlayerId, getArt, getRandomArt, formatTime, formatDate, shortenAddress 
} from './constants';

// ==================== Components ====================

const Spinner = () => (
  <div className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
);

const ArtDisplay = ({ artId, size = 280, showLabel = true }) => {
  const art = getArt(artId);
  const [loaded, setLoaded] = useState(false);
  const isSmall = size <= 80;
  
  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      {!loaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/5 rounded-xl">
          <div className="text-gray-500 text-xs">...</div>
        </div>
      )}
      <img 
        src={art.url} 
        alt={art.name}
        onLoad={() => setLoaded(true)}
        className={`w-full h-full object-cover rounded-xl shadow-xl transition-opacity ${loaded ? 'opacity-100' : 'opacity-0'}`}
      />
      {showLabel && !isSmall && (
        <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/80 to-transparent rounded-b-xl">
          <div className="text-sm font-medium text-white truncate">{art.name}</div>
          <div className="text-xs text-gray-300 truncate">{art.artist}, {art.year}</div>
        </div>
      )}
    </div>
  );
};

// ==================== Main App ====================

export default function App() {
  // State
  const [wallet, setWallet] = useState({ connected: false, address: '', initialized: false });
  const [globalState, setGlobalState] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || createInitialState();
    } catch {
      return createInitialState();
    }
  });
  const [activeTab, setActiveTab] = useState('lobby');
  const [currentRoomId, setCurrentRoomId] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [processing, setProcessing] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);
  const [txStatus, setTxStatus] = useState('');
  
  const globalStateRef = useRef(globalState);
  globalStateRef.current = globalState;
  const currentRoomIdRef = useRef(currentRoomId);
  currentRoomIdRef.current = currentRoomId;
  const chatEndRef = useRef(null);

  const currentRoom = currentRoomId ? globalState.rooms[currentRoomId] : null;

  function createInitialState() {
    return { rooms: {}, leaderboard: {}, history: [], totalGames: 0, playerIds: {} };
  }

  const getPlayerId = useCallback((address) => {
    if (!address) return '';
    if (globalState.playerIds[address]) return globalState.playerIds[address];
    const newId = generatePlayerId(address);
    setGlobalState(prev => ({ ...prev, playerIds: { ...prev.playerIds, [address]: newId } }));
    return newId;
  }, [globalState.playerIds]);

  // ==================== Storage Sync ====================
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(globalState));
  }, [globalState]);

  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        try { setGlobalState(JSON.parse(e.newValue)); } catch {}
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  // ==================== Game Timer ====================
  useEffect(() => {
    const timer = setInterval(() => {
      const state = globalStateRef.current;
      const now = Date.now();
      
      // Clean up expired rooms
      Object.entries(state.rooms).forEach(([roomId, room]) => {
        if (room.phase === 'waiting' && now - room.createdAt > CONFIG.ROOM_TIMEOUT) {
          setGlobalState(prev => {
            const newRooms = { ...prev.rooms };
            delete newRooms[roomId];
            return { ...prev, rooms: newRooms };
          });
          if (currentRoomIdRef.current === roomId) {
            setCurrentRoomId(null);
            setActiveTab('lobby');
            setError('Room expired');
          }
        }
      });

      const roomId = currentRoomIdRef.current;
      if (!roomId) return;
      
      const room = state.rooms[roomId];
      if (!room || room.phase === 'finished' || room.phase === 'waiting') {
        setTimeLeft(0);
        return;
      }
      
      const elapsed = Math.floor((now - room.startTime) / 1000);
      const remaining = room.phase === 'voting' 
        ? Math.max(0, Math.floor((room.voteDeadline - now) / 1000))
        : CONFIG.MAX_GAME_DURATION - elapsed;
      
      setTimeLeft(Math.max(0, remaining));

      if (room.phase === 'playing' && elapsed >= CONFIG.MAX_GAME_DURATION) {
        handleStartVoting(roomId);
      } else if (room.phase === 'voting' && remaining <= 0) {
        handleFinalizeGame(roomId);
      }
    }, 1000);
    
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (chatEndRef.current) chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
  }, [currentRoom?.messages?.length]);

  // ==================== Wallet & GenLayer ====================
  const connectWallet = async () => {
    setProcessing(true);
    setError('');
    setTxStatus('Initializing GenLayer...');
    
    try {
      const envPrivateKey = import.meta.env.VITE_PRIVATE_KEY;
      const result = await genLayer.initClient(envPrivateKey || null);
      
      if (result.success) {
        setWallet({ connected: true, address: result.address, initialized: true });
        getPlayerId(result.address);
        setSuccess(`Connected! ${shortenAddress(result.address)}`);
        setTxStatus('');
      } else {
        setError(`Connection failed: ${result.error}`);
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    }
    
    setProcessing(false);
    setTimeout(() => setSuccess(''), 3000);
  };

  const switchAccount = async () => {
    setProcessing(true);
    const envPrivateKey = import.meta.env.VITE_PRIVATE_KEY;
    const result = await genLayer.initClient(envPrivateKey || null);
    if (result.success) {
      setWallet({ connected: true, address: result.address, initialized: true });
      getPlayerId(result.address);
      setSuccess(`Switched to ${shortenAddress(result.address)}`);
    }
    setProcessing(false);
    setTimeout(() => setSuccess(''), 3000);
  };

  // ==================== Room Operations ====================
  const handleCreateRoom = useCallback(async () => {
    if (!wallet.connected || processing) return;
    
    setProcessing(true);
    setError('');
    setTxStatus('Creating room on chain...');
    
    try {
      const result = await genLayer.createRoom();
      
      if (result.success) {
        const art = getRandomArt();
        const roomId = result.roomId || `room_${Date.now()}`;
        
        const room = {
          id: roomId,
          gameNumber: globalState.totalGames + 1,
          creator: wallet.address,
          phase: 'waiting',
          artId: art.id,
          artName: art.name,
          maxPlayers: CONFIG.MAX_PLAYERS,
          players: [wallet.address],
          messages: [],
          votes: {},
          endGameVotes: [],
          winner: null,
          createdAt: Date.now(),
          startTime: null,
          voteDeadline: null,
          locked: false,
          onChain: true,
          txHash: result.hash,
        };

        setGlobalState(prev => ({
          ...prev,
          rooms: { ...prev.rooms, [roomId]: room },
          totalGames: prev.totalGames + 1,
        }));
        setCurrentRoomId(roomId);
        setActiveTab('game');
        setSuccess(`Room created! TX: ${shortenAddress(result.hash)}`);
      } else {
        setError(`Failed: ${result.error}`);
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    }
    
    setTxStatus('');
    setProcessing(false);
    setTimeout(() => setSuccess(''), 4000);
  }, [wallet, processing, globalState.totalGames]);

  const handleCreateRoomLocal = useCallback(() => {
    if (!wallet.connected) return;
    
    const art = getRandomArt();
    const roomId = 'local_' + Date.now();
    const room = {
      id: roomId,
      gameNumber: globalState.totalGames + 1,
      creator: wallet.address,
      phase: 'waiting',
      artId: art.id,
      artName: art.name,
      maxPlayers: CONFIG.MAX_PLAYERS,
      players: [wallet.address],
      messages: [],
      votes: {},
      endGameVotes: [],
      winner: null,
      createdAt: Date.now(),
      startTime: null,
      voteDeadline: null,
      locked: false,
      onChain: false,
    };

    setGlobalState(prev => ({
      ...prev,
      rooms: { ...prev.rooms, [roomId]: room },
      totalGames: prev.totalGames + 1,
    }));
    setCurrentRoomId(roomId);
    setActiveTab('game');
  }, [wallet, globalState.totalGames]);

  const handleJoinRoom = useCallback(async (roomId) => {
    if (!wallet.connected || processing) return;
    
    const room = globalState.rooms[roomId];
    if (!room || room.phase !== 'waiting' || room.locked) {
      setError('Room unavailable');
      return;
    }
    if (room.players.length >= room.maxPlayers) {
      setError('Room is full');
      return;
    }
    if (room.players.includes(wallet.address)) {
      setCurrentRoomId(roomId);
      setActiveTab('game');
      return;
    }

    setProcessing(true);
    
    if (room.onChain) {
      setTxStatus('Joining room on chain...');
      const result = await genLayer.joinRoom(roomId);
      if (!result.success) {
        setError(`Join failed: ${result.error}`);
        setProcessing(false);
        setTxStatus('');
        return;
      }
    }

    setGlobalState(prev => ({
      ...prev,
      rooms: {
        ...prev.rooms,
        [roomId]: { ...prev.rooms[roomId], players: [...prev.rooms[roomId].players, wallet.address] }
      }
    }));
    setCurrentRoomId(roomId);
    setActiveTab('game');
    setTxStatus('');
    setProcessing(false);
  }, [wallet, processing, globalState.rooms]);

  const handleStartGame = useCallback(async (roomId) => {
    const room = globalState.rooms[roomId];
    if (!room || room.phase !== 'waiting' || room.players.length < CONFIG.MIN_PLAYERS) return;
    
    if (room.onChain) {
      setProcessing(true);
      setTxStatus('Starting game on chain...');
      const result = await genLayer.startGame(roomId);
      setTxStatus('');
      setProcessing(false);
      if (!result.success) {
        setError(`Start failed: ${result.error}`);
        return;
      }
    }

    setGlobalState(prev => ({
      ...prev,
      rooms: {
        ...prev.rooms,
        [roomId]: { ...prev.rooms[roomId], phase: 'playing', locked: true, startTime: Date.now() }
      }
    }));
  }, [globalState.rooms]);

  const handleSendMessage = useCallback(async () => {
    if (!wallet.connected || !currentRoomId || !message.trim()) return;
    
    const room = globalState.rooms[currentRoomId];
    if (!room || room.phase !== 'playing') return;

    const msgContent = message.trim();
    setMessage('');

    if (room.onChain) {
      setTxStatus('Sending message...');
      const result = await genLayer.sendMessage(currentRoomId, msgContent);
      setTxStatus('');
      if (!result.success) {
        setError(`Send failed: ${result.error}`);
        return;
      }
    }

    const newMessage = { id: Date.now(), author: wallet.address, content: msgContent, timestamp: Date.now() };
    const newLeaderboard = { ...globalState.leaderboard };
    if (!newLeaderboard[wallet.address]) {
      newLeaderboard[wallet.address] = { experience: 0, wins: 0, participations: 0 };
    }
    const hasMessaged = room.messages.some(m => m.author === wallet.address);
    if (!hasMessaged) newLeaderboard[wallet.address].participations++;

    setGlobalState(prev => ({
      ...prev,
      leaderboard: newLeaderboard,
      rooms: { ...prev.rooms, [currentRoomId]: { ...room, messages: [...room.messages, newMessage] } }
    }));
  }, [wallet, currentRoomId, message, globalState]);

  const handleVoteEndGame = useCallback(async () => {
    if (!wallet.connected || !currentRoomId) return;
    
    const room = globalState.rooms[currentRoomId];
    if (!room || room.phase !== 'playing') return;
    
    const elapsed = (Date.now() - room.startTime) / 1000;
    if (elapsed < CONFIG.MIN_GAME_DURATION) return;
    if (room.endGameVotes.includes(wallet.address)) return;

    if (room.onChain) {
      setTxStatus('Voting to end...');
      const result = await genLayer.voteEndGame(currentRoomId);
      setTxStatus('');
      if (!result.success) {
        setError(`Vote failed: ${result.error}`);
        return;
      }
    }
    
    const newEndGameVotes = [...room.endGameVotes, wallet.address];
    const threshold = Math.ceil(room.players.length / 2);
    const shouldEnd = newEndGameVotes.length >= threshold;
    
    setGlobalState(prev => ({
      ...prev,
      rooms: {
        ...prev.rooms,
        [currentRoomId]: {
          ...room,
          endGameVotes: newEndGameVotes,
          ...(shouldEnd ? { phase: 'voting', voteDeadline: Date.now() + CONFIG.VOTE_DURATION * 1000 } : {})
        }
      }
    }));
  }, [wallet, currentRoomId, globalState]);

  const handleStartVoting = useCallback((roomId) => {
    setGlobalState(prev => {
      const room = prev.rooms[roomId];
      if (!room || room.phase !== 'playing') return prev;
      return {
        ...prev,
        rooms: { ...prev.rooms, [roomId]: { ...room, phase: 'voting', voteDeadline: Date.now() + CONFIG.VOTE_DURATION * 1000 } }
      };
    });
  }, []);

  const handleVote = useCallback(async (targetAddress) => {
    if (!wallet.connected || !currentRoomId) return;
    
    const room = globalState.rooms[currentRoomId];
    if (!room || room.phase !== 'voting') return;
    if (room.votes[wallet.address]) {
      setError('Already voted');
      return;
    }

    if (room.onChain) {
      setTxStatus('Submitting vote...');
      const result = await genLayer.vote(currentRoomId, targetAddress);
      setTxStatus('');
      if (!result.success) {
        setError(`Vote failed: ${result.error}`);
        return;
      }
    }

    const newVotes = { ...room.votes, [wallet.address]: targetAddress };
    const voters = room.messages.map(m => m.author).filter((v, i, a) => a.indexOf(v) === i);
    const allVoted = voters.every(p => newVotes[p]);
    
    if (allVoted) {
      setGlobalState(prev => finalizeGameState(prev, currentRoomId, newVotes));
    } else {
      setGlobalState(prev => ({
        ...prev,
        rooms: { ...prev.rooms, [currentRoomId]: { ...room, votes: newVotes } }
      }));
    }
  }, [wallet, currentRoomId, globalState]);

  const handleFinalizeGame = useCallback((roomId) => {
    setGlobalState(prev => {
      const room = prev.rooms[roomId];
      if (!room || room.phase === 'finished') return prev;
      return finalizeGameState(prev, roomId, room.votes || {});
    });
  }, []);

  const finalizeGameState = (prevState, roomId, votes) => {
    const room = prevState.rooms[roomId];
    if (!room || room.phase === 'finished') return prevState;

    const authors = room.messages.map(m => m.author).filter((v, i, a) => a.indexOf(v) === i);
    if (authors.length === 0) {
      const newRooms = { ...prevState.rooms };
      delete newRooms[roomId];
      return { ...prevState, rooms: newRooms };
    }

    const voteCount = {};
    authors.forEach(addr => { voteCount[addr] = 0; });
    Object.values(votes).forEach(target => {
      if (voteCount[target] !== undefined) voteCount[target]++;
    });

    const maxVotes = Math.max(...Object.values(voteCount), 0);
    const winners = authors.filter(addr => voteCount[addr] === maxVotes);
    const winnerAddress = winners[Math.floor(Math.random() * winners.length)];

    const newLeaderboard = JSON.parse(JSON.stringify(prevState.leaderboard));
    
    if (!newLeaderboard[winnerAddress]) {
      newLeaderboard[winnerAddress] = { experience: 0, wins: 0, participations: 0 };
    }
    newLeaderboard[winnerAddress].experience += CONFIG.WINNER_EXP;
    newLeaderboard[winnerAddress].wins += 1;

    Object.entries(votes).forEach(([voter, target]) => {
      if (!newLeaderboard[voter]) {
        newLeaderboard[voter] = { experience: 0, wins: 0, participations: 0 };
      }
      newLeaderboard[voter].experience += target === winnerAddress ? CONFIG.CORRECT_VOTER_EXP : CONFIG.PARTICIPANT_EXP;
    });

    const historyEntry = {
      id: roomId,
      gameNumber: room.gameNumber,
      artId: room.artId,
      artName: room.artName,
      winner: winnerAddress,
      winnerVotes: voteCount[winnerAddress] || 0,
      participants: authors.map(addr => ({
        address: addr,
        playerId: prevState.playerIds[addr] || generatePlayerId(addr),
        messageCount: room.messages.filter(m => m.author === addr).length,
        votes: voteCount[addr] || 0,
        isWinner: addr === winnerAddress,
        earnedXP: addr === winnerAddress ? CONFIG.WINNER_EXP : (votes[addr] === winnerAddress ? CONFIG.CORRECT_VOTER_EXP : CONFIG.PARTICIPANT_EXP)
      })),
      totalPlayers: room.players.length,
      duration: Math.floor((Date.now() - room.startTime) / 1000),
      timestamp: Date.now(),
      onChain: room.onChain,
    };

    return {
      ...prevState,
      leaderboard: newLeaderboard,
      history: [historyEntry, ...prevState.history].slice(0, 100),
      rooms: { ...prevState.rooms, [roomId]: { ...room, phase: 'finished', votes, winner: winnerAddress, voteCount } }
    };
  };

  const handleLeaveRoom = useCallback(() => {
    setCurrentRoomId(null);
    setActiveTab('lobby');
    setMessage('');
  }, []);

  // ==================== Computed Values ====================
  const availableRooms = useMemo(() => 
    Object.values(globalState.rooms).filter(r => r.phase === 'waiting' && !r.locked && r.players.length < r.maxPlayers),
    [globalState.rooms]);

  const myRooms = useMemo(() => 
    Object.values(globalState.rooms).filter(r => wallet.connected && r.players.includes(wallet.address) && r.phase !== 'finished'),
    [globalState.rooms, wallet]);

  const sortedLeaderboard = useMemo(() => 
    Object.entries(globalState.leaderboard)
      .map(([address, stats]) => ({ address, playerId: globalState.playerIds[address] || generatePlayerId(address), ...stats }))
      .filter(p => p.participations > 0 || p.experience > 0)
      .sort((a, b) => b.experience - a.experience),
    [globalState.leaderboard, globalState.playerIds]);

  const myHistory = useMemo(() => 
    wallet.connected ? globalState.history.filter(h => h.participants?.some(p => p.address === wallet.address)) : [],
    [globalState.history, wallet]);

  const gameElapsed = currentRoom?.startTime ? Math.floor((Date.now() - currentRoom.startTime) / 1000) : 0;
  const canVoteEnd = currentRoom?.phase === 'playing' && gameElapsed >= CONFIG.MIN_GAME_DURATION;
  const endVoteProgress = currentRoom ? `${currentRoom.endGameVotes?.length || 0}/${Math.ceil(currentRoom.players.length / 2)}` : '';

  const myPlayerId = wallet.connected ? (globalState.playerIds[wallet.address] || generatePlayerId(wallet.address)) : '';
  const myXP = wallet.connected ? (globalState.leaderboard[wallet.address]?.experience || 0) : 0;

  // ==================== Render ====================
  return (
    <div className="min-h-screen text-gray-200">
      {/* Header */}
      <header className="flex justify-between items-center px-4 md:px-6 py-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl btn-primary">🎨</div>
          <div>
            <h1 className="text-lg md:text-xl font-bold gradient-text">Consensus Gallery</h1>
            <p className="text-xs text-gray-500 hidden sm:block">GenLayer DApp • {genLayer.getNetwork()}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {wallet.connected ? (
            <>
              <div className="flex flex-col items-end gap-1 px-3 py-2 glass rounded-xl">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full" style={{ boxShadow: '0 0 8px #10B981' }}></div>
                  <span className="text-xs md:text-sm font-medium">{myPlayerId}</span>
                  <span className="px-2 py-0.5 bg-primary-500/30 rounded text-xs font-bold text-primary-300">{myXP} XP</span>
                </div>
                <span className="text-[10px] text-gray-500 font-mono">{shortenAddress(wallet.address)}</span>
              </div>
              <button onClick={switchAccount} disabled={processing} className="px-2 py-2 text-xs text-gray-400 hover:text-white rounded-lg hover:bg-white/5">
                {processing ? <Spinner /> : '🔄'}
              </button>
            </>
          ) : (
            <button onClick={connectWallet} disabled={processing} className="btn-primary px-4 py-2 rounded-xl text-white text-sm font-semibold flex items-center gap-2">
              {processing ? <><Spinner /> Connecting...</> : 'Connect'}
            </button>
          )}
        </div>
      </header>

      {/* Notifications */}
      {error && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-3 bg-red-500/90 text-white rounded-lg shadow-lg animate-fade-in flex items-center gap-3">
          <span>{error}</span>
          <button onClick={() => setError('')} className="text-white/80 hover:text-white">✕</button>
        </div>
      )}
      
      {success && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-3 bg-green-500/90 text-white rounded-lg shadow-lg animate-fade-in">
          ✓ {success}
        </div>
      )}

      {txStatus && (
        <div className="fixed top-32 left-1/2 -translate-x-1/2 z-50 px-4 py-3 bg-primary-500/90 text-white rounded-lg shadow-lg animate-fade-in flex items-center gap-2">
          <Spinner /> {txStatus}
        </div>
      )}

      {/* Navigation */}
      <nav className="flex gap-1 px-4 md:px-6 py-3 border-b border-white/5 overflow-x-auto">
        {[
          { id: 'lobby', icon: '🏠', label: 'Lobby' },
          { id: 'game', icon: '🎮', label: 'Game', badge: myRooms.length > 0 ? myRooms.length : null },
          { id: 'leaderboard', icon: '🏆', label: 'Leaderboard' },
          { id: 'history', icon: '📜', label: 'History' },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === tab.id ? 'bg-primary-500/20 border border-primary-500/50 text-primary-300' : 'text-gray-400 hover:bg-white/5'
            }`}>
            <span>{tab.icon}</span>
            <span className="hidden sm:inline">{tab.label}</span>
            {tab.badge && <span className="px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">{tab.badge}</span>}
          </button>
        ))}
      </nav>

      {/* Main Content */}
      <main className="px-4 md:px-6 py-6 max-w-6xl mx-auto">
        
        {/* Lobby */}
        {activeTab === 'lobby' && (
          <div className="space-y-6 animate-fade-in">
            <div className="text-center py-6">
              <h2 className="text-2xl md:text-3xl font-bold gradient-text mb-2">Consensus Gallery</h2>
              <p className="text-gray-400">On-Chain Art Description Game</p>
            </div>

            {!wallet.connected ? (
              <div className="glass rounded-2xl p-8 text-center">
                <div className="text-5xl mb-4">🔗</div>
                <p className="text-gray-400 mb-4">Connect to GenLayer to play</p>
                <button onClick={connectWallet} disabled={processing} className="btn-primary px-6 py-3 rounded-xl text-white font-semibold flex items-center gap-2 mx-auto">
                  {processing ? <><Spinner /> Connecting...</> : 'Connect Wallet'}
                </button>
              </div>
            ) : (
              <>
                <div className="glass rounded-2xl p-6">
                  <h3 className="text-lg font-semibold mb-4">🎮 Create Game</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <button onClick={handleCreateRoom} disabled={processing}
                      className="btn-primary py-4 rounded-xl text-white font-semibold disabled:opacity-50 flex items-center justify-center gap-2">
                      {processing ? <><Spinner /> Creating...</> : '⛓️ On-Chain'}
                    </button>
                    <button onClick={handleCreateRoomLocal} disabled={processing}
                      className="py-4 rounded-xl text-white font-semibold bg-white/10 hover:bg-white/20 disabled:opacity-50">
                      💾 Local Test
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-3 text-center">On-Chain requires GEN • Local is instant</p>
                </div>

                <div className="glass rounded-2xl p-6">
                  <h3 className="text-lg font-semibold mb-4">🚪 Available Rooms ({availableRooms.length})</h3>
                  {availableRooms.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">No rooms available</div>
                  ) : (
                    <div className="space-y-3">
                      {availableRooms.map(room => (
                        <div key={room.id} className="flex items-center justify-between p-4 bg-white/5 rounded-xl hover:bg-white/10 transition">
                          <div className="flex items-center gap-4">
                            <ArtDisplay artId={room.artId} size={60} />
                            <div>
                              <div className="font-medium flex items-center gap-2">
                                {room.artName}
                                {room.onChain && <span className="text-xs px-1 py-0.5 bg-green-500/20 text-green-400 rounded">⛓️</span>}
                              </div>
                              <div className="text-sm text-gray-400">👥 {room.players.length}/{room.maxPlayers}</div>
                            </div>
                          </div>
                          <button onClick={() => handleJoinRoom(room.id)} disabled={processing}
                            className="btn-success px-4 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-50">
                            {processing ? <Spinner /> : 'Join'}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {myRooms.length > 0 && (
                  <div className="glass rounded-2xl p-6 border-primary-500/30">
                    <h3 className="text-lg font-semibold mb-4 text-primary-300">⏳ My Games</h3>
                    <div className="space-y-3">
                      {myRooms.map(room => (
                        <div key={room.id} className="flex items-center justify-between p-4 bg-primary-500/10 rounded-xl">
                          <div className="flex items-center gap-4">
                            <ArtDisplay artId={room.artId} size={50} />
                            <div>
                              <div className="font-medium text-sm">{room.artName}</div>
                              <div className="text-xs text-gray-400">{PHASE_LABELS[room.phase]} • 👥 {room.players.length}</div>
                            </div>
                          </div>
                          <button onClick={() => { setCurrentRoomId(room.id); setActiveTab('game'); }}
                            className="btn-warning px-4 py-2 rounded-lg text-white text-sm font-medium">Enter</button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            <div className="grid grid-cols-3 gap-4">
              {[
                { label: 'Games', value: globalState.totalGames, icon: '🎮' },
                { label: 'Players', value: Object.keys(globalState.leaderboard).length, icon: '👥' },
                { label: 'Active', value: Object.values(globalState.rooms).filter(r => r.phase !== 'finished').length, icon: '⏳' },
              ].map((stat, i) => (
                <div key={i} className="glass rounded-xl p-4 text-center">
                  <div className="text-2xl mb-1">{stat.icon}</div>
                  <div className="text-2xl font-bold">{stat.value}</div>
                  <div className="text-xs text-gray-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Game Room */}
        {activeTab === 'game' && (
          <div className="animate-fade-in">
            {!currentRoom ? (
              <div className="glass rounded-2xl p-8 text-center">
                <p className="text-gray-400 mb-4">No active game</p>
                <button onClick={() => setActiveTab('lobby')} className="btn-primary px-6 py-3 rounded-xl text-white font-semibold">Go to Lobby</button>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column */}
                <div className="space-y-4">
                  <div className="glass rounded-xl p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="px-3 py-1 rounded-full text-sm font-semibold flex items-center gap-2" 
                          style={{ background: PHASE_COLORS[currentRoom.phase] + '20', color: PHASE_COLORS[currentRoom.phase] }}>
                          <span className="w-2 h-2 rounded-full pulse-dot" style={{ background: PHASE_COLORS[currentRoom.phase] }}></span>
                          {PHASE_LABELS[currentRoom.phase]}
                        </span>
                        {currentRoom.onChain && <span className="text-xs px-2 py-0.5 bg-green-500/20 text-green-400 rounded">⛓️ On-Chain</span>}
                      </div>
                      {(currentRoom.phase === 'playing' || currentRoom.phase === 'voting') && (
                        <div className={`px-3 py-1.5 rounded-lg ${timeLeft <= 30 ? 'bg-red-500/20 text-red-400' : 'bg-white/5'}`}>
                          <span className="text-xl font-bold font-mono">{formatTime(timeLeft)}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="glass rounded-xl p-6 text-center">
                    <ArtDisplay artId={currentRoom.artId} size={300} />
                    
                    {currentRoom.phase === 'waiting' && (
                      <div className="mt-4 p-3 bg-white/5 rounded-lg">
                        <div className="text-sm text-gray-400 mb-2">Players ({currentRoom.players.length}/{currentRoom.maxPlayers})</div>
                        <div className="flex flex-wrap gap-2 justify-center">
                          {currentRoom.players.map(addr => (
                            <span key={addr} className={`px-2 py-1 rounded text-xs ${addr === wallet.address ? 'bg-primary-500/30 text-primary-300' : 'bg-white/10'}`}>
                              {globalState.playerIds[addr] || generatePlayerId(addr)}
                            </span>
                          ))}
                        </div>
                        {currentRoom.creator === wallet.address && currentRoom.players.length >= CONFIG.MIN_PLAYERS && (
                          <button onClick={() => handleStartGame(currentRoomId)} disabled={processing}
                            className="btn-success w-full mt-4 py-3 rounded-lg text-white font-semibold disabled:opacity-50">
                            {processing ? <Spinner /> : '🚀 Start'}
                          </button>
                        )}
                        {currentRoom.players.length < CONFIG.MIN_PLAYERS && (
                          <p className="text-sm text-yellow-500 mt-3">Need {CONFIG.MIN_PLAYERS - currentRoom.players.length} more</p>
                        )}
                      </div>
                    )}

                    {currentRoom.phase === 'playing' && canVoteEnd && (
                      <div className="mt-4 p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                        <button onClick={handleVoteEndGame}
                          disabled={currentRoom.endGameVotes?.includes(wallet.address) || processing}
                          className={`w-full py-2 rounded-lg font-medium ${currentRoom.endGameVotes?.includes(wallet.address) ? 'bg-white/10 text-gray-500' : 'btn-warning text-white'}`}>
                          {currentRoom.endGameVotes?.includes(wallet.address) ? `✓ Voted (${endVoteProgress})` : `Vote End (${endVoteProgress})`}
                        </button>
                      </div>
                    )}
                  </div>

                  {currentRoom.phase === 'finished' && currentRoom.winner && (
                    <div className="rounded-xl p-6 text-center" style={{ background: 'linear-gradient(135deg, rgba(139,92,246,0.2), rgba(236,72,153,0.2))', border: '1px solid rgba(139,92,246,0.3)' }}>
                      <div className="text-4xl mb-3">🏆</div>
                      <h3 className="text-xl font-bold mb-2">Game Over!</h3>
                      <p className="text-sm text-gray-400">
                        Winner: {globalState.playerIds[currentRoom.winner] || generatePlayerId(currentRoom.winner)}
                        {currentRoom.winner === wallet.address && <span className="text-yellow-400 ml-2">🎉 +{CONFIG.WINNER_EXP}XP</span>}
                      </p>
                      <div className="flex gap-4 justify-center mt-4">
                        <button onClick={handleLeaveRoom} className="px-4 py-2 bg-white/10 rounded-lg">Lobby</button>
                      </div>
                    </div>
                  )}

                  {currentRoom.phase !== 'finished' && (
                    <button onClick={handleLeaveRoom} className="w-full py-2 text-sm text-gray-500 hover:text-gray-300">Leave</button>
                  )}
                </div>

                {/* Right Column */}
                <div className="space-y-4">
                  {currentRoom.phase === 'playing' && (
                    <div className="glass rounded-xl p-5">
                      <h3 className="font-semibold mb-3">💬 Describe the Art</h3>
                      <div className="chat-scroll mb-4 space-y-2 p-2 bg-black/20 rounded-lg min-h-[200px]">
                        {currentRoom.messages.length === 0 ? (
                          <div className="text-center py-8 text-gray-500 text-sm">Start describing!</div>
                        ) : (
                          currentRoom.messages.map(msg => (
                            <div key={msg.id} className={`p-3 rounded-lg ${msg.author === wallet.address ? 'bg-primary-500/20 ml-8' : 'bg-white/5 mr-8'}`}>
                              <div className="flex justify-between items-start mb-1">
                                <span className="text-xs font-medium text-gray-400">{globalState.playerIds[msg.author] || generatePlayerId(msg.author)}</span>
                                <span className="text-xs text-gray-500">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                              </div>
                              <p className="text-gray-200">{msg.content}</p>
                            </div>
                          ))
                        )}
                        <div ref={chatEndRef} />
                      </div>
                      <div className="flex gap-2">
                        <input type="text" value={message} onChange={e => setMessage(e.target.value)}
                          onKeyPress={e => e.key === 'Enter' && handleSendMessage()}
                          placeholder="Describe..." maxLength={300}
                          className="flex-1 px-4 py-2 rounded-lg bg-black/30 border border-white/10 text-gray-200 focus:outline-none focus:border-primary-500/50" />
                        <button onClick={handleSendMessage} disabled={!message.trim() || processing}
                          className={`px-4 py-2 rounded-lg font-medium ${message.trim() && !processing ? 'btn-success text-white' : 'bg-white/10 text-gray-500'}`}>
                          {processing ? <Spinner /> : 'Send'}
                        </button>
                      </div>
                    </div>
                  )}

                  {currentRoom.phase === 'voting' && (
                    <div className="glass rounded-xl p-5">
                      <h3 className="font-semibold mb-4">🗳️ Vote</h3>
                      <div className="space-y-3">
                        {currentRoom.messages.map(m => m.author).filter((v, i, a) => a.indexOf(v) === i).map(addr => {
                          const msgs = currentRoom.messages.filter(m => m.author === addr);
                          const isVoted = currentRoom.votes[wallet.address] === addr;
                          const voteCount = Object.values(currentRoom.votes || {}).filter(v => v === addr).length;
                          const canVote = !currentRoom.votes[wallet.address];
                          
                          return (
                            <div key={addr} onClick={() => canVote && handleVote(addr)}
                              className={`p-4 rounded-lg transition ${isVoted ? 'bg-primary-500/20 border border-primary-500/40' : 'bg-white/5 border border-white/5'} ${canVote ? 'cursor-pointer hover:bg-white/10' : ''}`}>
                              <div className="flex justify-between items-center mb-2">
                                <span className="text-sm font-medium">{globalState.playerIds[addr] || generatePlayerId(addr)}{addr === wallet.address ? ' (You)' : ''}</span>
                                <span className="text-yellow-500 text-sm">🗳️ {voteCount}</span>
                              </div>
                              <div className="space-y-1">
                                {msgs.slice(0, 2).map((m, i) => <p key={i} className="text-sm text-gray-300 truncate">"{m.content}"</p>)}
                              </div>
                              {isVoted && <div className="mt-2 text-sm text-primary-400">✓ Your vote</div>}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {currentRoom.phase === 'finished' && (
                    <div className="glass rounded-xl p-5">
                      <h3 className="font-semibold mb-4">📊 Results</h3>
                      <div className="space-y-2">
                        {currentRoom.messages.map(m => m.author).filter((v, i, a) => a.indexOf(v) === i)
                          .sort((a, b) => (currentRoom.voteCount?.[b] || 0) - (currentRoom.voteCount?.[a] || 0))
                          .map(addr => (
                            <div key={addr} className={`p-3 rounded-lg ${addr === currentRoom.winner ? 'bg-yellow-500/20' : 'bg-white/5'}`}>
                              <div className="flex justify-between">
                                <span>{addr === currentRoom.winner && '🏆 '}{globalState.playerIds[addr] || generatePlayerId(addr)}</span>
                                <span className="text-yellow-500">{currentRoom.voteCount?.[addr] || 0} votes</span>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Leaderboard */}
        {activeTab === 'leaderboard' && (
          <div className="glass rounded-2xl p-6 animate-fade-in">
            <h2 className="text-2xl font-bold text-center gradient-text-gold mb-6">🏆 Leaderboard</h2>
            {sortedLeaderboard.length === 0 ? (
              <div className="text-center py-10 text-gray-500">No data</div>
            ) : (
              <div className="space-y-2">
                {sortedLeaderboard.map((p, idx) => (
                  <div key={p.address} className={`grid grid-cols-[50px_1fr_70px_60px] items-center p-3 rounded-lg ${
                    idx === 0 ? 'bg-yellow-500/10' : p.address === wallet.address ? 'bg-primary-500/10' : 'bg-white/3'
                  }`}>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                      idx < 3 ? 'bg-gradient-to-br from-yellow-400 to-orange-500' : 'bg-white/10'
                    }`}>{idx < 3 ? ['🥇', '🥈', '🥉'][idx] : idx + 1}</div>
                    <span className="text-sm font-medium truncate">{p.playerId}{p.address === wallet.address && ' (You)'}</span>
                    <div className="text-center"><div className="font-bold text-primary-300">{p.experience}</div><div className="text-[10px] text-gray-500">XP</div></div>
                    <div className="text-center"><div className="font-bold text-green-400">{p.wins}</div><div className="text-[10px] text-gray-500">Wins</div></div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* History */}
        {activeTab === 'history' && (
          <div className="glass rounded-2xl p-6 animate-fade-in">
            <h2 className="text-2xl font-bold text-center mb-6">📜 History</h2>
            {myHistory.length === 0 ? (
              <div className="text-center py-10 text-gray-500">No history</div>
            ) : (
              <div className="space-y-4">
                {myHistory.map((record, idx) => {
                  const myPart = record.participants?.find(p => p.address === wallet.address);
                  const wasWinner = myPart?.isWinner;
                  
                  return (
                    <div key={record.id + idx} className={`p-5 rounded-xl border ${wasWinner ? 'bg-yellow-500/10 border-yellow-500/30' : 'bg-white/3 border-white/5'}`}>
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-3">
                          <ArtDisplay artId={record.artId} size={60} />
                          <div>
                            <div className="font-medium flex items-center gap-2">
                              {record.artName}
                              {record.onChain && <span className="text-xs px-1 py-0.5 bg-green-500/20 text-green-400 rounded">⛓️</span>}
                            </div>
                            <div className="text-sm text-gray-400">Game #{record.gameNumber}</div>
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">{formatDate(record.timestamp)}</div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 bg-white/5 rounded-lg">
                          <div className="text-xs text-gray-500 mb-1">Players</div>
                          {record.participants?.map(p => (
                            <div key={p.address} className="flex justify-between text-sm">
                              <span className={p.isWinner ? 'text-yellow-400' : ''}>{p.isWinner && '🏆 '}{p.playerId}</span>
                              <span className="text-gray-400">+{p.earnedXP}XP</span>
                            </div>
                          ))}
                        </div>
                        <div className="p-3 bg-white/5 rounded-lg">
                          <div className="text-xs text-gray-500 mb-1">Your Result</div>
                          {myPart && (
                            <div className="text-lg font-bold text-green-400">+{myPart.earnedXP}XP</div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="text-center py-6 border-t border-white/5 mt-8">
        <p className="text-sm text-gray-500 mb-2">Consensus Gallery • <a href="https://genlayer.com" target="_blank" className="text-primary-400">GenLayer</a></p>
        <div className="text-xs text-gray-600">
          <span>Contract: </span>
          <span className="font-mono text-primary-400/70">{shortenAddress(genLayer.getContractAddress())}</span>
          <span className="ml-2">({genLayer.getNetwork()})</span>
        </div>
      </footer>
    </div>
  );
}
