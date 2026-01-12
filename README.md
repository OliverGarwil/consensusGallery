# 🎨 Consensus Gallery DApp

> On-Chain Art Description Game built with GenLayerJS SDK

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📦 Project Structure

```
consensus-gallery-dapp/
├── src/
│   ├── main.jsx           # Entry point
│   ├── App.jsx            # Main app component
│   ├── genLayerClient.js  # GenLayerJS SDK wrapper
│   ├── constants.js       # Game config & art collection
│   └── index.css          # Styles
├── contracts/
│   └── consensus_gallery.py  # GenLayer smart contract
├── scripts/
│   └── deploy.js          # Deployment script
├── public/
├── .env                   # Environment config
├── package.json
├── vite.config.js
├── tailwind.config.js
└── README.md
```

## ⚙️ Configuration

Edit `.env` file:

```env
VITE_CONTRACT_ADDRESS=0x5c2F525BA54839338F9BC9Cd8DF7B656FBc5E7d0
VITE_NETWORK=studionet
```

## 🔗 Contract Deployment

### Deploy to Studionet

```bash
NETWORK=studionet npm run deploy
```

### Deploy to Testnet Asimov

```bash
NETWORK=testnetAsimov npm run deploy
```

### Deploy to Localnet

```bash
# Start local GenLayer Studio first
genlayer init

# Deploy
NETWORK=localnet npm run deploy
```

## 🎮 Features

### Game Flow

1. **Create Room** (On-Chain or Local)
2. **Wait for Players** (2-5 players)
3. **Start Game** (Host only)
4. **Chat Phase** (5-15 minutes)
5. **Vote to End** (>50% after 5 min)
6. **Final Vote** (30 seconds)
7. **Winner Announced**

### On-Chain Operations

| Function | Description |
|----------|-------------|
| `create_room` | Create new game room (0.0001 GEN) |
| `join_room` | Join existing room (0.0001 GEN) |
| `start_game` | Start the game (host only) |
| `send_message` | Send art description |
| `vote_end_game` | Vote to end playing phase |
| `vote` | Final vote for best player |

### XP Rewards

| Action | XP |
|--------|-----|
| Winner | +100 |
| Correct Vote | +30 |
| Participate | +10 |

## 🎨 Art Collection

15 classic masterpieces including:
- Starry Night (Van Gogh)
- The Persistence of Memory (Dali)
- The Great Wave (Hokusai)
- Girl with Pearl Earring (Vermeer)
- The Scream (Munch)
- And more...

## 🛠️ Tech Stack

- **Frontend**: React 18 + Vite
- **Styling**: Tailwind CSS
- **Blockchain**: GenLayer
- **SDK**: genlayer-js

## 📝 GenLayerJS Usage

### Initialize Client

```javascript
import { createClient, createAccount } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';

const account = createAccount();
const client = createClient({
  chain: studionet,
  account,
});

await client.initializeConsensusSmartContract();
```

### Read Contract

```javascript
const result = await client.readContract({
  address: CONTRACT_ADDRESS,
  functionName: 'get_room',
  args: [roomId],
});
```

### Write Contract

```javascript
const hash = await client.writeContract({
  address: CONTRACT_ADDRESS,
  functionName: 'create_room',
  args: [],
  value: 100000000000000n, // 0.0001 GEN
});

const receipt = await client.waitForTransactionReceipt({
  hash,
  status: 'ACCEPTED',
});
```

## 🔗 Links

- [GenLayer Docs](https://docs.genlayer.com)
- [GenLayerJS SDK](https://github.com/genlayerlabs/genlayer-js)
- [GenLayer Studio](https://studio.genlayer.com)

## 📄 License

MIT
