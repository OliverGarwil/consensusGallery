# { "Depends": "py-genlayer:test" }
"""
Consensus Gallery - Hybrid Version
只存储关键数据：玩家统计 + 游戏历史
实时游戏数据通过 Firebase 同步
"""

from genlayer import *


class ConsensusGalleryStats(gl.Contract):
    owner: str
    game_count: u32
    
    # 玩家统计: address -> "exp,wins,games"
    stats: TreeMap[str, str]
    
    # 玩家ID: address -> "PlayerId"
    player_ids: TreeMap[str, str]
    
    # 游戏历史: "rid:winner:art:time;;rid:winner:art:time" (最近50场)
    history: str

    def __init__(self):
        self.owner = gl.message.sender_address.as_hex
        self.game_count = u32(0)
        self.history = ""

    @gl.public.write
    def join_game(self, room_id: str) -> str:
        """
        创建或加入房间时调用
        产生链上交易记录，实际扣除GEN为0
        """
        return "OK"

    @gl.public.write
    def record_game(self, room_id: str, winner: str, art_id: str, participants: str) -> str:
        """
        游戏结束时调用，记录结果并更新统计
        participants: "addr1,addr2,addr3" (所有参与者)
        """
        self.game_count = u32(self.game_count + 1)
        
        # 更新所有参与者的统计
        for addr in participants.split(","):
            addr = addr.strip()
            if not addr or addr.startswith("AI_"):
                continue
                
            cur = self.stats.get(addr, "0,0,0")
            parts = cur.split(",")
            exp = int(parts[0])
            wins = int(parts[1])
            games = int(parts[2])
            
            if addr == winner:
                exp += 100  # 胜者 +100 XP
                wins += 1
            else:
                exp += 10   # 参与 +10 XP
            games += 1
            
            self.stats[addr] = f"{exp},{wins},{games}"
        
        # 添加到历史
        timestamp = gl.block.timestamp
        entry = f"{room_id}:{winner}:{art_id}:{timestamp}"
        
        if self.history:
            hist_list = self.history.split(";;")
            if len(hist_list) >= 50:
                hist_list = hist_list[-49:]
            hist_list.append(entry)
            self.history = ";;".join(hist_list)
        else:
            self.history = entry
        
        return "OK"

    @gl.public.write
    def set_player_id(self, player_id: str) -> str:
        """玩家设置自己的显示名称"""
        sender = gl.message.sender_address.as_hex
        if len(player_id) > 20:
            return "TOO_LONG"
        self.player_ids[sender] = player_id
        return "OK"

    @gl.public.view
    def get_stats(self, addr: str) -> str:
        """获取玩家统计: exp,wins,games"""
        return self.stats.get(addr, "0,0,0")

    @gl.public.view
    def get_player_id(self, addr: str) -> str:
        """获取玩家显示名称"""
        return self.player_ids.get(addr, "")

    @gl.public.view
    def get_history(self) -> str:
        """获取游戏历史"""
        return self.history

    @gl.public.view
    def get_game_count(self) -> u32:
        """获取总游戏数"""
        return self.game_count

    @gl.public.view
    def get_leaderboard(self, addresses: str) -> str:
        """
        获取指定地址的统计
        addresses: "addr1,addr2,addr3"
        返回: "addr1:exp1,wins1,games1;;addr2:exp2,wins2,games2"
        """
        result = []
        for addr in addresses.split(","):
            addr = addr.strip()
            if addr:
                stats = self.stats.get(addr, "0,0,0")
                pid = self.player_ids.get(addr, "")
                result.append(f"{addr}:{pid}:{stats}")
        return ";;".join(result)
