/**
 * Consensus Gallery - Constants
 */

// Game Configuration
export const CONFIG = {
  MAX_PLAYERS: 5,
  MIN_PLAYERS: 2,
  ENTRY_FEE: '0.0001',
  ROOM_TIMEOUT: 5 * 60 * 1000, // 5 minutes
  MIN_GAME_DURATION: 5 * 60,   // 5 minutes
  MAX_GAME_DURATION: 15 * 60,  // 15 minutes
  VOTE_DURATION: 30,           // 30 seconds
  WINNER_EXP: 100,
  CORRECT_VOTER_EXP: 30,
  PARTICIPANT_EXP: 10,
};

// Classic Art Collection
export const ART_COLLECTION = [
  { id: 1, name: 'Starry Night', artist: 'Van Gogh', year: 1889, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1280px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg' },
  { id: 2, name: 'Persistence of Memory', artist: 'Dali', year: 1931, url: 'https://upload.wikimedia.org/wikipedia/en/d/dd/The_Persistence_of_Memory.jpg' },
  { id: 3, name: 'The Great Wave', artist: 'Hokusai', year: 1831, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Tsunami_by_hokusai_19th_century.jpg/1280px-Tsunami_by_hokusai_19th_century.jpg' },
  { id: 4, name: 'Girl with Pearl Earring', artist: 'Vermeer', year: 1665, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/1665_Girl_with_a_Pearl_Earring.jpg/800px-1665_Girl_with_a_Pearl_Earring.jpg' },
  { id: 5, name: 'The Scream', artist: 'Munch', year: 1893, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C_91_x_73_cm%2C_National_Gallery_of_Norway.jpg/800px-Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C_91_x_73_cm%2C_National_Gallery_of_Norway.jpg' },
  { id: 6, name: 'Birth of Venus', artist: 'Botticelli', year: 1485, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Sandro_Botticelli_-_La_nascita_di_Venere_-_Google_Art_Project_-_edited.jpg/1280px-Sandro_Botticelli_-_La_nascita_di_Venere_-_Google_Art_Project_-_edited.jpg' },
  { id: 7, name: 'American Gothic', artist: 'Wood', year: 1930, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cc/Grant_Wood_-_American_Gothic_-_Google_Art_Project.jpg/800px-Grant_Wood_-_American_Gothic_-_Google_Art_Project.jpg' },
  { id: 8, name: 'The Kiss', artist: 'Klimt', year: 1908, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/The_Kiss_-_Gustav_Klimt_-_Google_Cultural_Institute.jpg/800px-The_Kiss_-_Gustav_Klimt_-_Google_Cultural_Institute.jpg' },
  { id: 9, name: 'Cafe Terrace', artist: 'Van Gogh', year: 1888, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Van_Gogh_-_Terrasse_des_Caf%C3%A9s_an_der_Place_du_Forum_in_Arles_am_Abend1.jpeg/800px-Van_Gogh_-_Terrasse_des_Caf%C3%A9s_an_der_Place_du_Forum_in_Arles_am_Abend1.jpeg' },
  { id: 10, name: 'Water Lilies', artist: 'Monet', year: 1906, url: 'https://upload.wikimedia.org/wikipedia/commons/a/aa/Claude_Monet_-_Water_Lilies_-_1906%2C_Ryerson.jpg' },
  { id: 11, name: 'Whistlers Mother', artist: 'Whistler', year: 1871, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/Whistlers_Mother_high_res.jpg/1280px-Whistlers_Mother_high_res.jpg' },
  { id: 12, name: 'La Grande Jatte', artist: 'Seurat', year: 1886, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/A_Sunday_on_La_Grande_Jatte%2C_Georges_Seurat%2C_1884.jpg/1280px-A_Sunday_on_La_Grande_Jatte%2C_Georges_Seurat%2C_1884.jpg' },
  { id: 13, name: 'The Night Watch', artist: 'Rembrandt', year: 1642, url: 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/The_Night_Watch_-_HD.jpg/1280px-The_Night_Watch_-_HD.jpg' },
  { id: 14, name: 'Guernica', artist: 'Picasso', year: 1937, url: 'https://upload.wikimedia.org/wikipedia/en/7/74/Guernica.jpg' },
  { id: 15, name: 'Son of Man', artist: 'Magritte', year: 1964, url: 'https://upload.wikimedia.org/wikipedia/en/e/ec/Magritte_TheSonOfMan.jpg' },
];

// Player ID Generation
const ADJECTIVES = ['Swift', 'Brave', 'Wise', 'Noble', 'Silent', 'Golden', 'Silver', 'Cosmic', 'Mystic', 'Ancient'];
const NOUNS = ['Phoenix', 'Dragon', 'Tiger', 'Eagle', 'Wolf', 'Hawk', 'Lion', 'Bear', 'Serpent', 'Falcon'];

export const generatePlayerId = (address) => {
  const hash = address.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  return `${ADJECTIVES[hash % ADJECTIVES.length]}${NOUNS[(hash * 7) % NOUNS.length]}${(hash % 99) + 1}`;
};

// Phase Labels
export const PHASE_LABELS = {
  waiting: 'Waiting',
  playing: 'Playing',
  voting: 'Voting',
  finished: 'Finished',
};

export const PHASE_COLORS = {
  waiting: '#6B7280',
  playing: '#10B981',
  voting: '#F59E0B',
  finished: '#8B5CF6',
};

// Storage Key
export const STORAGE_KEY = 'consensus_gallery_dapp_v1';

// Helper functions
export const getArt = (id) => ART_COLLECTION.find(a => a.id === id) || ART_COLLECTION[0];
export const getRandomArt = () => ART_COLLECTION[Math.floor(Math.random() * ART_COLLECTION.length)];
export const formatTime = (seconds) => `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;
export const formatDate = (ts) => new Date(ts).toLocaleString();
export const shortenAddress = (addr) => addr ? `${addr.slice(0, 6)}...${addr.slice(-4)}` : '';
