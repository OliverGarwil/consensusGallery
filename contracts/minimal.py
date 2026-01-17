# { "Depends": "py-genlayer:test" }
"""
Consensus Gallery - Minimal Version for GenLayer
"""

from genlayer import *


class ConsensusGallery(gl.Contract):
    owner: str
    total_games: u32
    
    # Simple storage using strings
    rooms: TreeMap[str, str]  # room_id -> "phase,creator,art_id,players,winner"
    messages: TreeMap[str, str]  # room_id -> "addr|msg|time;;addr|msg|time"
    votes: TreeMap[str, str]  # room_id -> "voter:target;;voter:target"
    stats: TreeMap[str, str]  # address -> "exp,wins"

    def __init__(self):
        self.owner = gl.message.sender_address.as_hex
        self.total_games = u32(0)

    @gl.public.write
    def create_room(self) -> str:
        sender = gl.message.sender_address.as_hex
        self.total_games = u32(self.total_games + 1)
        
        room_id = f"r{self.total_games}"
        art_id = str((int(gl.block.timestamp) % 15) + 1)
        
        # phase,creator,art_id,players,winner
        self.rooms[room_id] = f"0,{sender},{art_id},{sender},"
        self.messages[room_id] = ""
        self.votes[room_id] = ""
        
        return room_id

    @gl.public.write
    def join_room(self, room_id: str) -> str:
        sender = gl.message.sender_address.as_hex
        data = self.rooms.get(room_id, "")
        if not data:
            return "not_found"
        
        parts = data.split(",")
        if parts[0] != "0":
            return "started"
        if sender in parts[3]:
            return "already_in"
        
        parts[3] = parts[3] + ";" + sender
        self.rooms[room_id] = ",".join(parts)
        return "joined"

    @gl.public.write
    def start_game(self, room_id: str) -> str:
        sender = gl.message.sender_address.as_hex
        data = self.rooms.get(room_id, "")
        if not data:
            return "not_found"
        
        parts = data.split(",")
        if parts[1] != sender:
            return "not_creator"
        if parts[0] != "0":
            return "already_started"
        if len(parts[3].split(";")) < 2:
            return "need_players"
        
        parts[0] = "1"
        self.rooms[room_id] = ",".join(parts)
        return "started"

    @gl.public.write
    def send_msg(self, room_id: str, content: str) -> str:
        sender = gl.message.sender_address.as_hex
        data = self.rooms.get(room_id, "")
        if not data:
            return "not_found"
        
        parts = data.split(",")
        if parts[0] != "1":
            return "not_playing"
        if sender not in parts[3]:
            return "not_in_room"
        
        msgs = self.messages.get(room_id, "")
        new_msg = f"{sender}|{content}|{gl.block.timestamp}"
        self.messages[room_id] = (msgs + ";;" + new_msg) if msgs else new_msg
        return "sent"

    @gl.public.write
    def start_vote(self, room_id: str) -> str:
        data = self.rooms.get(room_id, "")
        if not data:
            return "not_found"
        
        parts = data.split(",")
        if parts[0] != "1":
            return "not_playing"
        
        parts[0] = "2"
        self.rooms[room_id] = ",".join(parts)
        return "voting"

    @gl.public.write
    def vote(self, room_id: str, target: str) -> str:
        sender = gl.message.sender_address.as_hex
        data = self.rooms.get(room_id, "")
        if not data:
            return "not_found"
        
        parts = data.split(",")
        if parts[0] != "2":
            return "not_voting"
        
        v = self.votes.get(room_id, "")
        if sender in v:
            return "voted"
        
        new_v = f"{sender}:{target}"
        self.votes[room_id] = (v + ";;" + new_v) if v else new_v
        return "ok"

    @gl.public.write
    def finish(self, room_id: str) -> str:
        data = self.rooms.get(room_id, "")
        if not data:
            return "not_found"
        
        parts = data.split(",")
        if parts[0] != "2":
            return "not_voting"
        
        # Count votes
        v = self.votes.get(room_id, "")
        counts = {}
        if v:
            for vote in v.split(";;"):
                if ":" in vote:
                    t = vote.split(":")[1]
                    counts[t] = counts.get(t, 0) + 1
        
        # Find winner
        winner = ""
        max_v = 0
        for addr, cnt in counts.items():
            if cnt > max_v:
                max_v = cnt
                winner = addr
        
        if not winner:
            players = parts[3].split(";")
            winner = players[0] if players else ""
        
        # Update winner stats
        if winner:
            s = self.stats.get(winner, "0,0")
            sp = s.split(",")
            exp = int(sp[0]) + 100
            wins = int(sp[1]) + 1
            self.stats[winner] = f"{exp},{wins}"
        
        parts[0] = "3"
        parts[4] = winner
        self.rooms[room_id] = ",".join(parts)
        return winner

    @gl.public.view
    def get_room(self, room_id: str) -> str:
        return self.rooms.get(room_id, "")

    @gl.public.view
    def get_msgs(self, room_id: str) -> str:
        return self.messages.get(room_id, "")

    @gl.public.view
    def get_votes(self, room_id: str) -> str:
        return self.votes.get(room_id, "")

    @gl.public.view
    def get_stats(self, addr: str) -> str:
        return self.stats.get(addr, "0,0")

    @gl.public.view
    def total(self) -> u32:
        return self.total_games
