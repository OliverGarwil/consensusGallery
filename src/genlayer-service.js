/**
 * GenLayer Blockchain Service
 * Handles all interactions with the GenLayer blockchain
 */

// Network configurations
const NETWORKS = {
  localnet: {
    name: 'GenLayer Localnet',
    chainId: 61999,
    rpcUrl: 'http://localhost:4000/api',
    explorerUrl: 'http://localhost:4000'
  },
  studionet: {
    name: 'GenLayer Studio',
    chainId: 61999,
    rpcUrl: 'https://rpc.studio.genlayer.com',
    explorerUrl: 'https://studio.genlayer.com'
  },
  testnet: {
    name: 'GenLayer Testnet Asimov',
    chainId: 61999,
    rpcUrl: 'https://rpc.testnet-asimov.genlayer.com',
    explorerUrl: 'https://explorer.testnet-asimov.genlayer.com'
  }
};

// Transaction status enum
const TransactionStatus = {
  PENDING: 'PENDING',
  PROPOSING: 'PROPOSING',
  COMMITTING: 'COMMITTING',
  REVEALING: 'REVEALING',
  ACCEPTED: 'ACCEPTED',
  FINALIZED: 'FINALIZED',
  CANCELED: 'CANCELED',
  UNDETERMINED: 'UNDETERMINED'
};

class GenLayerService {
  constructor(networkId = 'studionet', contractAddress = null) {
    this.network = NETWORKS[networkId] || NETWORKS.studionet;
    this.contractAddress = contractAddress;
    this.requestId = 0;
    this.account = null;
  }

  /**
   * Set the contract address
   */
  setContractAddress(address) {
    this.contractAddress = address;
  }

  /**
   * Set the current account
   */
  setAccount(account) {
    this.account = account;
  }

  /**
   * Make a JSON-RPC call to the GenLayer node
   */
  async rpcCall(method, params = []) {
    try {
      const response = await fetch(this.network.rpcUrl, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: ++this.requestId,
          method,
          params
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error.message || 'RPC Error');
      }
      
      return data.result;
    } catch (error) {
      console.error('RPC Call Error:', error);
      throw error;
    }
  }

  /**
   * Read data from the contract (no transaction needed)
   */
  async readContract(functionName, args = []) {
    if (!this.contractAddress) {
      throw new Error('Contract address not set');
    }

    return this.rpcCall('gen_call', [{
      to: this.contractAddress,
      data: { 
        function: functionName, 
        args: args 
      }
    }]);
  }

  /**
   * Write data to the contract (requires transaction)
   * Uses MetaMask for signing
   */
  async writeContract(functionName, args = [], value = '0x0') {
    if (!this.contractAddress) {
      throw new Error('Contract address not set');
    }

    if (!window.ethereum) {
      throw new Error('MetaMask not found');
    }

    const accounts = await window.ethereum.request({ 
      method: 'eth_accounts' 
    });

    if (accounts.length === 0) {
      throw new Error('No account connected');
    }

    const from = accounts[0];

    // Prepare transaction data
    // GenLayer uses a special encoding for function calls
    const callData = {
      function: functionName,
      args: args
    };

    const txParams = {
      from: from,
      to: this.contractAddress,
      value: value,
      data: '0x' + Buffer.from(JSON.stringify(callData)).toString('hex')
    };

    // Send transaction via MetaMask
    const txHash = await window.ethereum.request({
      method: 'eth_sendTransaction',
      params: [txParams]
    });

    return txHash;
  }

  /**
   * Wait for a transaction to be confirmed
   */
  async waitForTransaction(hash, targetStatus = 'FINALIZED', timeout = 60000, interval = 2000) {
    const startTime = Date.now();
    
    const statusPriority = {
      'PENDING': 0,
      'PROPOSING': 1,
      'COMMITTING': 2,
      'REVEALING': 3,
      'ACCEPTED': 4,
      'FINALIZED': 5
    };

    const targetPriority = statusPriority[targetStatus] || 5;

    while (Date.now() - startTime < timeout) {
      try {
        const receipt = await this.rpcCall('gen_getTransactionReceipt', [hash]);
        
        if (receipt) {
          const currentPriority = statusPriority[receipt.status] || 0;
          
          if (currentPriority >= targetPriority) {
            return receipt;
          }
          
          if (receipt.status === 'CANCELED' || receipt.status === 'UNDETERMINED') {
            throw new Error(`Transaction ${receipt.status}`);
          }
        }
      } catch (e) {
        // Receipt not available yet, continue waiting
      }
      
      await new Promise(r => setTimeout(r, interval));
    }
    
    throw new Error('Transaction timeout');
  }

  /**
   * Get contract state
   */
  async getContractState() {
    if (!this.contractAddress) {
      throw new Error('Contract address not set');
    }

    return this.rpcCall('gen_getContractState', [this.contractAddress]);
  }

  /**
   * Get contract schema (ABI equivalent)
   */
  async getContractSchema() {
    if (!this.contractAddress) {
      throw new Error('Contract address not set');
    }

    return this.rpcCall('gen_getContractSchema', [this.contractAddress]);
  }

  // ==================== Game-specific methods ====================

  /**
   * Create a new game room
   */
  async createRoom() {
    const value = '0x' + (100000000000000).toString(16); // 0.0001 GEN in wei
    const txHash = await this.writeContract('create_room', [], value);
    const receipt = await this.waitForTransaction(txHash, 'ACCEPTED');
    return receipt;
  }

  /**
   * Join an existing room
   */
  async joinRoom(roomId) {
    const value = '0x' + (100000000000000).toString(16);
    const txHash = await this.writeContract('join_room', [roomId], value);
    const receipt = await this.waitForTransaction(txHash, 'ACCEPTED');
    return receipt;
  }

  /**
   * Start the game
   */
  async startGame(roomId) {
    const txHash = await this.writeContract('start_game', [roomId]);
    const receipt = await this.waitForTransaction(txHash, 'ACCEPTED');
    return receipt;
  }

  /**
   * Send a message (art description)
   */
  async sendMessage(roomId, content) {
    const txHash = await this.writeContract('send_message', [roomId, content]);
    const receipt = await this.waitForTransaction(txHash, 'ACCEPTED');
    return receipt;
  }

  /**
   * Vote for a player
   */
  async vote(roomId, targetAddress) {
    const txHash = await this.writeContract('vote', [roomId, targetAddress]);
    const receipt = await this.waitForTransaction(txHash, 'ACCEPTED');
    return receipt;
  }

  /**
   * Vote to end the game
   */
  async voteEndGame(roomId) {
    const txHash = await this.writeContract('vote_end_game', [roomId]);
    const receipt = await this.waitForTransaction(txHash, 'ACCEPTED');
    return receipt;
  }

  /**
   * Finalize the game
   */
  async finalizeGame(roomId) {
    const txHash = await this.writeContract('finalize_game', [roomId]);
    const receipt = await this.waitForTransaction(txHash, 'ACCEPTED');
    return receipt;
  }

  /**
   * Get active rooms
   */
  async getActiveRooms() {
    try {
      return await this.readContract('get_active_rooms', []);
    } catch (e) {
      console.error('Error getting active rooms:', e);
      return [];
    }
  }

  /**
   * Get room details
   */
  async getRoom(roomId) {
    try {
      return await this.readContract('get_room', [roomId]);
    } catch (e) {
      console.error('Error getting room:', e);
      return null;
    }
  }

  /**
   * Get room players
   */
  async getRoomPlayers(roomId) {
    try {
      return await this.readContract('get_room_players', [roomId]);
    } catch (e) {
      console.error('Error getting room players:', e);
      return [];
    }
  }

  /**
   * Get room messages
   */
  async getRoomMessages(roomId) {
    try {
      const result = await this.readContract('get_room_messages', [roomId]);
      
      // Parse flat structure to array
      const messages = [];
      const count = parseInt(result.count || '0');
      
      for (let i = 0; i < count; i++) {
        messages.push({
          id: result[`msg_${i}_id`],
          author: result[`msg_${i}_author`],
          content: result[`msg_${i}_content`],
          timestamp: parseInt(result[`msg_${i}_timestamp`] || '0')
        });
      }
      
      return messages;
    } catch (e) {
      console.error('Error getting room messages:', e);
      return [];
    }
  }

  /**
   * Get room votes
   */
  async getRoomVotes(roomId) {
    try {
      return await this.readContract('get_room_votes', [roomId]);
    } catch (e) {
      console.error('Error getting room votes:', e);
      return {};
    }
  }

  /**
   * Get player stats
   */
  async getPlayerStats(address) {
    try {
      return await this.readContract('get_player_stats', [address]);
    } catch (e) {
      console.error('Error getting player stats:', e);
      return {
        experience: '0',
        wins: '0',
        participations: '0',
        total_rewards: '0',
        player_id: ''
      };
    }
  }

  /**
   * Get player ID
   */
  async getPlayerId(address) {
    try {
      return await this.readContract('get_player_id', [address]);
    } catch (e) {
      console.error('Error getting player ID:', e);
      return '';
    }
  }

  /**
   * Get contract info
   */
  async getContractInfo() {
    try {
      return await this.readContract('get_contract_info', []);
    } catch (e) {
      console.error('Error getting contract info:', e);
      return null;
    }
  }

  /**
   * Get game history
   */
  async getGameHistory(limit = 10) {
    try {
      return await this.readContract('get_game_history', [limit]);
    } catch (e) {
      console.error('Error getting game history:', e);
      return {};
    }
  }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { GenLayerService, NETWORKS, TransactionStatus };
}

// Also expose globally for browser use
if (typeof window !== 'undefined') {
  window.GenLayerService = GenLayerService;
  window.NETWORKS = NETWORKS;
  window.TransactionStatus = TransactionStatus;
}
