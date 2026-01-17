# Consensus Gallery - GenLayer Blockchain Game

🎨 A multiplayer art description game running on GenLayer blockchain. Players compete to write the best descriptions of famous artworks, with all game actions recorded on-chain.

## 🌟 Features

- **On-Chain Gaming**: All game state is stored on GenLayer blockchain
- **Real-time Multiplayer**: Multiple players can join the same game room
- **MetaMask Integration**: Connect your wallet to play
- **Prize Pool**: Winners receive 80% of the entry fee pool
- **XP System**: Earn experience points for winning, voting correctly, and participating

## 🏗️ Architecture

```
consensus-gallery-blockchain/
├── contracts/
│   └── consensus_gallery.py    # GenLayer Intelligent Contract
├── public/
│   └── index.html              # Frontend application
├── vercel.json                 # Vercel deployment config
└── README.md
```

## 🚀 Deployment

### 合约文件说明

| 文件 | 说明 | 推荐场景 |
|------|------|----------|
| `contracts/minimal.py` | **最简化版** - 推荐先部署这个 | 首次测试 |
| `contracts/consensus_gallery_simple.py` | 简化版 | 功能测试 |
| `contracts/consensus_gallery.py` | 完整版 | 生产环境 |

**建议**: 先用 `minimal.py` 测试部署是否成功，再尝试完整版。

### Step 1: Deploy the Smart Contract to GenLayer

#### Option A: Using GenLayer CLI

```bash
# Install GenLayer CLI (correct package name is "genlayer", not "genlayer-cli")
npm install -g genlayer

# Configure network (choose one)
genlayer network localnet      # For local development
genlayer network studionet     # For GenLayer Studio
genlayer network testnet-asimov # For testnet

# Deploy the contract
genlayer deploy --contract contracts/consensus_gallery.py --args "YOUR_TREASURY_ADDRESS"
```

#### Option B: Using GenLayer Studio (Recommended for beginners)

This is the **easiest method** - no CLI installation required!

1. Go to [GenLayer Studio](https://studio.genlayer.com)
2. Connect your wallet
3. Click "Contracts" → "New Contract"
4. Copy the contract code from `contracts/consensus_gallery.py`
5. Click "Deploy"
6. Enter your treasury address when prompted
7. **Copy the deployed contract address** (you'll need this!)

#### Option C: Using Local GenLayer (Advanced)

```bash
# Clone and run GenLayer Studio locally
git clone https://github.com/genlayerlabs/genlayer-studio
cd genlayer-studio
npm install -g genlayer
genlayer up

# Then deploy via the local Studio UI at http://localhost:8080
```

### Step 2: Update Contract Address

Edit `public/index.html` and update the contract address:

```javascript
const CONTRACT = {
  ADDRESS: '0xYOUR_DEPLOYED_CONTRACT_ADDRESS',  // Update this!
  // ...
};
```

Also update `CURRENT_NETWORK` to match your deployment:

```javascript
CURRENT_NETWORK: 'studionet' // or 'localnet' or 'testnet'
```

### Step 3: Deploy Frontend to Vercel

#### Option A: Using Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd consensus-gallery-blockchain
vercel --prod
```

#### Option B: Using Vercel Dashboard

1. Push your code to GitHub
2. Go to [Vercel Dashboard](https://vercel.com)
3. Import your GitHub repository
4. Deploy!

## 🎮 How to Play

1. **Connect Wallet**: Click "Connect" to link your MetaMask wallet
2. **Create/Join Room**: Create a new game room or join an existing one
3. **Wait for Players**: Need at least 2 players to start
4. **Start Game**: Host clicks "Start Game" when ready
5. **Describe Art**: Write creative descriptions of the displayed artwork
6. **Vote**: Vote for the best description when voting phase begins
7. **Win Prizes**: Most voted player wins the prize pool!

## 💰 Rewards

| Action | XP Reward | GEN Reward |
|--------|-----------|------------|
| Win Game | +100 XP | 80% of pool |
| Vote for Winner | +30 XP | - |
| Participate | +10 XP | - |

## 🔧 Configuration

Key settings in `public/index.html`:

```javascript
const CONFIG = {
  MAX_PLAYERS: 5,           // Max players per room
  MIN_PLAYERS: 2,           // Min players to start
  ENTRY_FEE: 0.0001,        // Entry fee in GEN
  MIN_GAME_DURATION: 60,    // Min game time (seconds)
  MAX_GAME_DURATION: 300,   // Max game time (seconds)
  VOTE_DURATION: 60,        // Voting phase duration
  POLL_INTERVAL: 3000,      // Blockchain polling interval (ms)
};
```

## 🌐 Networks

| Network | RPC URL | Use Case |
|---------|---------|----------|
| Localnet | http://localhost:4000/api | Local development |
| Studionet | https://rpc.studio.genlayer.com | Testing in Studio |
| Testnet Asimov | https://rpc.testnet-asimov.genlayer.com | Public testnet |

## 📜 Smart Contract Functions

### Write Functions (require transaction)

| Function | Description |
|----------|-------------|
| `create_room()` | Create a new game room |
| `join_room(room_id)` | Join an existing room |
| `start_game(room_id)` | Start the game (creator only) |
| `send_message(room_id, content)` | Send art description |
| `vote(room_id, target)` | Vote for best description |
| `vote_end_game(room_id)` | Vote to end game early |
| `finalize_game(room_id)` | Finalize after voting |

### Read Functions (free)

| Function | Description |
|----------|-------------|
| `get_room(room_id)` | Get room details |
| `get_room_players(room_id)` | Get player list |
| `get_room_messages(room_id)` | Get all messages |
| `get_room_votes(room_id)` | Get voting results |
| `get_active_rooms()` | List active rooms |
| `get_player_stats(address)` | Get player statistics |
| `get_contract_info()` | Get config info |

## 🔒 Security Notes

- Entry fees are held in the contract until game ends
- Winners automatically receive prize (80% of pool)
- Treasury receives remaining 20%
- All game actions are verifiable on-chain

## 🛠️ Local Development

### Running GenLayer Locally

```bash
# Install GenLayer
pip install genlayer

# Start local node
genlayer node start

# Deploy contract
genlayer deploy --contract contracts/consensus_gallery.py --args "0xYourAddress"
```

### Testing the Frontend

```bash
# Serve locally
npx serve public

# Or use Python
cd public && python -m http.server 3000
```

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📞 Support

- [GenLayer Documentation](https://docs.genlayer.com)
- [GenLayer Discord](https://discord.gg/genlayer)
- [GenLayer Telegram](https://t.me/genlayer)

---

Built with ❤️ on GenLayer
