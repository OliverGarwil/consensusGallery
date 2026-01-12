/**
 * Deploy Consensus Gallery Contract to GenLayer
 * 
 * Usage: 
 *   node scripts/deploy.js
 * 
 * Environment:
 *   PRIVATE_KEY - Private key for deployment
 *   NETWORK - Network to deploy to (localnet, studionet, testnetAsimov)
 */

import { createClient, createAccount, generatePrivateKey } from 'genlayer-js';
import { studionet, localnet, testnetAsimov } from 'genlayer-js/chains';
import { readFileSync } from 'fs';

const TREASURY_ADDRESS = '0x0000000000000000000000000000000000000001';
const NETWORK = process.env.NETWORK || 'studionet';

const getChain = () => {
  switch (NETWORK) {
    case 'localnet': return localnet;
    case 'testnetAsimov': return testnetAsimov;
    default: return studionet;
  }
};

async function main() {
  console.log('='.repeat(50));
  console.log('Consensus Gallery - GenLayer Deployment');
  console.log('='.repeat(50));
  console.log(`Network: ${NETWORK}`);
  console.log('');

  // Create account
  const privateKey = process.env.PRIVATE_KEY || generatePrivateKey();
  const account = createAccount(privateKey);
  console.log(`Deployer: ${account.address}`);
  console.log('');

  // Create client
  const client = createClient({
    chain: getChain(),
    account,
  });

  // Initialize consensus
  console.log('Initializing consensus...');
  await client.initializeConsensusSmartContract();

  // Read contract code
  console.log('Reading contract...');
  const contractCode = readFileSync('./contracts/consensus_gallery.py', 'utf-8');

  // Deploy
  console.log('Deploying contract...');
  const hash = await client.deployContract({
    code: contractCode,
    args: [TREASURY_ADDRESS],
    leaderOnly: false,
  });

  console.log(`Transaction hash: ${hash}`);
  console.log('Waiting for confirmation...');

  // Wait for receipt
  const receipt = await client.waitForTransactionReceipt({
    hash,
    status: 'ACCEPTED',
    retries: 50,
    interval: 5000,
  });

  const contractAddress = receipt.data?.contract_address;
  
  console.log('');
  console.log('='.repeat(50));
  console.log('✅ Deployment Successful!');
  console.log('='.repeat(50));
  console.log(`Contract Address: ${contractAddress}`);
  console.log(`Transaction: ${hash}`);
  console.log('');
  console.log('Update your .env file:');
  console.log(`VITE_CONTRACT_ADDRESS=${contractAddress}`);
  console.log(`VITE_NETWORK=${NETWORK}`);
  console.log('');

  return contractAddress;
}

main().catch(console.error);
