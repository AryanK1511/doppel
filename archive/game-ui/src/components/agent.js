import { AGENT_COLORS, FONT_SIZES } from '../config.js';

export function createAgentSprite(k, agentData, onSelect) {
  const color = AGENT_COLORS[agentData.agent_type] || [200, 200, 200];
  const isRecruiter = agentData.agent_type === 'recruiter';

  const agent = k.add([
    k.circle(28),
    k.pos(agentData.x, agentData.y),
    k.color(...color),
    k.anchor('center'),
    k.z(10),
    k.opacity(1),
    k.area(),
    {
      agentId: agentData.agent_id,
      agentName: agentData.name,
      agentType: agentData.agent_type,
      targetX: agentData.x,
      targetY: agentData.y,
      currentBubble: null,
      isTalking: false,
      isSelected: false,
    },
    'agent',
  ]);

  // Outer glow ring
  const glowRing = agent.add([
    k.circle(36),
    k.pos(0, 0),
    k.color(...color),
    k.anchor('center'),
    k.opacity(0.2),
    k.z(-1),
  ]);

  // Selection ring (hidden by default)
  const selectionRing = agent.add([
    k.circle(45),
    k.pos(0, 0),
    k.color(255, 255, 100),
    k.anchor('center'),
    k.opacity(0),
    k.z(-2),
  ]);

  // Inner highlight
  agent.add([
    k.circle(12),
    k.pos(-6, -6),
    k.color(255, 255, 255),
    k.anchor('center'),
    k.opacity(0.25),
  ]);

  // Name label with background
  const nameContainer = agent.add([
    k.rect(agentData.name.length * 10 + 16, 26, { radius: 6 }),
    k.pos(0, -50),
    k.color(20, 20, 35),
    k.anchor('center'),
    k.opacity(0.9),
  ]);

  nameContainer.add([
    k.text(agentData.name, { size: FONT_SIZES.small, font: 'pixelFont' }),
    k.pos(0, 0),
    k.color(255, 255, 255),
    k.anchor('center'),
  ]);

  // Type badge
  const typeLabel = isRecruiter ? 'R' : 'C';
  const badgeColor = isRecruiter ? [180, 80, 70] : [70, 130, 200];

  agent.add([
    k.circle(14),
    k.pos(20, -20),
    k.color(...badgeColor),
    k.anchor('center'),
    k.outline(2, k.Color.fromArray([255, 255, 255, 180])),
  ]);

  agent.add([
    k.text(typeLabel, { size: FONT_SIZES.tiny, font: 'pixelFont' }),
    k.pos(20, -20),
    k.color(255, 255, 255),
    k.anchor('center'),
  ]);

  // Click to select
  agent.onClick(() => {
    if (onSelect) {
      onSelect(agent);
    }
  });

  // Hover effect
  agent.onHover(() => {
    if (!agent.isSelected) {
      glowRing.opacity = 0.4;
    }
  });

  agent.onHoverEnd(() => {
    if (!agent.isSelected) {
      glowRing.opacity = 0.2;
    }
  });

  // Animate glow when talking or selected
  agent.onUpdate(() => {
    if (agent.isSelected) {
      // Pulsing selection ring
      const pulse = Math.sin(k.time() * 5) * 0.2 + 0.6;
      selectionRing.opacity = pulse;
      glowRing.opacity = 0.5;
    } else if (agent.isTalking) {
      const pulse = Math.sin(k.time() * 6) * 0.15 + 0.35;
      glowRing.opacity = pulse;
      glowRing.radius = 36 + Math.sin(k.time() * 4) * 4;
      selectionRing.opacity = 0;
    } else {
      glowRing.opacity = 0.2;
      glowRing.radius = 36;
      selectionRing.opacity = 0;
    }
  });

  // Method to set selection state
  agent.setSelected = (selected) => {
    agent.isSelected = selected;
  };

  return agent;
}

export function updateAgentPosition(k, agent, newX, newY, state) {
  // Only update target if not selected (manual control)
  if (!agent.isSelected) {
    agent.targetX = newX;
    agent.targetY = newY;
  }
  agent.isTalking = state === 'talking';

  if (state === 'talking') {
    const baseColor = AGENT_COLORS[agent.agentType] || [200, 200, 200];
    agent.color = k.Color.fromArray([
      Math.min(255, baseColor[0] + 60),
      Math.min(255, baseColor[1] + 60),
      Math.min(255, baseColor[2] + 60),
      255,
    ]);
  } else {
    const baseColor = AGENT_COLORS[agent.agentType] || [200, 200, 200];
    agent.color = k.Color.fromArray([...baseColor, 255]);
  }
}
