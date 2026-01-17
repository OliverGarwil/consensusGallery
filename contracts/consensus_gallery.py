# { "Depends": "py-genlayer:test" }
"""
Consensus Gallery - GenLayer Intelligent Contract
Multi-player Art Description Game with Real-time Multiplayer Support
Supports multiple players joining the same game on-chain
"""

from genlayer import *
from dataclasses import dataclass

# Game Configuration
MAX_PLAYERS = 5
MIN_PLAYERS = 2
ENTRY_FEE = u256(100000000000000)  # 0.0001 GEN
ROOM_TIMEOUT = 300  # 5 minutes
MIN_GAME_DURATION = 60  # 1 minute minimum
MAX_GAME_DURATION = 300  # 5 minutes max
VOTE_DURATION = 60  # 1 minute voting

# Experience Points
WINNER_EXP = u64(100)
CORRECT_VOTER_EXP = u64(30)
PARTICIPANT_EXP = u64(10)

# Player ID Generation
ADJECTIVES = ["Swift", "Brave", "Wise", "Noble", "Silent", "Golden", "Silver", "Cosmic", "Mystic", "Ancient"]
NOUNS = ["Phoenix", "Dragon", "Tiger", "Eagle", "Wolf", "Hawk", "Lion", "Bear", "Serpent", "Falcon"]


@allow_storage
@dataclass
class Message:
    id: u64
    author: str
    content: str
    timestamp: u64


@allow_storage
@dataclass
class PlayerStats:
    experience: u64
    wins: u32
    participations: u32
    total_rewards: u256
    player_id: str


@allow_storage
@dataclass
class Room:
    id: str
    game_number: u32
    creator: str
    phase: u8  # 0=waiting, 1=playing, 2=voting, 3=finished
    art_id: u32
    max_players: u8
    start_time: u64
    vote_deadline: u64
    winner: str
    locked: bool
    created_at: u64
    pool: u256


@allow_storage
@dataclass
class GameHistory:
    room_id: str
    game_number: u32
    art_id: u32
    winner: str
    winner_votes: u32
    total_players: u8
    total_messages: u32
    duration: u32
    timestamp: u64
    prize: u256


class ConsensusGallery(gl.Contract):
    owner: Address
    treasury: Address
    total_games: u32
    message_counter: u64
    
    # Room data
    rooms: TreeMap[str, Room]
    room_players: TreeMap[str, DynArray[str]]
    room_messages: TreeMap[str, DynArray[Message]]
    room_votes: TreeMap[str, TreeMap[str, str]]
    room_end_votes: TreeMap[str, DynArray[str]]
    
    # Active rooms list for discovery
    active_room_ids: DynArray[str]
    
    # Player data
    leaderboard: TreeMap[str, PlayerStats]
    player_ids: TreeMap[str, str]
    
    # History
    history: DynArray[GameHistory]

    def __init__(self, treasury_address: str):
        self.owner = gl.message.sender_address
        self.treasury = Address(treasury_address)
        self.total_games = u32(0)
        self.message_counter = u64(0)

    def _generate_player_id(self, address: str) -> str:
        """Generate a unique player ID based on address"""
        hash_val = 0
        for c in address:
            hash_val = hash_val + ord(c)
        adj = ADJECTIVES[hash_val % len(ADJECTIVES)]
        noun = NOUNS[(hash_val * 7) % len(NOUNS)]
        num = (hash_val % 99) + 1
        return f"{adj}{noun}{num}"

    def _get_player_id(self, address: str) -> str:
        """Get or create player ID"""
        existing = self.player_ids.get(address, None)
        if existing is not None:
            return existing
        new_id = self._generate_player_id(address)
        self.player_ids[address] = new_id
        return new_id

    def _verify_payment(self) -> bool:
        """Verify entry fee payment"""
        return gl.message.value >= ENTRY_FEE

    def _ensure_player(self, address: str) -> None:
        """Ensure player stats exist"""
        if self.leaderboard.get(address, None) is None:
            self.leaderboard[address] = PlayerStats(
                experience=u64(0),
                wins=u32(0),
                participations=u32(0),
                total_rewards=u256(0),
                player_id=self._get_player_id(address)
            )

    def _add_active_room(self, room_id: str) -> None:
        """Add room to active list"""
        self.active_room_ids.append(room_id)

    def _remove_active_room(self, room_id: str) -> None:
        """Remove room from active list"""
        new_list: DynArray[str] = DynArray()
        for i in range(len(self.active_room_ids)):
            if self.active_room_ids[i] != room_id:
                new_list.append(self.active_room_ids[i])
        self.active_room_ids = new_list

    @gl.public.write.payable
    def create_room(self) -> str:
        """Create a new game room"""
        assert self._verify_payment(), "Insufficient payment"
        
        sender = gl.message.sender_address.as_hex
        self.total_games = u32(self.total_games + 1)
        room_id = f"room_{gl.block.timestamp}_{sender[:8]}"
        art_id = u32((gl.block.timestamp % 15) + 1)
        
        self.rooms[room_id] = Room(
            id=room_id,
            game_number=self.total_games,
            creator=sender,
            phase=u8(0),
            art_id=art_id,
            max_players=u8(MAX_PLAYERS),
            start_time=u64(0),
            vote_deadline=u64(0),
            winner="",
            locked=False,
            created_at=u64(gl.block.timestamp),
            pool=gl.message.value
        )
        
        players: DynArray[str] = DynArray()
        players.append(sender)
        self.room_players[room_id] = players
        
        messages: DynArray[Message] = DynArray()
        self.room_messages[room_id] = messages
        
        end_votes: DynArray[str] = DynArray()
        self.room_end_votes[room_id] = end_votes
        
        self._get_player_id(sender)
        self._add_active_room(room_id)
        
        return room_id

    @gl.public.write.payable
    def join_room(self, room_id: str) -> str:
        """Join an existing game room"""
        assert self._verify_payment(), "Insufficient payment"
        
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(0), "Game already started"
        assert not room.locked, "Room is locked"
        
        players = self.room_players.get(room_id, DynArray())
        assert len(players) < int(room.max_players), "Room is full"
        
        for i in range(len(players)):
            if players[i] == sender:
                return "Already joined"
        
        players.append(sender)
        self.room_players[room_id] = players
        
        # Update pool
        room.pool = u256(room.pool + gl.message.value)
        self.rooms[room_id] = room
        
        self._get_player_id(sender)
        
        return f"Joined {room_id}"

    @gl.public.write
    def start_game(self, room_id: str) -> str:
        """Start the game (creator only)"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(0), "Game already started"
        assert room.creator == sender, "Only creator can start"
        
        players = self.room_players.get(room_id, DynArray())
        assert len(players) >= MIN_PLAYERS, "Need at least 2 players"
        
        room.phase = u8(1)
        room.locked = True
        room.start_time = u64(gl.block.timestamp)
        self.rooms[room_id] = room
        
        return "Game started"

    @gl.public.write
    def send_message(self, room_id: str, content: str) -> str:
        """Send a message (art description) during the game"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(1), "Game not in playing phase"
        
        players = self.room_players.get(room_id, DynArray())
        is_player = False
        for i in range(len(players)):
            if players[i] == sender:
                is_player = True
                break
        assert is_player, "Not in this room"
        
        messages = self.room_messages.get(room_id, DynArray())
        
        # Track participation
        has_messaged = False
        for i in range(len(messages)):
            if messages[i].author == sender:
                has_messaged = True
                break
        
        if not has_messaged:
            self._ensure_player(sender)
            stats = self.leaderboard[sender]
            stats.participations = u32(stats.participations + 1)
            self.leaderboard[sender] = stats
        
        self.message_counter = u64(self.message_counter + 1)
        messages.append(Message(
            id=self.message_counter,
            author=sender,
            content=content,
            timestamp=u64(gl.block.timestamp)
        ))
        self.room_messages[room_id] = messages
        
        return "Message sent"

    @gl.public.write
    def vote_end_game(self, room_id: str) -> str:
        """Vote to end the game early"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(1), "Game not in playing phase"
        
        elapsed = gl.block.timestamp - room.start_time
        assert elapsed >= MIN_GAME_DURATION, "Minimum game duration not reached"
        
        end_votes = self.room_end_votes.get(room_id, DynArray())
        for i in range(len(end_votes)):
            if end_votes[i] == sender:
                return "Already voted to end"
        
        end_votes.append(sender)
        self.room_end_votes[room_id] = end_votes
        
        players = self.room_players.get(room_id, DynArray())
        threshold = (len(players) + 1) // 2
        
        if len(end_votes) >= threshold:
            room.phase = u8(2)
            room.vote_deadline = u64(gl.block.timestamp + VOTE_DURATION)
            self.rooms[room_id] = room
            return "Voting phase started"
        
        return "End vote recorded"

    @gl.public.write
    def force_end_game(self, room_id: str) -> str:
        """Force end game after max duration"""
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(1), "Game not in playing phase"
        
        elapsed = gl.block.timestamp - room.start_time
        assert elapsed >= MAX_GAME_DURATION, "Max duration not reached"
        
        room.phase = u8(2)
        room.vote_deadline = u64(gl.block.timestamp + VOTE_DURATION)
        self.rooms[room_id] = room
        
        return "Voting phase started"

    @gl.public.write
    def vote(self, room_id: str, target: str) -> str:
        """Vote for the best description"""
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(2), "Not in voting phase"
        
        votes = self.room_votes.get(room_id, TreeMap())
        assert votes.get(sender, None) is None, "Already voted"
        
        votes[sender] = target
        self.room_votes[room_id] = votes
        
        # Check if all participants have voted
        messages = self.room_messages.get(room_id, DynArray())
        authors: DynArray[str] = DynArray()
        for i in range(len(messages)):
            author = messages[i].author
            is_new = True
            for j in range(len(authors)):
                if authors[j] == author:
                    is_new = False
                    break
            if is_new:
                authors.append(author)
        
        all_voted = True
        for i in range(len(authors)):
            if votes.get(authors[i], None) is None:
                all_voted = False
                break
        
        if all_voted:
            self._finalize_game(room_id)
        
        return "Vote recorded"

    @gl.public.write
    def finalize_game(self, room_id: str) -> str:
        """Finalize the game after voting deadline"""
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(2), "Not in voting phase"
        assert gl.block.timestamp >= room.vote_deadline, "Voting still in progress"
        
        self._finalize_game(room_id)
        return "Game finalized"

    def _finalize_game(self, room_id: str) -> None:
        """Internal: Finalize game and distribute rewards"""
        room = self.rooms[room_id]
        if room.phase == u8(3):
            return
        
        messages = self.room_messages.get(room_id, DynArray())
        votes = self.room_votes.get(room_id, TreeMap())
        players = self.room_players.get(room_id, DynArray())
        
        # Get unique authors
        authors: DynArray[str] = DynArray()
        for i in range(len(messages)):
            author = messages[i].author
            is_new = True
            for j in range(len(authors)):
                if authors[j] == author:
                    is_new = False
                    break
            if is_new:
                authors.append(author)
        
        if len(authors) == 0:
            room.phase = u8(3)
            self.rooms[room_id] = room
            self._remove_active_room(room_id)
            return
        
        # Count votes
        vote_count: TreeMap[str, u32] = TreeMap()
        for i in range(len(authors)):
            vote_count[authors[i]] = u32(0)
        
        for i in range(len(authors)):
            v = votes.get(authors[i], "")
            if v != "" and vote_count.get(v, None) is not None:
                vote_count[v] = u32(vote_count[v] + 1)
        
        # Find winner
        winner = authors[0] if len(authors) > 0 else ""
        max_votes = u32(0)
        for i in range(len(authors)):
            if vote_count[authors[i]] > max_votes:
                max_votes = vote_count[authors[i]]
                winner = authors[i]
        
        # Calculate prize (80% of pool)
        prize = u256(room.pool * 80 // 100)
        
        # Award winner
        self._ensure_player(winner)
        stats = self.leaderboard[winner]
        stats.experience = u64(stats.experience + WINNER_EXP)
        stats.wins = u32(stats.wins + 1)
        stats.total_rewards = u256(stats.total_rewards + prize)
        self.leaderboard[winner] = stats
        
        # Award voters
        for i in range(len(authors)):
            addr = authors[i]
            if addr == winner:
                continue
            v = votes.get(addr, "")
            self._ensure_player(addr)
            s = self.leaderboard[addr]
            if v == winner:
                s.experience = u64(s.experience + CORRECT_VOTER_EXP)
            else:
                s.experience = u64(s.experience + PARTICIPANT_EXP)
            self.leaderboard[addr] = s
        
        # Record history
        duration = u32(gl.block.timestamp - room.start_time)
        self.history.append(GameHistory(
            room_id=room_id,
            game_number=room.game_number,
            art_id=room.art_id,
            winner=winner,
            winner_votes=max_votes,
            total_players=u8(len(players)),
            total_messages=u32(len(messages)),
            duration=duration,
            timestamp=u64(gl.block.timestamp),
            prize=prize
        ))
        
        # Update room
        room.phase = u8(3)
        room.winner = winner
        self.rooms[room_id] = room
        self._remove_active_room(room_id)
        
        # Transfer prize to winner (in real deployment)
        # gl.transfer(Address(winner), prize)

    # ==================== View Functions ====================

    @gl.public.view
    def get_room(self, room_id: str) -> TreeMap[str, str]:
        """Get room details"""
        room = self.rooms.get(room_id, None)
        if room is None:
            return {}
        
        players = self.room_players.get(room_id, DynArray())
        messages = self.room_messages.get(room_id, DynArray())
        phases = ["waiting", "playing", "voting", "finished"]
        
        return {
            "id": room.id,
            "game_number": str(room.game_number),
            "creator": room.creator,
            "phase": phases[int(room.phase)],
            "art_id": str(room.art_id),
            "player_count": str(len(players)),
            "message_count": str(len(messages)),
            "winner": room.winner,
            "start_time": str(room.start_time),
            "vote_deadline": str(room.vote_deadline),
            "pool": str(room.pool),
            "created_at": str(room.created_at)
        }

    @gl.public.view
    def get_room_players(self, room_id: str) -> DynArray[str]:
        """Get list of players in a room"""
        return self.room_players.get(room_id, DynArray())

    @gl.public.view
    def get_room_messages(self, room_id: str) -> TreeMap[str, str]:
        """Get messages as JSON-like structure"""
        messages = self.room_messages.get(room_id, DynArray())
        result: TreeMap[str, str] = TreeMap()
        
        for i in range(len(messages)):
            m = messages[i]
            key = f"msg_{i}"
            result[f"{key}_id"] = str(m.id)
            result[f"{key}_author"] = m.author
            result[f"{key}_content"] = m.content
            result[f"{key}_timestamp"] = str(m.timestamp)
        
        result["count"] = str(len(messages))
        return result

    @gl.public.view
    def get_room_votes(self, room_id: str) -> TreeMap[str, str]:
        """Get votes for a room"""
        votes = self.room_votes.get(room_id, TreeMap())
        result: TreeMap[str, str] = TreeMap()
        
        messages = self.room_messages.get(room_id, DynArray())
        authors: DynArray[str] = DynArray()
        for i in range(len(messages)):
            author = messages[i].author
            is_new = True
            for j in range(len(authors)):
                if authors[j] == author:
                    is_new = False
                    break
            if is_new:
                authors.append(author)
        
        for i in range(len(authors)):
            addr = authors[i]
            vote = votes.get(addr, "")
            if vote != "":
                result[addr] = vote
        
        return result

    @gl.public.view
    def get_active_rooms(self) -> DynArray[str]:
        """Get list of active room IDs"""
        return self.active_room_ids

    @gl.public.view
    def get_player_id(self, address: str) -> str:
        """Get player ID for an address"""
        return self.player_ids.get(address, "")

    @gl.public.view
    def get_player_stats(self, address: str) -> TreeMap[str, str]:
        """Get player statistics"""
        stats = self.leaderboard.get(address, None)
        if stats is None:
            return {
                "experience": "0",
                "wins": "0",
                "participations": "0",
                "total_rewards": "0",
                "player_id": ""
            }
        return {
            "experience": str(stats.experience),
            "wins": str(stats.wins),
            "participations": str(stats.participations),
            "total_rewards": str(stats.total_rewards),
            "player_id": stats.player_id
        }

    @gl.public.view
    def get_leaderboard_top(self, limit: u32) -> TreeMap[str, str]:
        """Get top players (simplified - returns addresses)"""
        # Note: In production, you'd want proper sorting
        # This is a simplified version
        result: TreeMap[str, str] = TreeMap()
        result["note"] = "Use client-side sorting for full leaderboard"
        return result

    @gl.public.view
    def get_game_history(self, limit: u32) -> TreeMap[str, str]:
        """Get recent game history"""
        result: TreeMap[str, str] = TreeMap()
        count = min(int(limit), len(self.history))
        
        for i in range(count):
            idx = len(self.history) - 1 - i
            if idx < 0:
                break
            h = self.history[idx]
            prefix = f"game_{i}"
            result[f"{prefix}_room_id"] = h.room_id
            result[f"{prefix}_game_number"] = str(h.game_number)
            result[f"{prefix}_art_id"] = str(h.art_id)
            result[f"{prefix}_winner"] = h.winner
            result[f"{prefix}_winner_votes"] = str(h.winner_votes)
            result[f"{prefix}_total_players"] = str(h.total_players)
            result[f"{prefix}_duration"] = str(h.duration)
            result[f"{prefix}_prize"] = str(h.prize)
        
        result["count"] = str(count)
        return result

    @gl.public.view
    def get_contract_info(self) -> TreeMap[str, str]:
        """Get contract configuration info"""
        return {
            "total_games": str(self.total_games),
            "max_players": str(MAX_PLAYERS),
            "min_players": str(MIN_PLAYERS),
            "entry_fee": str(ENTRY_FEE),
            "min_game_duration": str(MIN_GAME_DURATION),
            "max_game_duration": str(MAX_GAME_DURATION),
            "vote_duration": str(VOTE_DURATION),
            "winner_exp": str(WINNER_EXP),
            "correct_voter_exp": str(CORRECT_VOTER_EXP),
            "participant_exp": str(PARTICIPANT_EXP)
        }
