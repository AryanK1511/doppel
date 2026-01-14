import { API_BASE_URL } from './config.js';

export async function fetchAgents() {
  const response = await fetch(`${API_BASE_URL}/agent`);
  const data = await response.json();
  return data.data || [];
}

export async function createAgent(agentData) {
  const response = await fetch(`${API_BASE_URL}/agent/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(agentData),
  });
  const data = await response.json();
  return data.data;
}

export async function startWorld() {
  const response = await fetch(`${API_BASE_URL}/world/start`, {
    method: 'POST',
  });
  return response.json();
}

export async function stopWorld() {
  const response = await fetch(`${API_BASE_URL}/world/stop`, {
    method: 'POST',
  });
  return response.json();
}

export async function spawnAgent(agentId, x, y) {
  const response = await fetch(`${API_BASE_URL}/world/spawn`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId, x, y }),
  });
  return response.json();
}

export async function removeAgent(agentId) {
  const response = await fetch(`${API_BASE_URL}/world/remove`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId }),
  });
  return response.json();
}

export async function getWorldState() {
  const response = await fetch(`${API_BASE_URL}/world/state`);
  return response.json();
}

export async function getConversations() {
  const response = await fetch(`${API_BASE_URL}/conversation`);
  const data = await response.json();
  return data.data || [];
}

export async function getConversation(conversationId) {
  const response = await fetch(`${API_BASE_URL}/conversation/${conversationId}`);
  const data = await response.json();
  return data.data;
}

export async function getMatches(minScore = null) {
  const url = minScore
    ? `${API_BASE_URL}/conversation/matches?min_score=${minScore}`
    : `${API_BASE_URL}/conversation/matches`;
  const response = await fetch(url);
  const data = await response.json();
  return data.data || [];
}
