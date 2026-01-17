# { "Depends": "py-genlayer:test" }
"""
Consensus Gallery - Online Multiplayer Version for GenLayer
All game data stored on-chain for true multiplayer experience
"""

from genlayer import *

# Game constants
MAX_PLAYERS = 5
MIN_PLAYERS = 2
WINNER_EXP = 100
CORRECT_VOTER_EXP = 30
PARTICIPANT_EXP = 10


class ConsensusGallery(gl.Contract):
    owner: str
    game_count: u32
    
    # Room data: room_id -> "phase,creator,art_id,create_time,start_time,winner"
    # phase: 0=waiting, 1=playing, 2=voting, 3=finished
    rooms: TreeMap[str, str]
    
    # Players: room_id -> "addr1,addr2,addr3"
    players: TreeMap[str, str]
    
    # Messages: room_id -> "author|msg|time;;author|msg|time"
    messages: TreeMap[str, str]
    
    # Votes: room_id -> "voter:target;;voter:target"
    votes: TreeMap[str, str]
    
    # End game votes: room_id -> "addr1,addr2"
    end_votes: TreeMap[str, str]
    
    # Player stats: address -> "exp,wins,participations"
    stats: TreeMap[str, str]
    
    # Player IDs: address -> "PlayerId"
    player_ids: TreeMap[str, str]
    
    # Game history: "rid1:winner1:art1:time1;;rid2:winner2:art2:time2" (last 50)
    history: str
    
    # Active room IDs (comma separated)
    room_ids: str

    def __init__(self):
        self.owner = gl.message.sender_address.as_hex
        self.game_count = u32(0)
        self.room_ids = ""
        self.history = ""

    def _generate_player_id(self, address: str) -> str:
        """Generate a unique player ID from address"""
        adjs = ["Swift", "Brave", "Wise", "Noble", "Silent", "Golden", "Silver", "Cosmic", "Mystic", "Ancient"]
        nouns = ["Phoenix", "Dragon", "Tiger", "Eagle", "Wolf", "Hawk", "Lion", "Bear", "Serpent", "Falcon"]
        
        hash_val = 0
        for c in address:
            hash_val = hash_val + ord(c)
        
        adj = adjs[hash_val % 10]
        noun = nouns[(hash_val * 7) % 10]
        num = (hash_val % 99) + 1
        return f"{adj}{noun}{num}"

    def _get_player_id(self, address: str) -> str:
        """Get or create player ID"""
        if address.startswith("AI_"):
            return "ArtBot_" + address[3:]
        existing = self.player_ids.get(address, "")
        if existing:
            return existing
        new_id = self._generate_player_id(address)
        self.player_ids[address] = new_id
        return new_id

    def _ensure_stats(self, address: str) -> None:
        """Ensure player has stats entry"""
        if not self.stats.get(address, ""):
            self.stats[address] = "0,0,0"

    @gl.public.write
    def create_room(self) -> str:
        """Create a new game room"""
        sender = gl.message.sender_address.as_hex
        self.game_count = u32(self.game_count + 1)
        rid = f"r{self.game_count}"
        art = (gl.block.timestamp % 8) + 1
        create_time = gl.block.timestamp
        
        # phase,creator,art_id,create_time,start_time,winner
        self.rooms[rid] = f"0,{sender},{art},{create_time},0,"
        self.players[rid] = sender
        self.messages[rid] = ""
        self.votes[rid] = ""
        self.end_votes[rid] = ""
        
        # Ensure player ID exists
        self._get_player_id(sender)
        
        # Add to active room list
        if self.room_ids:
            self.room_ids = self.room_ids + "," + rid
        else:
            self.room_ids = rid
        
        return rid

    @gl.public.write
    def join_room(self, rid: str) -> str:
        """Join an existing room"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[0] != "0":
            return "STARTED"
        
        plist = self.players.get(rid, "")
        if sender in plist:
            return "ALREADY_JOINED"
        if plist.count(",") >= MAX_PLAYERS - 1:
            return "FULL"
        
        self.players[rid] = plist + "," + sender
        self._get_player_id(sender)
        return "OK"

    @gl.public.write
    def add_ai_player(self, rid: str) -> str:
        """Add AI player (called by creator after timeout)"""
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
        ai_addr = "AI_" + rid
        if ai_addr in plist:
            return "AI_EXISTS"
        
        self.players[rid] = plist + "," + ai_addr
        return "OK"

    @gl.public.write
    def start_game(self, rid: str) -> str:
        """Start the game (creator only)"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[1] != sender:
            return "NOT_CREATOR"
        if parts[0] != "0":
            return "ALREADY_STARTED"
        
        plist = self.players.get(rid, "")
        if plist.count(",") < MIN_PLAYERS - 1:
            return "NEED_PLAYERS"
        
        parts[0] = "1"
        parts[4] = str(gl.block.timestamp)
        self.rooms[rid] = ",".join(parts)
        return "OK"

    @gl.public.write
    def send_msg(self, rid: str, msg: str) -> str:
        """Send a message/description"""
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
    def ai_send_msg(self, rid: str, msg: str) -> str:
        """AI sends message (creator calls on behalf of AI)"""
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
    def vote_end_game(self, rid: str) -> str:
        """Vote to end the game early"""
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
        
        evotes = self.end_votes.get(rid, "")
        if sender in evotes:
            return "ALREADY_VOTED"
        
        if evotes:
            evotes = evotes + "," + sender
        else:
            evotes = sender
        self.end_votes[rid] = evotes
        
        # Check if majority wants to end
        player_count = plist.count(",") + 1
        vote_count = evotes.count(",") + 1
        threshold = (player_count + 1) // 2
        
        if vote_count >= threshold:
            parts[0] = "2"
            self.rooms[rid] = ",".join(parts)
            return "VOTING_STARTED"
        
        return f"VOTE_RECORDED:{vote_count}/{threshold}"

    @gl.public.write
    def start_voting(self, rid: str) -> str:
        """Force start voting phase"""
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
        """Vote for best description"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[0] != "2":
            return "NOT_VOTING"
        
        cur = self.votes.get(rid, "")
        if sender in cur:
            return "ALREADY_VOTED"
        
        entry = f"{sender}:{target}"
        self.votes[rid] = cur + ";;" + entry if cur else entry
        return "OK"

    @gl.public.write
    def ai_vote(self, rid: str, target: str) -> str:
        """AI votes (creator calls on behalf of AI)"""
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
            return "ALREADY_VOTED"
        
        entry = f"{ai_addr}:{target}"
        self.votes[rid] = cur + ";;" + entry if cur else entry
        return "OK"

    @gl.public.write
    def finish_game(self, rid: str) -> str:
        """Finalize game and calculate winner"""
        room = self.rooms.get(rid, "")
        if not room:
            return "NO_ROOM"
        
        parts = room.split(",")
        if parts[0] == "3":
            return "ALREADY_FINISHED"
        if parts[0] != "2":
            return "NOT_VOTING"
        
        # Count votes
        vstr = self.votes.get(rid, "")
        counts = {}
        voters = {}
        if vstr:
            for v in vstr.split(";;"):
                if ":" in v:
                    voter, target = v.split(":")
                    counts[target] = counts.get(target, 0) + 1
                    voters[voter] = target
        
        # Find winner
        winner = ""
        max_votes = 0
        for addr, cnt in counts.items():
            if cnt > max_votes:
                max_votes = cnt
                winner = addr
        
        # Get all message authors
        msgs = self.messages.get(rid, "")
        authors = []
        if msgs:
            for m in msgs.split(";;"):
                if "|" in m:
                    author = m.split("|")[0]
                    if author not in authors:
                        authors.append(author)
        
        # Update stats for all participants
        for author in authors:
            if author.startswith("AI_"):
                continue
            self._ensure_stats(author)
            st = self.stats.get(author, "0,0,0")
            sp = st.split(",")
            exp = int(sp[0])
            wins = int(sp[1])
            parts_count = int(sp[2])
            
            if author == winner:
                exp += WINNER_EXP
                wins += 1
            elif voters.get(author, "") == winner:
                exp += CORRECT_VOTER_EXP
            else:
                exp += PARTICIPANT_EXP
            
            parts_count += 1
            self.stats[author] = f"{exp},{wins},{parts_count}"
        
        # Update room
        parts[0] = "3"
        parts[5] = winner
        self.rooms[rid] = ",".join(parts)
        
        # Add to history
        art_id = parts[2]
        timestamp = gl.block.timestamp
        entry = f"{rid}:{winner}:{art_id}:{timestamp}"
        if self.history:
            # Keep last 50 games
            hist_list = self.history.split(";;")
            if len(hist_list) >= 50:
                hist_list = hist_list[-49:]
            hist_list.append(entry)
            self.history = ";;".join(hist_list)
        else:
            self.history = entry
        
        return winner if winner else "NO_WINNER"

    # ===== VIEW METHODS =====
    
    @gl.public.view
    def get_room(self, rid: str) -> str:
        """Get room data: phase,creator,art_id,create_time,start_time,winner"""
        return self.rooms.get(rid, "")

    @gl.public.view
    def get_players(self, rid: str) -> str:
        """Get players: addr1,addr2,addr3"""
        return self.players.get(rid, "")

    @gl.public.view
    def get_messages(self, rid: str) -> str:
        """Get messages: author|msg|time;;author|msg|time"""
        return self.messages.get(rid, "")

    @gl.public.view
    def get_votes(self, rid: str) -> str:
        """Get votes: voter:target;;voter:target"""
        return self.votes.get(rid, "")

    @gl.public.view
    def get_end_votes(self, rid: str) -> str:
        """Get end game votes: addr1,addr2"""
        return self.end_votes.get(rid, "")

    @gl.public.view
    def get_stats(self, addr: str) -> str:
        """Get player stats: exp,wins,participations"""
        return self.stats.get(addr, "0,0,0")

    @gl.public.view
    def get_player_id(self, addr: str) -> str:
        """Get player display name"""
        if addr.startswith("AI_"):
            return "ArtBot_" + addr[3:]
        return self.player_ids.get(addr, "")

    @gl.public.view
    def get_game_count(self) -> u32:
        """Get total games created"""
        return self.game_count

    @gl.public.view
    def get_waiting_rooms(self) -> str:
        """Get all waiting rooms: rid:creator:art:time:players;;..."""
        if not self.room_ids:
            return ""
        
        result = []
        for rid in self.room_ids.split(","):
            room = self.rooms.get(rid, "")
            if room:
                parts = room.split(",")
                if parts[0] == "0":  # waiting
                    plist = self.players.get(rid, "")
                    pcount = plist.count(",") + 1 if plist else 0
                    result.append(f"{rid}:{parts[1]}:{parts[2]}:{parts[3]}:{pcount}")
        
        return ";;".join(result)

    @gl.public.view
    def get_active_rooms(self) -> str:
        """Get all non-finished rooms: rid:phase:creator:art:players;;..."""
        if not self.room_ids:
            return ""
        
        result = []
        for rid in self.room_ids.split(","):
            room = self.rooms.get(rid, "")
            if room:
                parts = room.split(",")
                if parts[0] != "3":  # not finished
                    plist = self.players.get(rid, "")
                    pcount = plist.count(",") + 1 if plist else 0
                    result.append(f"{rid}:{parts[0]}:{parts[1]}:{parts[2]}:{pcount}")
        
        return ";;".join(result)

    @gl.public.view
    def get_history(self) -> str:
        """Get game history: rid:winner:art:time;;..."""
        return self.history

    @gl.public.view
    def get_leaderboard(self) -> str:
        """Get top players: addr:exp:wins:parts;;..."""
        # Note: This is a simplified version - in production you'd want pagination
        if not self.room_ids:
            return ""
        
        # Collect all unique players from history
        players = []
        if self.history:
            for entry in self.history.split(";;"):
                if ":" in entry:
                    winner = entry.split(":")[1]
                    if winner and winner not in players and not winner.startswith("AI_"):
                        players.append(winner)
        
        # Get stats for each player
        result = []
        for addr in players:
            stats = self.stats.get(addr, "0,0,0")
            pid = self.player_ids.get(addr, "")
            result.append(f"{addr}:{pid}:{stats}")
        
        # Sort by experience (descending)
        result.sort(key=lambda x: -int(x.split(":")[2].split(",")[0]) if len(x.split(":")) > 2 else 0)
        
        return ";;".join(result[:20])  # Top 20
