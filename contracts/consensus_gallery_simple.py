# { "Depends": "py-genlayer:test" }
"""
Consensus Gallery - Simplified Version
A lightweight multiplayer art game contract
"""

from genlayer import *


class ConsensusGallery(gl.Contract):
    # Basic state
    owner: str
    total_games: u32
    
    # Room data - using simple types
    room_phase: TreeMap[str, u8]  # 0=waiting, 1=playing, 2=voting, 3=finished
    room_creator: TreeMap[str, str]
    room_art: TreeMap[str, u32]
    room_start: TreeMap[str, u64]
    room_winner: TreeMap[str, str]
    
    # Players per room (comma-separated addresses)
    room_players: TreeMap[str, str]
    
    # Messages: room_id -> "author1|content1|time1;;author2|content2|time2"
    room_messages: TreeMap[str, str]
    
    # Votes: room_id -> "voter1:target1;;voter2:target2"
    room_votes: TreeMap[str, str]
    
    # Player stats
    player_exp: TreeMap[str, u64]
    player_wins: TreeMap[str, u32]

    def __init__(self):
        self.owner = gl.message.sender_address.as_hex
        self.total_games = u32(0)

    @gl.public.write
    def create_room(self) -> str:
        sender = gl.message.sender_address.as_hex
        self.total_games = u32(self.total_games + 1)
        room_id = f"r{gl.block.timestamp}"
        
        self.room_phase[room_id] = u8(0)
        self.room_creator[room_id] = sender
        self.room_art[room_id] = u32((gl.block.timestamp % 15) + 1)
        self.room_start[room_id] = u64(0)
        self.room_winner[room_id] = ""
        self.room_players[room_id] = sender
        self.room_messages[room_id] = ""
        self.room_votes[room_id] = ""
        
        return room_id

    @gl.public.write
    def join_room(self, room_id: str) -> str:
        sender = gl.message.sender_address.as_hex
        
        phase = self.room_phase.get(room_id, None)
        if phase is None:
            return "Room not found"
        if phase != u8(0):
            return "Game started"
        
        players = self.room_players.get(room_id, "")
        if sender in players:
            return "Already joined"
        
        player_list = players.split(",") if players else []
        if len(player_list) >= 5:
            return "Room full"
        
        self.room_players[room_id] = players + "," + sender if players else sender
        return "Joined"

    @gl.public.write
    def start_game(self, room_id: str) -> str:
        sender = gl.message.sender_address.as_hex
        
        if self.room_creator.get(room_id, "") != sender:
            return "Not creator"
        if self.room_phase.get(room_id, u8(0)) != u8(0):
            return "Already started"
        
        players = self.room_players.get(room_id, "")
        if len(players.split(",")) < 2:
            return "Need 2+ players"
        
        self.room_phase[room_id] = u8(1)
        self.room_start[room_id] = u64(gl.block.timestamp)
        return "Started"

    @gl.public.write
    def send_message(self, room_id: str, content: str) -> str:
        sender = gl.message.sender_address.as_hex
        
        if self.room_phase.get(room_id, u8(0)) != u8(1):
            return "Not playing"
        
        players = self.room_players.get(room_id, "")
        if sender not in players:
            return "Not in room"
        
        # Ensure player has exp entry
        if self.player_exp.get(sender, None) is None:
            self.player_exp[sender] = u64(0)
        
        messages = self.room_messages.get(room_id, "")
        new_msg = f"{sender}|{content}|{gl.block.timestamp}"
        self.room_messages[room_id] = messages + ";;" + new_msg if messages else new_msg
        
        return "Sent"

    @gl.public.write
    def start_voting(self, room_id: str) -> str:
        if self.room_phase.get(room_id, u8(0)) != u8(1):
            return "Not playing"
        
        self.room_phase[room_id] = u8(2)
        return "Voting started"

    @gl.public.write
    def vote(self, room_id: str, target: str) -> str:
        sender = gl.message.sender_address.as_hex
        
        if self.room_phase.get(room_id, u8(0)) != u8(2):
            return "Not voting"
        
        votes = self.room_votes.get(room_id, "")
        if sender in votes:
            return "Already voted"
        
        new_vote = f"{sender}:{target}"
        self.room_votes[room_id] = votes + ";;" + new_vote if votes else new_vote
        
        return "Voted"

    @gl.public.write
    def finalize(self, room_id: str) -> str:
        if self.room_phase.get(room_id, u8(0)) != u8(2):
            return "Not voting"
        
        # Count votes
        votes = self.room_votes.get(room_id, "")
        vote_count: TreeMap[str, u32] = TreeMap()
        
        if votes:
            for v in votes.split(";;"):
                if ":" in v:
                    parts = v.split(":")
                    target = parts[1] if len(parts) > 1 else ""
                    if target:
                        current = vote_count.get(target, u32(0))
                        vote_count[target] = u32(current + 1)
        
        # Find winner
        winner = ""
        max_votes = u32(0)
        players = self.room_players.get(room_id, "").split(",")
        
        for p in players:
            if p and vote_count.get(p, u32(0)) > max_votes:
                max_votes = vote_count[p]
                winner = p
        
        if not winner and players:
            winner = players[0]
        
        # Award XP
        if winner:
            current_exp = self.player_exp.get(winner, u64(0))
            self.player_exp[winner] = u64(current_exp + 100)
            
            current_wins = self.player_wins.get(winner, u32(0))
            self.player_wins[winner] = u32(current_wins + 1)
        
        self.room_winner[room_id] = winner
        self.room_phase[room_id] = u8(3)
        
        return f"Winner: {winner}"

    # View functions
    @gl.public.view
    def get_room(self, room_id: str) -> TreeMap[str, str]:
        phase = self.room_phase.get(room_id, None)
        if phase is None:
            return {}
        
        phases = ["waiting", "playing", "voting", "finished"]
        return {
            "id": room_id,
            "phase": phases[int(phase)],
            "creator": self.room_creator.get(room_id, ""),
            "art_id": str(self.room_art.get(room_id, u32(1))),
            "players": self.room_players.get(room_id, ""),
            "winner": self.room_winner.get(room_id, ""),
            "start_time": str(self.room_start.get(room_id, u64(0)))
        }

    @gl.public.view
    def get_messages(self, room_id: str) -> str:
        return self.room_messages.get(room_id, "")

    @gl.public.view
    def get_votes(self, room_id: str) -> str:
        return self.room_votes.get(room_id, "")

    @gl.public.view
    def get_stats(self, address: str) -> TreeMap[str, str]:
        return {
            "exp": str(self.player_exp.get(address, u64(0))),
            "wins": str(self.player_wins.get(address, u32(0)))
        }

    @gl.public.view
    def get_total_games(self) -> u32:
        return self.total_games
