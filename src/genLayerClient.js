/**
 * GenLayer Client - SDK wrapper for Consensus Gallery
 */

import { createClient, createAccount, generatePrivateKey } from 'genlayer-js';
import { studionet, localnet, testnetAsimov } from 'genlayer-js/chains';

// Contract configuration
const CONTRACT_ADDRESS = import.meta.env.VITE_CONTRACT_ADDRESS || '0x5c2F525BA54839338F9BC9Cd8DF7B656FBc5E7d0';
const NETWORK = import.meta.env.VITE_NETWORK || 'studionet';

// Entry fee in wei (0.0001 GEN)
const ENTRY_FEE = 100000000000000n;

// Get chain config based on network
const getChain = () => {
  switch (NETWORK) {
    case 'localnet': return localnet;
    case 'testnetAsimov': return testnetAsimov;
    case 'studionet':
    default: return studionet;
  }
};

// Client instance
let client = null;
let currentAccount = null;

/**
 * Initialize the GenLayer client
 */
export const initClient = async (privateKey = null) => {
  try {
    const chain = getChain();
    
    if (privateKey) {
      currentAccount = createAccount(privateKey);
    } else {
      // Generate new account for testing
      const newPrivateKey = generatePrivateKey();
      currentAccount = createAccount(newPrivateKey);
      console.log('Generated new account:', currentAccount.address);
    }
    
    client = createClient({
      chain,
      account: currentAccount,
    });
    
    // Initialize consensus smart contract
    await client.initializeConsensusSmartContract();
    
    return {
      success: true,
      address: currentAccount.address,
      privateKey: currentAccount.privateKey,
    };
  } catch (error) {
    console.error('Failed to init client:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Get current account address
 */
export const getAddress = () => {
  return currentAccount?.address || null;
};

/**
 * Get contract address
 */
export const getContractAddress = () => CONTRACT_ADDRESS;

/**
 * Get network name
 */
export const getNetwork = () => NETWORK;

/**
 * Read from contract (view function)
 */
export const readContract = async (functionName, args = []) => {
  if (!client) throw new Error('Client not initialized');
  
  try {
    const result = await client.readContract({
      address: CONTRACT_ADDRESS,
      functionName,
      args,
    });
    return { success: true, data: result };
  } catch (error) {
    console.error(`readContract ${functionName} failed:`, error);
    return { success: false, error: error.message };
  }
};

/**
 * Write to contract (transaction)
 */
export const writeContract = async (functionName, args = [], value = 0n) => {
  if (!client) throw new Error('Client not initialized');
  
  try {
    const hash = await client.writeContract({
      address: CONTRACT_ADDRESS,
      functionName,
      args,
      value,
    });
    
    console.log(`Transaction sent: ${hash}`);
    return { success: true, hash };
  } catch (error) {
    console.error(`writeContract ${functionName} failed:`, error);
    return { success: false, error: error.message };
  }
};

/**
 * Wait for transaction receipt
 */
export const waitForReceipt = async (hash, status = 'ACCEPTED', retries = 50) => {
  if (!client) throw new Error('Client not initialized');
  
  try {
    const receipt = await client.waitForTransactionReceipt({
      hash,
      status,
      retries,
      interval: 3000,
    });
    return { success: true, receipt };
  } catch (error) {
    console.error('waitForReceipt failed:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Create room on chain
 */
export const createRoom = async () => {
  const result = await writeContract('create_room', [], ENTRY_FEE);
  if (!result.success) return result;
  
  const receiptResult = await waitForReceipt(result.hash);
  if (!receiptResult.success) return receiptResult;
  
  return {
    success: true,
    hash: result.hash,
    receipt: receiptResult.receipt,
    roomId: receiptResult.receipt?.data?.result,
  };
};

/**
 * Join room on chain
 */
export const joinRoom = async (roomId) => {
  const result = await writeContract('join_room', [roomId], ENTRY_FEE);
  if (!result.success) return result;
  
  const receiptResult = await waitForReceipt(result.hash);
  return {
    success: receiptResult.success,
    hash: result.hash,
    receipt: receiptResult.receipt,
  };
};

/**
 * Start game on chain
 */
export const startGame = async (roomId) => {
  const result = await writeContract('start_game', [roomId]);
  if (!result.success) return result;
  
  const receiptResult = await waitForReceipt(result.hash);
  return {
    success: receiptResult.success,
    hash: result.hash,
    receipt: receiptResult.receipt,
  };
};

/**
 * Send message on chain
 */
export const sendMessage = async (roomId, content) => {
  const result = await writeContract('send_message', [roomId, content]);
  if (!result.success) return result;
  
  const receiptResult = await waitForReceipt(result.hash);
  return {
    success: receiptResult.success,
    hash: result.hash,
    receipt: receiptResult.receipt,
  };
};

/**
 * Vote to end game
 */
export const voteEndGame = async (roomId) => {
  const result = await writeContract('vote_end_game', [roomId]);
  if (!result.success) return result;
  
  const receiptResult = await waitForReceipt(result.hash);
  return {
    success: receiptResult.success,
    hash: result.hash,
    receipt: receiptResult.receipt,
  };
};

/**
 * Final vote
 */
export const vote = async (roomId, targetAddress) => {
  const result = await writeContract('vote', [roomId, targetAddress]);
  if (!result.success) return result;
  
  const receiptResult = await waitForReceipt(result.hash);
  return {
    success: receiptResult.success,
    hash: result.hash,
    receipt: receiptResult.receipt,
  };
};

/**
 * Get room info
 */
export const getRoom = async (roomId) => {
  return readContract('get_room', [roomId]);
};

/**
 * Get player stats
 */
export const getPlayerStats = async (address) => {
  return readContract('get_player_stats', [address]);
};

/**
 * Get player ID
 */
export const getPlayerId = async (address) => {
  return readContract('get_player_id', [address]);
};

export default {
  initClient,
  getAddress,
  getContractAddress,
  getNetwork,
  readContract,
  writeContract,
  waitForReceipt,
  createRoom,
  joinRoom,
  startGame,
  sendMessage,
  voteEndGame,
  vote,
  getRoom,
  getPlayerStats,
  getPlayerId,
};
