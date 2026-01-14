import { fetchAgents, spawnAgent, startWorld, stopWorld } from '../api.js';
import { AGENT_COLORS, FONT_SIZES, UI_COLORS, WORLD_CONFIG } from '../config.js';

export function initControlPanel(k) {
  let agents = [];
  let isWorldRunning = false;

  k.scene('control', async () => {
    k.setBackground(k.Color.fromArray([15, 15, 25, 255]));

    // Background pattern
    for (let i = 0; i < 24; i++) {
      for (let j = 0; j < 16; j++) {
        k.add([
          k.circle(1.5),
          k.pos(50 + i * 50, 50 + j * 50),
          k.color(40, 40, 60),
          k.anchor('center'),
          k.opacity(0.3),
          k.z(0),
        ]);
      }
    }

    // Header
    k.add([
      k.rect(WORLD_CONFIG.width, 80),
      k.pos(0, 0),
      k.color(20, 20, 35),
      k.anchor('topleft'),
      k.z(50),
    ]);

    k.add([
      k.rect(WORLD_CONFIG.width, 3),
      k.pos(0, 80),
      k.color(...UI_COLORS.primary),
      k.anchor('topleft'),
      k.z(51),
      k.opacity(0.6),
    ]);

    k.add([
      k.text('CONTROL PANEL', { size: FONT_SIZES.heading, font: 'pixelFont' }),
      k.pos(WORLD_CONFIG.width / 2, 40),
      k.color(255, 255, 255),
      k.anchor('center'),
      k.z(52),
    ]);

    // Back button
    const backBtn = k.add([
      k.rect(120, 45, { radius: 8 }),
      k.pos(80, 40),
      k.color(...UI_COLORS.panelLight),
      k.anchor('center'),
      k.area(),
      k.z(52),
    ]);

    backBtn.add([
      k.text('< Back', { size: FONT_SIZES.body, font: 'pixelFont' }),
      k.pos(0, 0),
      k.color(255, 255, 255),
      k.anchor('center'),
    ]);

    backBtn.onClick(() => {
      k.go('networking');
    });

    backBtn.onHover(() => {
      backBtn.color = k.Color.fromArray([60, 60, 80, 255]);
    });

    backBtn.onHoverEnd(() => {
      backBtn.color = k.Color.fromArray([...UI_COLORS.panelLight, 255]);
    });

    // World Control Section
    const worldPanel = k.add([
      k.rect(550, 180, { radius: 12 }),
      k.pos(30, 110),
      k.color(...UI_COLORS.panel),
      k.anchor('topleft'),
      k.z(10),
    ]);

    k.add([
      k.text('World Simulation', { size: FONT_SIZES.subheading, font: 'pixelFont' }),
      k.pos(50, 135),
      k.color(255, 255, 255),
      k.z(15),
    ]);

    // Status indicator
    const statusContainer = k.add([
      k.rect(180, 45, { radius: 8 }),
      k.pos(350, 125),
      k.color(...UI_COLORS.panelLight),
      k.z(15),
    ]);

    const statusIndicator = statusContainer.add([
      k.circle(10),
      k.pos(25, 22),
      k.color(...UI_COLORS.danger),
      k.anchor('center'),
    ]);

    const statusLabel = statusContainer.add([
      k.text('Stopped', { size: FONT_SIZES.small, font: 'pixelFont' }),
      k.pos(45, 15),
      k.color(...UI_COLORS.danger),
    ]);

    // Control buttons
    const startBtn = k.add([
      k.rect(200, 60, { radius: 10 }),
      k.pos(50, 190),
      k.color(...UI_COLORS.success),
      k.area(),
      k.z(15),
    ]);

    startBtn.add([
      k.text('Start Simulation', { size: FONT_SIZES.body, font: 'pixelFont' }),
      k.pos(100, 30),
      k.color(255, 255, 255),
      k.anchor('center'),
    ]);

    const stopBtn = k.add([
      k.rect(200, 60, { radius: 10 }),
      k.pos(270, 190),
      k.color(...UI_COLORS.danger),
      k.area(),
      k.z(15),
    ]);

    stopBtn.add([
      k.text('Stop Simulation', { size: FONT_SIZES.body, font: 'pixelFont' }),
      k.pos(100, 30),
      k.color(255, 255, 255),
      k.anchor('center'),
    ]);

    startBtn.onClick(async () => {
      try {
        await startWorld();
        isWorldRunning = true;
        statusIndicator.color = k.Color.fromArray([...UI_COLORS.success, 255]);
        statusLabel.text = 'Running';
        statusLabel.color = k.Color.fromArray([...UI_COLORS.success, 255]);

        // Flash effect
        startBtn.color = k.Color.fromArray([150, 255, 180, 255]);
        k.wait(0.2, () => {
          startBtn.color = k.Color.fromArray([...UI_COLORS.success, 255]);
        });
      } catch (e) {
        console.error('Failed to start world:', e);
      }
    });

    stopBtn.onClick(async () => {
      try {
        await stopWorld();
        isWorldRunning = false;
        statusIndicator.color = k.Color.fromArray([...UI_COLORS.danger, 255]);
        statusLabel.text = 'Stopped';
        statusLabel.color = k.Color.fromArray([...UI_COLORS.danger, 255]);

        // Flash effect
        stopBtn.color = k.Color.fromArray([255, 150, 150, 255]);
        k.wait(0.2, () => {
          stopBtn.color = k.Color.fromArray([...UI_COLORS.danger, 255]);
        });
      } catch (e) {
        console.error('Failed to stop world:', e);
      }
    });

    startBtn.onHover(() => {
      startBtn.color = k.Color.fromArray([120, 240, 160, 255]);
    });

    startBtn.onHoverEnd(() => {
      startBtn.color = k.Color.fromArray([...UI_COLORS.success, 255]);
    });

    stopBtn.onHover(() => {
      stopBtn.color = k.Color.fromArray([255, 130, 150, 255]);
    });

    stopBtn.onHoverEnd(() => {
      stopBtn.color = k.Color.fromArray([...UI_COLORS.danger, 255]);
    });

    // Agent List Section
    k.add([
      k.rect(550, WORLD_CONFIG.height - 330, { radius: 12 }),
      k.pos(30, 310),
      k.color(...UI_COLORS.panel),
      k.anchor('topleft'),
      k.z(10),
    ]);

    k.add([
      k.text('Available Agents', { size: FONT_SIZES.subheading, font: 'pixelFont' }),
      k.pos(50, 335),
      k.color(255, 255, 255),
      k.z(15),
    ]);

    // Refresh agents button
    const refreshBtn = k.add([
      k.rect(120, 40, { radius: 8 }),
      k.pos(420, 325),
      k.color(...UI_COLORS.primary),
      k.area(),
      k.z(15),
    ]);

    refreshBtn.add([
      k.text('Refresh', { size: FONT_SIZES.small, font: 'pixelFont' }),
      k.pos(60, 20),
      k.color(255, 255, 255),
      k.anchor('center'),
    ]);

    refreshBtn.onClick(loadAgents);

    const agentListContainer = k.add([k.pos(50, 380), k.z(15)]);

    // Instructions Panel (right side)
    k.add([
      k.rect(570, WORLD_CONFIG.height - 140, { radius: 12 }),
      k.pos(600, 110),
      k.color(...UI_COLORS.panel),
      k.anchor('topleft'),
      k.z(10),
    ]);

    k.add([
      k.text('How It Works', { size: FONT_SIZES.subheading, font: 'pixelFont' }),
      k.pos(620, 135),
      k.color(255, 255, 255),
      k.z(15),
    ]);

    const instructions = [
      { text: '1. Start the world simulation', color: UI_COLORS.success },
      { text: '2. Spawn agents from the list below', color: UI_COLORS.primary },
      { text: '3. Watch agents wander and meet', color: UI_COLORS.secondary },
      { text: '4. Conversations start automatically', color: UI_COLORS.textMuted },
      { text: '5. Check Dashboard for results', color: UI_COLORS.textMuted },
    ];

    instructions.forEach((inst, i) => {
      k.add([
        k.text(inst.text, { size: FONT_SIZES.body, font: 'pixelFont' }),
        k.pos(620, 180 + i * 40),
        k.color(...inst.color),
        k.z(15),
      ]);
    });

    // Agent behavior section
    k.add([
      k.rect(530, 2),
      k.pos(620, 400),
      k.color(...UI_COLORS.panelBorder),
      k.opacity(0.3),
      k.z(15),
    ]);

    k.add([
      k.text('Agent Behavior', { size: FONT_SIZES.body, font: 'pixelFont' }),
      k.pos(620, 420),
      k.color(255, 255, 255),
      k.z(15),
    ]);

    const behaviors = [
      'Agents wander around the world randomly',
      'When a recruiter and candidate get close,',
      'they automatically start a conversation',
      'The recruiter evaluates the candidate',
      'and provides a match score (1-10)',
    ];

    behaviors.forEach((behavior, i) => {
      k.add([
        k.text(behavior, { size: FONT_SIZES.small, font: 'pixelFont' }),
        k.pos(620, 455 + i * 28),
        k.color(...UI_COLORS.textMuted),
        k.z(15),
      ]);
    });

    // Legend
    k.add([
      k.rect(530, 2),
      k.pos(620, 600),
      k.color(...UI_COLORS.panelBorder),
      k.opacity(0.3),
      k.z(15),
    ]);

    k.add([
      k.text('Agent Types', { size: FONT_SIZES.body, font: 'pixelFont' }),
      k.pos(620, 620),
      k.color(255, 255, 255),
      k.z(15),
    ]);

    k.add([
      k.circle(12),
      k.pos(635, 665),
      k.color(...AGENT_COLORS.recruiter),
      k.anchor('center'),
      k.z(15),
    ]);
    k.add([
      k.text('Recruiters - Evaluate candidates', { size: FONT_SIZES.small, font: 'pixelFont' }),
      k.pos(660, 657),
      k.color(...AGENT_COLORS.recruiter),
      k.z(15),
    ]);

    k.add([
      k.circle(12),
      k.pos(635, 705),
      k.color(...AGENT_COLORS.candidate),
      k.anchor('center'),
      k.z(15),
    ]);
    k.add([
      k.text('Candidates - Share their experience', { size: FONT_SIZES.small, font: 'pixelFont' }),
      k.pos(660, 697),
      k.color(...AGENT_COLORS.candidate),
      k.z(15),
    ]);

    async function loadAgents() {
      try {
        agents = await fetchAgents();
        renderAgentList();
      } catch (e) {
        console.error('Failed to load agents:', e);
      }
    }

    function renderAgentList() {
      agentListContainer.children.forEach((c) => c.destroy());

      if (agents.length === 0) {
        agentListContainer.add([
          k.text('No agents found.', { size: FONT_SIZES.body, font: 'pixelFont' }),
          k.pos(0, 20),
          k.color(...UI_COLORS.textDim),
        ]);
        agentListContainer.add([
          k.text('Create some agents via the API first!', {
            size: FONT_SIZES.small,
            font: 'pixelFont',
          }),
          k.pos(0, 50),
          k.color(...UI_COLORS.textDim),
        ]);
        return;
      }

      agents.slice(0, 6).forEach((agent, i) => {
        const row = agentListContainer.add([
          k.rect(490, 55, { radius: 8 }),
          k.pos(0, i * 65),
          k.color(...UI_COLORS.panelLight),
          k.z(16),
        ]);

        const typeColor =
          agent.type === 'recruiter' ? AGENT_COLORS.recruiter : AGENT_COLORS.candidate;

        // Type indicator
        row.add([k.circle(10), k.pos(25, 27), k.color(...typeColor), k.anchor('center')]);

        // Agent name
        row.add([
          k.text(agent.name, { size: FONT_SIZES.body, font: 'pixelFont' }),
          k.pos(50, 12),
          k.color(255, 255, 255),
        ]);

        // Agent type
        row.add([
          k.text(agent.type, { size: FONT_SIZES.tiny, font: 'pixelFont' }),
          k.pos(50, 34),
          k.color(...typeColor),
        ]);

        // Spawn button
        const spawnBtn = row.add([
          k.rect(100, 40, { radius: 6 }),
          k.pos(375, 8),
          k.color(...UI_COLORS.success),
          k.area(),
        ]);

        spawnBtn.add([
          k.text('Spawn', { size: FONT_SIZES.small, font: 'pixelFont' }),
          k.pos(50, 20),
          k.color(255, 255, 255),
          k.anchor('center'),
        ]);

        spawnBtn.onClick(async () => {
          try {
            const randomX = 100 + Math.random() * (WORLD_CONFIG.width - 500);
            const randomY = 150 + Math.random() * (WORLD_CONFIG.height - 300);
            await spawnAgent(agent.id, randomX, randomY);
            // Success flash
            spawnBtn.color = k.Color.fromArray([150, 255, 180, 255]);
            k.wait(0.3, () => {
              spawnBtn.color = k.Color.fromArray([...UI_COLORS.success, 255]);
            });
          } catch (e) {
            console.error('Failed to spawn agent:', e);
            // Error flash
            spawnBtn.color = k.Color.fromArray([255, 100, 120, 255]);
            k.wait(0.3, () => {
              spawnBtn.color = k.Color.fromArray([...UI_COLORS.success, 255]);
            });
          }
        });

        spawnBtn.onHover(() => {
          spawnBtn.color = k.Color.fromArray([120, 240, 160, 255]);
        });

        spawnBtn.onHoverEnd(() => {
          spawnBtn.color = k.Color.fromArray([...UI_COLORS.success, 255]);
        });
      });

      if (agents.length > 6) {
        agentListContainer.add([
          k.text(`... and ${agents.length - 6} more agents`, {
            size: FONT_SIZES.small,
            font: 'pixelFont',
          }),
          k.pos(0, 6 * 65 + 10),
          k.color(...UI_COLORS.textDim),
        ]);
      }
    }

    // Keyboard shortcuts
    k.onKeyPress('escape', () => {
      k.go('networking');
    });

    await loadAgents();
  });

  return {
    start: () => k.go('control'),
  };
}
