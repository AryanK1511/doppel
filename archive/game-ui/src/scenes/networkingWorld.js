import { createAgentSprite, updateAgentPosition } from '../components/agent.js';
import { createSpeechBubble } from '../components/speechBubble.js';
import { AGENT_COLORS, WORLD_CONFIG, UI_COLORS, FONT_SIZES } from '../config.js';
import { WorldWebSocket } from '../websocket.js';
import { fetchAgents, spawnAgent, startWorld } from '../api.js';

export function initNetworkingWorld(k) {
    const agents = new Map();
    let worldWs = null;
    const activeBubbles = new Map();
    let selectedAgent = null;
    const MOVE_SPEED = 3;
    const PROXIMITY_THRESHOLD = 100; // Distance for conversations to trigger
    const activeConversations = new Set(); // Track ongoing conversations

    k.scene('networking', async () => {
        k.setBackground(k.Color.fromArray([...WORLD_CONFIG.backgroundColor, 255]));

        // Main world background with gradient effect
        k.add([
            k.rect(WORLD_CONFIG.width, WORLD_CONFIG.height),
            k.pos(0, 0),
            k.color(20, 20, 35),
            k.anchor('topleft'),
            k.z(0),
        ]);

        // Animated grid background
        for (let i = 0; i < 24; i++) {
            for (let j = 0; j < 16; j++) {
                const delay = (i + j) * 0.08;
                const dot = k.add([
                    k.circle(2),
                    k.pos(50 + i * 50, 50 + j * 50),
                    k.color(60, 60, 90),
                    k.anchor('center'),
                    k.opacity(0.3),
                    k.z(1),
                ]);

                dot.onUpdate(() => {
                    const pulse = Math.sin(k.time() * 1.5 + delay) * 0.2 + 0.3;
                    dot.opacity = pulse;
                });
            }
        }

        // Header bar
        k.add([
            k.rect(WORLD_CONFIG.width, 70),
            k.pos(0, 0),
            k.color(15, 15, 25),
            k.anchor('topleft'),
            k.z(50),
            k.opacity(0.95),
        ]);

        // Header gradient line
        k.add([
            k.rect(WORLD_CONFIG.width, 3),
            k.pos(0, 70),
            k.color(...UI_COLORS.primary),
            k.anchor('topleft'),
            k.z(51),
            k.opacity(0.6),
        ]);

        // Title
        k.add([
            k.text('DOPPEL', { size: FONT_SIZES.heading, font: 'pixelFont' }),
            k.pos(30, 35),
            k.color(255, 255, 255),
            k.anchor('left'),
            k.z(52),
        ]);

        k.add([
            k.text('AI Networking World', { size: FONT_SIZES.small, font: 'pixelFont' }),
            k.pos(170, 35),
            k.color(...UI_COLORS.textMuted),
            k.anchor('left'),
            k.z(52),
        ]);

        // Status panel
        const statusPanel = k.add([
            k.rect(200, 40, { radius: 8 }),
            k.pos(WORLD_CONFIG.width / 2 - 150, 35),
            k.color(...UI_COLORS.panel),
            k.anchor('center'),
            k.z(52),
        ]);

        const statusText = statusPanel.add([
            k.text('Connecting...', { size: FONT_SIZES.small, font: 'pixelFont' }),
            k.pos(0, 0),
            k.color(...UI_COLORS.warning),
            k.anchor('center'),
        ]);

        // Selected agent indicator
        const selectedPanel = k.add([
            k.rect(220, 40, { radius: 8 }),
            k.pos(WORLD_CONFIG.width / 2 + 100, 35),
            k.color(...UI_COLORS.panel),
            k.anchor('center'),
            k.z(52),
        ]);

        const selectedText = selectedPanel.add([
            k.text('Click agent to select', { size: FONT_SIZES.small, font: 'pixelFont' }),
            k.pos(0, 0),
            k.color(...UI_COLORS.textDim),
            k.anchor('center'),
        ]);

        // Navigation buttons
        const dashboardBtn = k.add([
            k.rect(130, 42, { radius: 8 }),
            k.pos(WORLD_CONFIG.width - 160, 35),
            k.color(...UI_COLORS.primary),
            k.anchor('center'),
            k.area(),
            k.z(52),
        ]);

        dashboardBtn.add([
            k.text('Dashboard', { size: FONT_SIZES.small, font: 'pixelFont' }),
            k.pos(0, 0),
            k.color(255, 255, 255),
            k.anchor('center'),
        ]);

        dashboardBtn.onClick(() => {
            k.go('dashboard');
        });

        dashboardBtn.onHover(() => {
            dashboardBtn.color = k.Color.fromArray([...UI_COLORS.primaryHover, 255]);
        });

        dashboardBtn.onHoverEnd(() => {
            dashboardBtn.color = k.Color.fromArray([...UI_COLORS.primary, 255]);
        });

        // Bottom bar with legend
        k.add([
            k.rect(WORLD_CONFIG.width, 60),
            k.pos(0, WORLD_CONFIG.height - 60),
            k.color(15, 15, 25),
            k.anchor('topleft'),
            k.z(50),
            k.opacity(0.9),
        ]);

        // Legend
        k.add([
            k.circle(12),
            k.pos(30, WORLD_CONFIG.height - 30),
            k.color(...AGENT_COLORS.recruiter),
            k.anchor('center'),
            k.z(52),
        ]);
        k.add([
            k.text('Recruiters', { size: FONT_SIZES.small, font: 'pixelFont' }),
            k.pos(50, WORLD_CONFIG.height - 30),
            k.color(...AGENT_COLORS.recruiter),
            k.anchor('left'),
            k.z(52),
        ]);

        k.add([
            k.circle(12),
            k.pos(180, WORLD_CONFIG.height - 30),
            k.color(...AGENT_COLORS.candidate),
            k.anchor('center'),
            k.z(52),
        ]);
        k.add([
            k.text('Candidates', { size: FONT_SIZES.small, font: 'pixelFont' }),
            k.pos(200, WORLD_CONFIG.height - 30),
            k.color(...AGENT_COLORS.candidate),
            k.anchor('left'),
            k.z(52),
        ]);

        // Controls hint
        k.add([
            k.text('Click agent to select  |  Click canvas to move  |  ESC: Deselect', { size: FONT_SIZES.tiny, font: 'pixelFont' }),
            k.pos(400, WORLD_CONFIG.height - 30),
            k.color(...UI_COLORS.textDim),
            k.anchor('left'),
            k.z(52),
        ]);

        // Conversation log panel (right side)
        k.add([
            k.rect(300, WORLD_CONFIG.height - 140),
            k.pos(WORLD_CONFIG.width - 310, 80),
            k.color(15, 15, 25),
            k.anchor('topleft'),
            k.z(40),
            k.opacity(0.85),
        ]);

        k.add([
            k.text('Live Conversations', { size: FONT_SIZES.body, font: 'pixelFont' }),
            k.pos(WORLD_CONFIG.width - 160, 95),
            k.color(255, 255, 255),
            k.anchor('center'),
            k.z(41),
        ]);

        const conversationLog = [];
        const maxLogEntries = 8;
        const logContainer = k.add([k.pos(WORLD_CONFIG.width - 300, 130), k.z(41)]);

        function addToLog(speakerName, content, role) {
            conversationLog.unshift({ speakerName, content, role, time: Date.now() });
            if (conversationLog.length > maxLogEntries) {
                conversationLog.pop();
            }
            renderLog();
        }

        function renderLog() {
            logContainer.children.forEach(c => c.destroy());

            conversationLog.forEach((entry, i) => {
                const roleColor = AGENT_COLORS[entry.role] || [150, 150, 150];
                const truncatedContent = entry.content.length > 35
                    ? entry.content.substring(0, 35) + '...'
                    : entry.content;

                const entryContainer = logContainer.add([
                    k.rect(280, 55, { radius: 6 }),
                    k.pos(5, i * 62),
                    k.color(...UI_COLORS.panel),
                    k.opacity(Math.max(0.3, 1 - i * 0.12)),
                ]);

                entryContainer.add([
                    k.text(entry.speakerName, { size: FONT_SIZES.tiny, font: 'pixelFont' }),
                    k.pos(10, 8),
                    k.color(...roleColor),
                ]);

                entryContainer.add([
                    k.text(truncatedContent, { size: FONT_SIZES.tiny, font: 'pixelFont' }),
                    k.pos(10, 28),
                    k.color(...UI_COLORS.textMuted),
                ]);
            });
        }

        // Keyboard shortcuts info
        k.add([
            k.text('D: Dashboard', { size: FONT_SIZES.tiny, font: 'pixelFont' }),
            k.pos(WORLD_CONFIG.width - 160, WORLD_CONFIG.height - 30),
            k.color(...UI_COLORS.textDim),
            k.anchor('center'),
            k.z(52),
        ]);

        // Agent selection handler
        function handleAgentSelect(agent) {
            // Deselect previous agent
            if (selectedAgent && selectedAgent !== agent) {
                selectedAgent.setSelected(false);
            }

            // Toggle selection
            if (selectedAgent === agent) {
                selectedAgent.setSelected(false);
                selectedAgent = null;
                selectedText.text = 'Click agent to select';
                selectedText.color = k.Color.fromArray([...UI_COLORS.textDim, 255]);
            } else {
                selectedAgent = agent;
                selectedAgent.setSelected(true);
                selectedText.text = `Selected: ${agent.agentName}`;
                const agentColor = AGENT_COLORS[agent.agentType];
                selectedText.color = k.Color.fromArray([...agentColor, 255]);
            }
        }

        // Click-to-move: click on canvas to move selected agent
        k.onClick(() => {
            if (selectedAgent) {
                const mousePos = k.mousePos();
                // Clamp to playable area
                const targetX = Math.max(80, Math.min(WORLD_CONFIG.width - 380, mousePos.x));
                const targetY = Math.max(120, Math.min(WORLD_CONFIG.height - 120, mousePos.y));

                selectedAgent.targetX = targetX;
                selectedAgent.targetY = targetY;
            }
        });

        // Deselect on escape
        k.onKeyPress('escape', () => {
            if (selectedAgent) {
                selectedAgent.setSelected(false);
                selectedAgent = null;
                selectedText.text = 'Click agent to select';
                selectedText.color = k.Color.fromArray([...UI_COLORS.textDim, 255]);
            } else {
                k.go('menu');
            }
        });

        // D for dashboard
        k.onKeyPress('d', () => {
            k.go('dashboard');
        });

        // Message handlers
        function handleWorldMessage(data) {
            if (data.type === 'world_state') {
                updateAgents(data.data);
                statusText.text = `Agents: ${data.data.agents.length}  |  Active: ${data.data.active_conversations.length}`;
                statusText.color = k.Color.fromArray([...UI_COLORS.success, 255]);
            } else if (data.type === 'conversation_turn') {
                handleConversationTurn(data);
            }
        }

        function updateAgents(worldState) {
            const currentAgentIds = new Set(worldState.agents.map((a) => a.agent_id));

            // Remove agents that are no longer in the world
            for (const [agentId, agentSprite] of agents) {
                if (!currentAgentIds.has(agentId)) {
                    if (selectedAgent === agentSprite) {
                        selectedAgent = null;
                        selectedText.text = 'Click agent to select';
                        selectedText.color = k.Color.fromArray([...UI_COLORS.textDim, 255]);
                    }
                    agentSprite.destroy();
                    agents.delete(agentId);
                    if (activeBubbles.has(agentId)) {
                        activeBubbles.get(agentId).destroy();
                        activeBubbles.delete(agentId);
                    }
                }
            }

            // Update or create agents
            for (const agentData of worldState.agents) {
                // Adjust positions to stay within visible area
                const adjustedX = Math.max(80, Math.min(agentData.x, WORLD_CONFIG.width - 380));
                const adjustedY = Math.max(120, Math.min(agentData.y, WORLD_CONFIG.height - 120));

                if (agents.has(agentData.agent_id)) {
                    const sprite = agents.get(agentData.agent_id);
                    // Don't update position for selected agent (manual control)
                    if (!sprite.isSelected) {
                        updateAgentPosition(k, sprite, adjustedX, adjustedY, agentData.state);
                    } else {
                        // Still update talking state
                        sprite.isTalking = agentData.state === 'talking';
                    }
                } else {
                    const adjustedAgentData = {
                        ...agentData,
                        x: adjustedX,
                        y: adjustedY,
                    };
                    const sprite = createAgentSprite(k, adjustedAgentData, handleAgentSelect);
                    agents.set(agentData.agent_id, sprite);
                }
            }
        }

        function handleConversationTurn(data) {
            const turn = data.turn;

            const speakingAgents = [...agents.values()].filter(
                (a) => a.agentType === turn.role
            );

            if (speakingAgents.length > 0) {
                const speaker = speakingAgents.find((a) => a.agentName === turn.speaker_name);
                if (speaker) {
                    showSpeechBubble(speaker, turn.content, turn.speaker_name, turn.role);
                    addToLog(turn.speaker_name, turn.content, turn.role);
                }
            }

            if (turn.is_final && turn.final_evaluation) {
                console.log('Conversation completed:', data.conversation_id);
            }
        }

        function showSpeechBubble(agent, text, speakerName, role) {
            if (activeBubbles.has(agent.agentId)) {
                activeBubbles.get(agent.agentId).destroy();
            }

            const bubble = createSpeechBubble(k, text, speakerName, role);
            bubble.pos = k.vec2(agent.pos.x, agent.pos.y - 70);
            activeBubbles.set(agent.agentId, bubble);

            k.wait(6, () => {
                if (activeBubbles.get(agent.agentId) === bubble) {
                    // Fade out animation
                    k.tween(1, 0, 0.3, (v) => {
                        if (bubble.exists()) {
                            bubble.opacity = v;
                        }
                    }).onEnd(() => {
                        if (bubble.exists()) {
                            bubble.destroy();
                        }
                        if (activeBubbles.get(agent.agentId) === bubble) {
                            activeBubbles.delete(agent.agentId);
                        }
                    });
                }
            });
        }

        // Update loop - smooth movement and proximity detection
        k.onUpdate(() => {
            for (const [agentId, sprite] of agents) {
                // Smooth movement towards target
                if (sprite.targetX !== undefined && sprite.targetY !== undefined) {
                    const dx = sprite.targetX - sprite.pos.x;
                    const dy = sprite.targetY - sprite.pos.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist > 2) {
                        // Move towards target smoothly
                        sprite.pos.x += (dx / dist) * MOVE_SPEED;
                        sprite.pos.y += (dy / dist) * MOVE_SPEED;
                    }
                }

                // Update bubble position to follow agent
                if (activeBubbles.has(agentId)) {
                    const bubble = activeBubbles.get(agentId);
                    bubble.pos = k.vec2(sprite.pos.x, sprite.pos.y - 70);
                }
            }

            // Proximity detection for conversations
            checkProximityForConversations();
        });

        // Check if agents are close enough to start a conversation
        function checkProximityForConversations() {
            const agentList = [...agents.values()];

            for (let i = 0; i < agentList.length; i++) {
                for (let j = i + 1; j < agentList.length; j++) {
                    const agent1 = agentList[i];
                    const agent2 = agentList[j];

                    // Only check recruiter-candidate pairs
                    if (agent1.agentType === agent2.agentType) continue;

                    const dx = agent1.pos.x - agent2.pos.x;
                    const dy = agent1.pos.y - agent2.pos.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    const pairKey = [agent1.agentId, agent2.agentId].sort().join('-');

                    if (distance < PROXIMITY_THRESHOLD) {
                        if (!activeConversations.has(pairKey)) {
                            activeConversations.add(pairKey);
                            // Visual indicator that they're close enough to talk
                            agent1.isTalking = true;
                            agent2.isTalking = true;
                        }
                    } else {
                        if (activeConversations.has(pairKey)) {
                            activeConversations.delete(pairKey);
                            // Only stop talking visual if not in another conversation
                            const hasOtherConvo1 = [...activeConversations].some(k => k.includes(agent1.agentId));
                            const hasOtherConvo2 = [...activeConversations].some(k => k.includes(agent2.agentId));
                            if (!hasOtherConvo1) agent1.isTalking = false;
                            if (!hasOtherConvo2) agent2.isTalking = false;
                        }
                    }
                }
            }
        }

        // WebSocket connection
        worldWs = new WorldWebSocket(
            handleWorldMessage,
            () => {
                statusText.text = 'Connection Error';
                statusText.color = k.Color.fromArray([...UI_COLORS.danger, 255]);
            },
            () => {
                statusText.text = 'Disconnected';
                statusText.color = k.Color.fromArray([...UI_COLORS.warning, 255]);
            }
        );

        worldWs.connect();

        // Auto-spawn all agents at random positions
        async function autoSpawnAgents() {
            try {
                statusText.text = 'Loading agents...';
                statusText.color = k.Color.fromArray([...UI_COLORS.warning, 255]);

                // Start the world first
                await startWorld();

                // Fetch all available agents
                const allAgents = await fetchAgents();

                if (allAgents.length === 0) {
                    statusText.text = 'No agents available';
                    return;
                }

                // Spawn each agent at a random position
                for (const agent of allAgents) {
                    const randomX = 100 + Math.random() * (WORLD_CONFIG.width - 500);
                    const randomY = 150 + Math.random() * (WORLD_CONFIG.height - 300);
                    await spawnAgent(agent.id, randomX, randomY);
                }

                statusText.text = `Spawned ${allAgents.length} agents`;
                statusText.color = k.Color.fromArray([...UI_COLORS.success, 255]);
            } catch (err) {
                console.error('Failed to auto-spawn agents:', err);
                statusText.text = 'Failed to load agents';
                statusText.color = k.Color.fromArray([...UI_COLORS.danger, 255]);
            }
        }

        // Trigger auto-spawn when scene loads
        autoSpawnAgents();

        k.onSceneLeave(() => {
            if (worldWs) {
                worldWs.disconnect();
            }
            selectedAgent = null;
        });
    });

    return {
        start: () => k.go('networking'),
        getAgents: () => agents,
    };
}
