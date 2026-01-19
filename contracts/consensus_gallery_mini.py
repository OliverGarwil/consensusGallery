# { "Depends": "py-genlayer:test" }
"""
Consensus Gallery - Minimal Version for GenLayer Studio
"""

from genlayer import *


class ConsensusGallery(gl.Contract):
    owner: str
    game_count: u32
    
    # Simplified storage using strings
    rooms: TreeMap[str, str]  # room_id -> "phase,creator,art_id,create_time,winner"
    players: TreeMap[str, str]  # room_id -> "addr1,addr2,addr3"
    messages: TreeMap[str, str]  # room_id -> "author|msg|time;;author|msg|time"
    votes: TreeMap[str, str]  # room_id -> "voter:target;;voter:target"
    stats: TreeMap[str, str]  # address -> "exp,wins"
    room_ids: str  # Comma-separated list of all room ids

    def __init__(self):
        self.owner = gl.message.sender_address.as_hex
        self.game_count = u32(0)
        self.room_ids = ""

    @gl.public.write
    def create_room(self) -> str:
        sender = gl.message.sender_address.as_hex
        self.game_count = u32(self.game_count + 1)
        rid = f"r{self.game_count}"
        art = (gl.block.timestamp % 15) + 1
        create_time = gl.block.timestamp
        
        self.rooms[rid] = f"0,{sender},{art},{create_time},"
        self.players[rid] = sender
        self.messages[rid] = ""
        self.votes[rid] = ""
        
        # Add to room list
        if self.room_ids:
            self.room_ids = self.room_ids + "," + rid
        else:
            self.room_ids = rid
        
        return rid
    
    @gl.public.write
    def add_ai_player(self, rid: str) -> str:
        """Add AI player to room (called by creator after 30s timeout)"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[1] != sender:
            return "NOT_CREATOR"
        if parts[0] != "0":
            return "STARTED"
        
        plist = self.players.get(rid, "")
        # Add AI player with special prefix
        ai_addr = "AI_" + rid
        if ai_addr in plist:
            return "AI_EXISTS"
        
        self.players[rid] = plist + "," + ai_addr
        return "AI_ADDED"
    
    @gl.public.write
    def ai_send_msg(self, rid: str, msg: str) -> str:
        """AI sends a message (called by room creator on behalf of AI)"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[1] != sender:
            return "NOT_CREATOR"
        if parts[0] != "1":
            return "NOT_PLAYING"
        
        ai_addr = "AI_" + rid
        cur = self.messages.get(rid, "")
        entry = f"{ai_addr}|{msg}|{gl.block.timestamp}"
        self.messages[rid] = cur + ";;" + entry if cur else entry
        return "OK"
    
    @gl.public.write
    def ai_vote(self, rid: str, target: str) -> str:
        """AI votes (called by room creator on behalf of AI)"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[1] != sender:
            return "NOT_CREATOR"
        if parts[0] != "2":
            return "NOT_VOTING"
        
        ai_addr = "AI_" + rid
        cur = self.votes.get(rid, "")
        if ai_addr in cur:
            return "VOTED"
        
        entry = f"{ai_addr}:{target}"
        self.votes[rid] = cur + ";;" + entry if cur else entry
        return "OK"

    @gl.public.write
    def join_room(self, rid: str) -> str:
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[0] != "0":
            return "STARTED"
        
        plist = self.players.get(rid, "")
        if sender in plist:
            return "JOINED"
        if plist.count(",") >= 4:
            return "FULL"
        
        self.players[rid] = plist + "," + sender
        return "OK"

    @gl.public.write
    def start_game(self, rid: str) -> str:
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[1] != sender:
            return "NOT_CREATOR"
        if parts[0] != "0":
            return "STARTED"
        
        plist = self.players.get(rid, "")
        # Need at least 2 players (can include AI)
        if plist.count(",") < 1:
            return "NEED_PLAYERS"
        
        parts[0] = "1"
        self.rooms[rid] = ",".join(parts)
        return "OK"

    @gl.public.write
    def send_msg(self, rid: str, msg: str) -> str:
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[0] != "1":
            return "NOT_PLAYING"
        
        plist = self.players.get(rid, "")
        if sender not in plist:
            return "NOT_PLAYER"
        
        cur = self.messages.get(rid, "")
        entry = f"{sender}|{msg}|{gl.block.timestamp}"
        self.messages[rid] = cur + ";;" + entry if cur else entry
        return "OK"

    @gl.public.write
    def start_vote(self, rid: str) -> str:
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[0] != "1":
            return "NOT_PLAYING"
        
        parts[0] = "2"
        self.rooms[rid] = ",".join(parts)
        return "OK"

    @gl.public.write
    def vote(self, rid: str, target: str) -> str:
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[0] != "2":
            return "NOT_VOTING"
        
        cur = self.votes.get(rid, "")
        if sender in cur:
            return "VOTED"
        
        entry = f"{sender}:{target}"
        self.votes[rid] = cur + ";;" + entry if cur else entry
        return "OK"

    @gl.public.write
    def finish(self, rid: str) -> str:
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[0] != "2":
            return "NOT_VOTING"
        
        # Count votes
        vstr = self.votes.get(rid, "")
        counts = {}
        if vstr:
            for v in vstr.split(";;"):
                if ":" in v:
                    t = v.split(":")[1]
                    counts[t] = counts.get(t, 0) + 1
        
        # Find winner
        winner = ""
        maxv = 0
        for addr, cnt in counts.items():
            if cnt > maxv:
                maxv = cnt
                winner = addr
        
        # Update stats
        if winner:
            st = self.stats.get(winner, "0,0")
            sp = st.split(",")
            exp = int(sp[0]) + 100
            wins = int(sp[1]) + 1
            self.stats[winner] = f"{exp},{wins}"
        
        parts[0] = "3"
        parts[4] = winner
        self.rooms[rid] = ",".join(parts)
        return winner if winner else "NO_WINNER"

    @gl.public.view
    def get_room(self, rid: str) -> str:
        return self.rooms.get(rid, "")

    @gl.public.view
    def get_players(self, rid: str) -> str:
        return self.players.get(rid, "")

    @gl.public.view
    def get_messages(self, rid: str) -> str:
        return self.messages.get(rid, "")

    @gl.public.view
    def get_votes(self, rid: str) -> str:
        return self.votes.get(rid, "")

    @gl.public.view
    def get_stats(self, addr: str) -> str:
        return self.stats.get(addr, "0,0")

    @gl.public.view
    def get_count(self) -> u32:
        return self.game_count
    
    @gl.public.view
    def get_room_ids(self) -> str:
        return self.room_ids
    
    @gl.public.view
    def get_waiting_rooms(self) -> str:
        """Returns waiting rooms as: rid1:creator1:art1:time1;;rid2:creator2:art2:time2"""
        if not self.room_ids:
            return ""
        
        result = []
        for rid in self.room_ids.split(","):
            room = self.rooms.get(rid, "")
            if room:
                parts = room.split(",")
                # phase 0 = waiting
                if parts[0] == "0":
                    plist = self.players.get(rid, "")
                    pcount = plist.count(",") + 1 if plist else 0
                    # rid:creator:art_id:create_time:player_count
                    result.append(f"{rid}:{parts[1]}:{parts[2]}:{parts[3]}:{pcount}")
        
        return ";;".join(result)
