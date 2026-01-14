import kaplay from 'kaplay';

import { WORLD_CONFIG } from './config.js';

export const k = kaplay({
  global: false,
  width: WORLD_CONFIG.width,
  height: WORLD_CONFIG.height,
  touchToMouse: true,
  canvas: document.getElementById('game'),
  debugKey: 'f8',
  buttons: {
    up: { keyboard: ['w', 'up'], gamepad: 'north' },
    down: { keyboard: ['s', 'down'], gamepad: 'south' },
    left: { keyboard: ['a', 'left'], gamepad: 'west' },
    right: { keyboard: ['d', 'right'], gamepad: 'east' },
    dashboard: { keyboard: ['d'] },
    control: { keyboard: ['c'] },
    escape: { keyboard: ['escape'] },
  },
  loadingScreen: false,
  background: WORLD_CONFIG.backgroundColor,
  crisp: false,
});
