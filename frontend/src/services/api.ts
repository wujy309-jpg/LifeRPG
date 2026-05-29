import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 120秒，AI响应可能较慢
});

export interface Character {
  id: number;
  name: string;
  level: number;
  exp: number;
  gold: number;
  strength: number;
  intelligence: number;
  agility: number;
  charisma: number;
  willpower: number;
}

export interface ActivityLog {
  id: number;
  character_id: number;
  activity_type: string;
  description: string;
  exp_gained: number;
  gold_gained: number;
  attribute_changes: string;
  ai_feedback: string;
  created_at: string;
}

export interface Equipment {
  id: number;
  name: string;
  description: string;
  rarity: string;
  stat_bonuses: string;
  special_effect: string;
  equipped: boolean;
  created_at: string;
}

export interface Title {
  id: number;
  name: string;
  description: string;
  unlock_condition: string;
  equipped: boolean;
}

export interface Quest {
  id: number;
  title: string;
  description: string;
  quest_type: string;
  exp_reward: number;
  gold_reward: number;
  status: string;
}

export interface GameFeedback {
  activity_log: ActivityLog;
  character: Character;
  level_up: boolean;
  new_level: number | null;
  equipment_found: Equipment | null;
  title_earned: Title | null;
  quest_generated: Quest | null;
  ai_comment: string | null;
}

export interface CharacterFull {
  character: Character;
  equipment: Equipment[];
  titles: Title[];
  active_quests: Quest[];
  recent_activities: ActivityLog[];
  next_level_exp: number;
  level_title: string;
}

export interface DailySummary {
  date: string;
  total_exp: number;
  total_gold: number;
  activities_count: number;
  activities: ActivityLog[];
  summary: string | null;
}

export const createCharacter = async (name: string): Promise<Character> => {
  const res = await api.post('/character', { name });
  return res.data;
};

export const getCharacterFull = async (characterId: number): Promise<CharacterFull> => {
  const res = await api.get(`/character/${characterId}/full`);
  return res.data;
};

export const logActivity = async (characterId: number, description: string): Promise<GameFeedback> => {
  const res = await api.post(`/activity/${characterId}`, { description });
  return res.data;
};

export const getActivities = async (characterId: number, limit: number = 20): Promise<ActivityLog[]> => {
  const res = await api.get(`/activities/${characterId}?limit=${limit}`);
  return res.data;
};

export const getEquipment = async (characterId: number): Promise<Equipment[]> => {
  const res = await api.get(`/equipment/${characterId}`);
  return res.data;
};

export const getTitles = async (characterId: number): Promise<Title[]> => {
  const res = await api.get(`/titles/${characterId}`);
  return res.data;
};

export const getQuests = async (characterId: number, status?: string): Promise<Quest[]> => {
  const url = status ? `/quests/${characterId}?status=${status}` : `/quests/${characterId}`;
  const res = await api.get(url);
  return res.data;
};

export const completeQuest = async (questId: number): Promise<any> => {
  const res = await api.post(`/quests/${questId}/complete`);
  return res.data;
};

export const getDailySummary = async (characterId: number): Promise<DailySummary> => {
  const res = await api.get(`/daily-summary/${characterId}`);
  return res.data;
};

export const getSystemStatus = async (): Promise<any> => {
  const res = await api.get('/status');
  return res.data;
};

// AI配置相关API
export interface AIProvider {
  name: string;
  base_url: string;
  model: string;
  api_key?: string;
  api_key_masked?: string;
  api_key_set?: boolean;
}

export interface AIProvidersResponse {
  current_provider: string;
  providers: Record<string, AIProvider>;
}

export const getAIProviders = async (): Promise<AIProvidersResponse> => {
  const res = await api.get('/ai/providers');
  return res.data;
};

export const switchAIProvider = async (providerName: string): Promise<any> => {
  const res = await api.post(`/ai/switch/${providerName}`);
  return res.data;
};

export const updateAIConfig = async (providerName: string, config: Partial<AIProvider>): Promise<any> => {
  const res = await api.post(`/ai/config/${providerName}`, config);
  return res.data;
};

export const testAIConnection = async (providerName: string): Promise<any> => {
  const res = await api.post(`/ai/test/${providerName}`);
  return res.data;
};

export default api;
