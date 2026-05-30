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
  gender?: string;
  age?: number;
  height?: number;
  weight?: number;
  education?: string;
  occupation?: string;
  created_at?: string;
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
  use_desc: string;
  use_effect: string;
  use_bonus: string;
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

export const getAllCharacters = async (): Promise<{ characters: Character[], count: number, max_count: number }> => {
  const res = await api.get('/characters');
  return res.data;
};

export const createCharacter = async (
  name: string,
  gender?: string,
  age?: number,
  height?: number,
  weight?: number,
  education?: string,
  occupation?: string
): Promise<Character> => {
  const res = await api.post('/character', { 
    name,
    gender: gender || '',
    age: age || 0,
    height: height || 0,
    weight: weight || 0,
    education: education || '',
    occupation: occupation || ''
  });
  return res.data;
};

export const deleteCharacter = async (characterId: number): Promise<any> => {
  const res = await api.delete(`/character/${characterId}`);
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

export const useEquipment = async (equipmentId: number): Promise<any> => {
  const res = await api.post(`/equipment/${equipmentId}/use`);
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

export interface AllQuestsResponse {
  available_quests: {
    daily: Quest[];
    weekly: Quest[];
    challenge: Quest[];
  };
  active_quests: Quest[];
  completed_today: number;
  active_count: number;
}

export const getAllQuests = async (characterId: number): Promise<AllQuestsResponse> => {
  const res = await api.get(`/quests/${characterId}/all`);
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

// 统计相关API
export interface ActivityStats {
  total_count: number;
  today_count: number;
  week_count: number;
  total_exp: number;
  total_gold: number;
  type_stats: { activity_type: string; count: number }[];
  most_common: string;
  consecutive_days: number;
}

export interface ActivityHistory {
  date: string;
  count: number;
  exp: number;
  gold: number;
}

export interface AttributeHistory {
  date: string;
  strength: number;
  intelligence: number;
  agility: number;
  charisma: number;
  willpower: number;
}

export const getActivityStats = async (characterId: number): Promise<ActivityStats> => {
  const res = await api.get(`/stats/${characterId}`);
  return res.data;
};

export const getActivityHistory = async (characterId: number, days: number = 30): Promise<ActivityHistory[]> => {
  const res = await api.get(`/stats/${characterId}/history?days=${days}`);
  return res.data.history;
};

export const getAttributeHistory = async (characterId: number, days: number = 30): Promise<AttributeHistory[]> => {
  const res = await api.get(`/stats/${characterId}/attributes?days=${days}`);
  return res.data.history;
};

export const getWeeklyActivityTypes = async (characterId: number): Promise<Record<string, number>> => {
  const res = await api.get(`/stats/${characterId}/weekly-types`);
  return res.data.types;
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


// ==================== 现实连接 API ====================

export interface RealityReward {
  id: number;
  character_id: number;
  name: string;
  description: string;
  category: string;
  cost: number;
  icon: string;
  is_custom: boolean;
  times_redeemed: number;
}

export interface HabitChallenge {
  id: number;
  character_id: number;
  name: string;
  description: string;
  duration_days: number;
  cost: number;
  reward_exp: number;
  reward_gold: number;
  status: string;
  start_date: string;
  end_date: string;
  check_in_days: number;
  last_check_in: string;
}

export interface ImmunityCard {
  id: number;
  character_id: number;
  name: string;
  description: string;
  cost: number;
  uses_remaining: number;
  card_type: string;
}

export const getRealityRewards = async (characterId: number): Promise<{rewards: RealityReward[], gold: number}> => {
  const res = await api.get(`/reality/rewards/${characterId}`);
  return res.data;
};

export const addCustomReward = async (characterId: number, data: {name: string, description?: string, cost: number}): Promise<any> => {
  const res = await api.post(`/reality/rewards/${characterId}/add`, data);
  return res.data;
};

export const redeemReward = async (characterId: number, rewardId: number): Promise<any> => {
  const res = await api.post(`/reality/rewards/${characterId}/redeem/${rewardId}`);
  return res.data;
};

export const getHabitChallenges = async (characterId: number): Promise<{challenges: HabitChallenge[], gold: number}> => {
  const res = await api.get(`/reality/challenges/${characterId}`);
  return res.data;
};

export const createHabitChallenge = async (characterId: number, data: {name: string, description?: string, duration_days?: number, cost?: number}): Promise<any> => {
  const res = await api.post(`/reality/challenges/${characterId}/create`, data);
  return res.data;
};

export const checkInChallenge = async (characterId: number, challengeId: number): Promise<any> => {
  const res = await api.post(`/reality/challenges/${challengeId}/checkin/${characterId}`);
  return res.data;
};

export const getImmunityCards = async (characterId: number): Promise<{cards: ImmunityCard[], gold: number}> => {
  const res = await api.get(`/reality/cards/${characterId}`);
  return res.data;
};

export const buyImmunityCard = async (characterId: number, cardType: string): Promise<any> => {
  const res = await api.post(`/reality/cards/${characterId}/buy`, {card_type: cardType});
  return res.data;
};

export const checkPenalty = async (characterId: number): Promise<any> => {
  const res = await api.get(`/reality/penalty/${characterId}`);
  return res.data;
};

export const getPenaltyHistory = async (characterId: number): Promise<any> => {
  const res = await api.get(`/reality/penalty/${characterId}/history`);
  return res.data;
};

export default api;
