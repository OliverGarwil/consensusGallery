# Consensus Gallery

一款基于 GenLayer 区块链的社交艺术游戏，通过社区共识机制描述艺术作品并赢取奖励！
- 项目演示：https://consensus-gallery5.vercel.app/


## 游戏介绍

**Consensus Gallery** 是一款创新的链上社交游戏，将艺术鉴赏与区块链共识机制相结合。玩家需要：

1.  **观看艺术作品** - 欣赏来自世界各地的名画
2.  **描述艺术** - 用自己的语言表达对艺术的理解
3.  **投票** - 为最佳描述投票
4.  **赢取奖励** - 获胜者获得经验值和排名提升

### 游戏特色

- **完全免费** - 无需任何 GEN 代币即可畅玩（入场费设为 0）
- **实时对战** - 2-5人房间，60秒游戏时长
- **链上存储** - 所有数据存储在 GenLayer Studio 网络
- **经验系统** - 赢得游戏获得100 XP，正确投票获得30 XP
- **排行榜** - 实时追踪玩家经验和胜场

## 🎮 游戏玩法

### 1. 连接钱包
- 点击 "Connect Wallet" 按钮
- 支持 MetaMask 等 Web3 钱包
- 自动切换到 GenLayer Studio 网络

### 2. 创建或加入房间
- **创建房间**：成为房主，等待其他玩家加入
- **加入房间**：选择已有房间，直接加入
- 房间人数：2-5人

### 3. 游戏阶段

#### 等待阶段 (Waiting)
- 房主等待玩家加入
- 至少需要2名玩家才能开始
- 房主可以启动游戏

#### 游戏阶段 (Playing) - 60秒
- 所有玩家查看同一幅艺术作品
- 在聊天框中描述这幅画
- 可以多次发送描述
- 倒计时结束后自动进入投票阶段

#### 投票阶段 (Voting) - 30秒
- 查看所有玩家的描述
- 为你认为最好的描述投票
- 每人只能投一票
- 不能为自己投票

#### 结算阶段 (Finished)
- 显示最终投票结果
- 获胜者获得 100 XP
- 正确投票者获得 30 XP
- 其他参与者获得 10 XP
- 更新排行榜

## 🛠 技术栈

### 前端技术
- **React 18** - UI框架
- **Tailwind CSS** - 样式框架
- **Babel Standalone** - JSX转译

### 区块链集成
- **GenLayer Studio** - Layer 1 区块链网络
- **Web3 Provider** - MetaMask集成
- **Chain ID**: 10242 (0x27F2)
- **RPC URL**: https://rpc.asimov.genlayer.com

### 数据存储
- **LocalStorage** - 本地游戏状态
- **实时同步** - 跨标签页状态管理

### 艺术资源
- Wikipedia Commons - 12幅世界名画
- 包括梵高、达利、北斋、克里姆特等大师作品

## 📁 项目结构

```
consensus-gallery/
├── index.html          # 游戏主文件（单页应用）
├── vercel.json         # Vercel部署配置
├── package.json        # 项目配置
├── README.md          # 项目文档
└── .gitignore         # Git忽略文件
```

## 本地部署

**启动本地服务器**
   ```bash
   # 使用 Python
   python -m http.server 8000



## 🔧 配置说明

### GenLayer 网络配置

游戏已预配置 GenLayer Studio 网络，连接钱包时会自动添加：

```javascript
{
  chainId: '0x27F2',           // 10242
  chainName: 'GenLayer Studio',
  rpcUrls: ['https://rpc.asimov.genlayer.com'],
  nativeCurrency: {
    name: 'GEN',
    symbol: 'GEN',
    decimals: 18
  },
  blockExplorerUrls: ['https://studio.genlayer.com']
}
```

### 游戏参数配置

在 `index.html` 中可以调整以下参数：

```javascript
const CONFIG = {
  MAX_PLAYERS: 5,              // 最大玩家数
  MIN_PLAYERS: 2,              // 最小玩家数
  ENTRY_FEE: 0,               // 入场费（当前为0）
  MIN_GAME_DURATION: 60,      // 游戏时长（秒）
  VOTE_DURATION: 30,          // 投票时长（秒）
  WINNER_EXP: 100,            // 获胜者经验值
  CORRECT_VOTER_EXP: 30,      // 正确投票者经验值
  PARTICIPANT_EXP: 10,        // 参与者经验值
};
```

## 艺术作品列表

游戏包含12幅世界名画：

| 作品名 | 艺术家 | 年份 |
|--------|--------|------|
| Starry Night | Van Gogh | 1889 |
| Persistence of Memory | Dali | 1931 |
| The Great Wave | Hokusai | 1831 |
| Girl with Pearl Earring | Vermeer | 1665 |
| The Scream | Munch | 1893 |
| Birth of Venus | Botticelli | 1485 |
| American Gothic | Wood | 1930 |
| The Kiss | Klimt | 1908 |
| Cafe Terrace | Van Gogh | 1888 |
| Water Lilies | Monet | 1906 |
| Whistlers Mother | Whistler | 1871 |
| La Grande Jatte | Seurat | 1886 |

## 开发路线图

### 当前版本 (v1.0)
- ✅ 基础游戏功能
- ✅ 钱包连接
- ✅ 多人房间系统
- ✅ 投票机制
- ✅ 经验系统
- ✅ 排行榜

### 计划功能 (v2.0)
- 🔄 智能合约集成
- 🔄 NFT 奖励系统
- 🔄 AI 评分辅助
- 🔄 更多艺术作品
- 🔄 多语言支持
- 🔄 成就系统

## 常见问题

### Q: 为什么需要连接钱包？
A: 虽然游戏是免费的，但我们使用钱包地址作为玩家身份标识，并为未来的链上功能做准备。

### Q: 我的数据安全吗？
A: 游戏数据存储在本地浏览器中，不会上传到服务器。钱包仅用于身份验证。

### Q: 可以添加自己的艺术作品吗？
A: 当前版本使用固定的艺术品列表。未来版本将支持用户上传。

### Q: 如何获取 GEN 测试币？
A: 当前游戏完全免费，不需要任何代币。未来版本可能需要测试币。



## 相关链接

- [GenLayer 官网](https://genlayer.com)
- [GenLayer Studio](https://studio.genlayer.com)
- [GenLayer 文档](https://docs.genlayer.com)


## 开发团队

由 GenLayer 社区开发者共同维护

Made with ❤️ by GenLayer Community
