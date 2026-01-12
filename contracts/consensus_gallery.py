# { "Depends": "py-genlayer:test" }
"""
Consensus Gallery - GenLayer Intelligent Contract
Multi-round art description game with player IDs and self-voting
"""

from genlayer import *
from dataclasses import dataclass

MAX_PLAYERS = 5
MIN_PLAYERS = 2
ENTRY_FEE = 100000000000000
ROOM_TIMEOUT = 300
MIN_GAME_DURATION = 300
MAX_GAME_DURATION = 900
VOTE_DURATION = 30
WINNER_EXP = 100
CORRECT_VOTER_EXP = 30
PARTICIPANT_EXP = 10

ADJECTIVES = ["Swift", "Brave", "Wise", "Noble", "Silent", "Golden", "Silver", "Cosmic", "Mystic", "Ancient"]
NOUNS = ["Phoenix", "Dragon", "Tiger", "Eagle", "Wolf", "Hawk", "Lion", "Bear", "Serpent", "Falcon"]


@allow_storage
@dataclass
class Message:
    author: str
    content: str
    timestamp: u64


@allow_storage
@dataclass
class PlayerStats:
    experience: u64
    wins: u32
    participations: u32
    player_id: str


@allow_storage
@dataclass
class Room:
    id: str
    game_number: u32
    creator: str
    phase: u8
    art_id: u32
    max_players: u8
    start_time: u64
    vote_deadline: u64
    winner: str
    locked: bool
    created_at: u64


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


class ConsensusGallery(gl.Contract):
    owner: Address
    treasury: Address
    total_games: u32
    
    rooms: TreeMap[str, Room]
    room_players: TreeMap[str, DynArray[str]]
    room_messages: TreeMap[str, DynArray[Message]]
    room_votes: TreeMap[str, TreeMap[str, str]]
    room_end_votes: TreeMap[str, DynArray[str]]
    
    leaderboard: TreeMap[str, PlayerStats]
    player_ids: TreeMap[str, str]
    history: DynArray[GameHistory]

    def __init__(self, treasury_address: str):
        self.owner = gl.message.sender_address
        self.treasury = Address(treasury_address)
        self.total_games = u32(0)

    def _generate_player_id(self, address: str) -> str:
        hash_val = 0
        for c in address:
            hash_val = hash_val + ord(c)
        adj = ADJECTIVES[hash_val % len(ADJECTIVES)]
        noun = NOUNS[(hash_val * 7) % len(NOUNS)]
        num = (hash_val % 99) + 1
        return f"{adj}{noun}{num}"

    def _get_player_id(self, address: str) -> str:
        existing = self.player_ids.get(address, None)
        if existing is not None:
            return existing
        new_id = self._generate_player_id(address)
        self.player_ids[address] = new_id
        return new_id

    def _verify_payment(self) -> bool:
        return gl.message.value >= ENTRY_FEE

    def _ensure_player(self, address: str) -> None:
        if self.leaderboard.get(address, None) is None:
            self.leaderboard[address] = PlayerStats(
                experience=u64(0),
                wins=u32(0),
                participations=u32(0),
                player_id=self._get_player_id(address)
            )

    @gl.public.write
    def create_room(self) -> str:
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
            created_at=u64(gl.block.timestamp)
        )
        
        players: DynArray[str] = DynArray()
        players.append(sender)
        self.room_players[room_id] = players
        
        messages: DynArray[Message] = DynArray()
        self.room_messages[room_id] = messages
        
        end_votes: DynArray[str] = DynArray()
        self.room_end_votes[room_id] = end_votes
        
        self._get_player_id(sender)
        return room_id

    @gl.public.write
    def join_room(self, room_id: str) -> str:
        assert self._verify_payment(), "Insufficient payment"
        
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(0), "Game started"
        assert not room.locked, "Room locked"
        
        players = self.room_players.get(room_id, DynArray())
        assert len(players) < int(room.max_players), "Room full"
        
        for i in range(len(players)):
            if players[i] == sender:
                return "Already joined"
        
        players.append(sender)
        self.room_players[room_id] = players
        self._get_player_id(sender)
        
        return f"Joined {room_id}"

    @gl.public.write
    def start_game(self, room_id: str) -> str:
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(0), "Game started"
        assert room.creator == sender, "Not creator"
        
        players = self.room_players.get(room_id, DynArray())
        assert len(players) >= MIN_PLAYERS, "Need more players"
        
        room.phase = u8(1)
        room.locked = True
        room.start_time = u64(gl.block.timestamp)
        self.rooms[room_id] = room
        
        return "Started"

    @gl.public.write
    def send_message(self, room_id: str, content: str) -> str:
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(1), "Not playing"
        
        players = self.room_players.get(room_id, DynArray())
        is_player = False
        for i in range(len(players)):
            if players[i] == sender:
                is_player = True
                break
        assert is_player, "Not in room"
        
        messages = self.room_messages.get(room_id, DynArray())
        
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
        
        messages.append(Message(
            author=sender,
            content=content,
            timestamp=u64(gl.block.timestamp)
        ))
        self.room_messages[room_id] = messages
        
        return "Sent"

    @gl.public.write
    def vote_end_game(self, room_id: str) -> str:
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(1), "Not playing"
        
        elapsed = gl.block.timestamp - room.start_time
        assert elapsed >= MIN_GAME_DURATION, "Too early"
        
        end_votes = self.room_end_votes.get(room_id, DynArray())
        for i in range(len(end_votes)):
            if end_votes[i] == sender:
                return "Already voted"
        
        end_votes.append(sender)
        self.room_end_votes[room_id] = end_votes
        
        players = self.room_players.get(room_id, DynArray())
        threshold = (len(players) + 1) // 2
        
        if len(end_votes) >= threshold:
            room.phase = u8(2)
            room.vote_deadline = u64(gl.block.timestamp + VOTE_DURATION)
            self.rooms[room_id] = room
            return "Voting started"
        
        return "Vote recorded"

    @gl.public.write
    def vote(self, room_id: str, target: str) -> str:
        sender = gl.message.sender_address.as_hex
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(2), "Not voting"
        
        votes = self.room_votes.get(room_id, TreeMap())
        assert votes.get(sender, None) is None, "Already voted"
        
        votes[sender] = target
        self.room_votes[room_id] = votes
        
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
        
        return "Voted"

    @gl.public.write
    def finalize_game(self, room_id: str) -> str:
        room = self.rooms.get(room_id, None)
        assert room is not None, "Room not found"
        assert room.phase == u8(2), "Not voting"
        
        self._finalize_game(room_id)
        return "Finalized"

    def _finalize_game(self, room_id: str) -> None:
        room = self.rooms[room_id]
        if room.phase == u8(3):
            return
        
        messages = self.room_messages.get(room_id, DynArray())
        votes = self.room_votes.get(room_id, TreeMap())
        players = self.room_players.get(room_id, DynArray())
        
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
            return
        
        vote_count: TreeMap[str, u32] = TreeMap()
        for i in range(len(authors)):
            vote_count[authors[i]] = u32(0)
        
        for i in range(len(authors)):
            v = votes.get(authors[i], "")
            if v != "" and vote_count.get(v, None) is not None:
                vote_count[v] = u32(vote_count[v] + 1)
        
        winner = authors[0] if len(authors) > 0 else ""
        max_votes = u32(0)
        for i in range(len(authors)):
            if vote_count[authors[i]] > max_votes:
                max_votes = vote_count[authors[i]]
                winner = authors[i]
        
        self._ensure_player(winner)
        stats = self.leaderboard[winner]
        stats.experience = u64(stats.experience + WINNER_EXP)
        stats.wins = u32(stats.wins + 1)
        self.leaderboard[winner] = stats
        
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
            timestamp=u64(gl.block.timestamp)
        ))
        
        room.phase = u8(3)
        room.winner = winner
        self.rooms[room_id] = room

    @gl.public.view
    def get_room(self, room_id: str) -> TreeMap[str, str]:
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
            "winner": room.winner
        }

    @gl.public.view
    def get_player_id(self, address: str) -> str:
        return self.player_ids.get(address, "")

    @gl.public.view
    def get_player_stats(self, address: str) -> TreeMap[str, str]:
        stats = self.leaderboard.get(address, None)
        if stats is None:
            return {"experience": "0", "wins": "0", "participations": "0", "player_id": ""}
        return {
            "experience": str(stats.experience),
            "wins": str(stats.wins),
            "participations": str(stats.participations),
            "player_id": stats.player_id
        }
