import { k } from './kplayCtx.js';
import { initDashboard } from './scenes/dashboard.js';
import { initNetworkingWorld } from './scenes/networkingWorld.js';
import { FONT_SIZES, UI_COLORS, WORLD_CONFIG } from './config.js';

k.loadFont('pixelFont', './assets/fonts/PixelifySans-VariableFont_wght.ttf');

const networkingWorld = initNetworkingWorld(k);
const dashboard = initDashboard(k);

k.scene('menu', () => {
    k.setBackground(k.Color.fromArray([15, 15, 25, 255]));

    // Animated background grid
    for (let i = 0; i < 20; i++) {
        for (let j = 0; j < 15; j++) {
            const delay = (i + j) * 0.05;
            const dot = k.add([
                k.circle(2),
                k.pos(60 + i * 60, 60 + j * 60),
                k.color(40, 40, 70),
                k.anchor('center'),
                k.opacity(0.3),
                k.z(0),
            ]);

            // Subtle pulse animation
            dot.onUpdate(() => {
                const pulse = Math.sin(k.time() * 2 + delay) * 0.15 + 0.35;
                dot.opacity = pulse;
            });
        }
    }

    // Glowing orbs in background
    const orb1 = k.add([
        k.circle(150),
        k.pos(200, 200),
        k.color(120, 100, 255),
        k.opacity(0.08),
        k.anchor('center'),
        k.z(1),
    ]);

    const orb2 = k.add([
        k.circle(200),
        k.pos(WORLD_CONFIG.width - 250, WORLD_CONFIG.height - 200),
        k.color(255, 100, 120),
        k.opacity(0.06),
        k.anchor('center'),
        k.z(1),
    ]);

    orb1.onUpdate(() => {
        orb1.pos.x = 200 + Math.sin(k.time() * 0.5) * 30;
        orb1.pos.y = 200 + Math.cos(k.time() * 0.3) * 20;
    });

    orb2.onUpdate(() => {
        orb2.pos.x = WORLD_CONFIG.width - 250 + Math.cos(k.time() * 0.4) * 25;
        orb2.pos.y = WORLD_CONFIG.height - 200 + Math.sin(k.time() * 0.6) * 30;
    });

    // Main title with glow effect
    k.add([
        k.text('DOPPEL', { size: FONT_SIZES.title + 4, font: 'pixelFont' }),
        k.pos(WORLD_CONFIG.width / 2, WORLD_CONFIG.height / 3 - 20),
        k.color(120, 100, 255),
        k.anchor('center'),
        k.opacity(0.3),
        k.z(5),
    ]);

    const title = k.add([
        k.text('DOPPEL', { size: FONT_SIZES.title, font: 'pixelFont' }),
        k.pos(WORLD_CONFIG.width / 2, WORLD_CONFIG.height / 3 - 20),
        k.color(255, 255, 255),
        k.anchor('center'),
        k.z(10),
    ]);

    title.onUpdate(() => {
        const glow = Math.sin(k.time() * 3) * 0.1 + 0.9;
        title.opacity = glow;
    });

    // Subtitle
    k.add([
        k.text('AI Networking Simulator', { size: FONT_SIZES.subheading, font: 'pixelFont' }),
        k.pos(WORLD_CONFIG.width / 2, WORLD_CONFIG.height / 3 + 50),
        k.color(...UI_COLORS.textMuted),
        k.anchor('center'),
        k.z(10),
    ]);

    // Tagline
    k.add([
        k.text('Watch AI agents network, converse, and find matches', { size: FONT_SIZES.body, font: 'pixelFont' }),
        k.pos(WORLD_CONFIG.width / 2, WORLD_CONFIG.height / 3 + 90),
        k.color(...UI_COLORS.textDim),
        k.anchor('center'),
        k.z(10),
    ]);

    // Main button - Enter World
    const startBtn = k.add([
        k.rect(280, 60, { radius: 12 }),
        k.pos(WORLD_CONFIG.width / 2, WORLD_CONFIG.height / 2 + 80),
        k.color(...UI_COLORS.primary),
        k.anchor('center'),
        k.area(),
        k.z(10),
        'startBtn',
    ]);

    startBtn.add([
        k.text('Enter World', { size: FONT_SIZES.subheading, font: 'pixelFont' }),
        k.pos(0, 0),
        k.color(255, 255, 255),
        k.anchor('center'),
    ]);

    // Button glow effect
    let btnGlow = 0;
    startBtn.onUpdate(() => {
        btnGlow = Math.sin(k.time() * 4) * 0.08;
    });

    startBtn.onClick(() => {
        networkingWorld.start();
    });

    startBtn.onHover(() => {
        startBtn.color = k.Color.fromArray([...UI_COLORS.primaryHover, 255]);
        startBtn.scale = k.vec2(1.05, 1.05);
    });

    startBtn.onHoverEnd(() => {
        startBtn.color = k.Color.fromArray([...UI_COLORS.primary, 255]);
        startBtn.scale = k.vec2(1, 1);
    });

    // Agent type indicators
    const indicatorY = WORLD_CONFIG.height / 2 + 160;

    // Recruiter indicator
    k.add([
        k.circle(16),
        k.pos(WORLD_CONFIG.width / 2 - 120, indicatorY),
        k.color(255, 120, 100),
        k.anchor('center'),
        k.z(10),
    ]);
    k.add([
        k.text('Recruiters', { size: FONT_SIZES.body, font: 'pixelFont' }),
        k.pos(WORLD_CONFIG.width / 2 - 90, indicatorY),
        k.color(255, 120, 100),
        k.anchor('left'),
        k.z(10),
    ]);

    // Candidate indicator
    k.add([
        k.circle(16),
        k.pos(WORLD_CONFIG.width / 2 + 50, indicatorY),
        k.color(100, 180, 255),
        k.anchor('center'),
        k.z(10),
    ]);
    k.add([
        k.text('Candidates', { size: FONT_SIZES.body, font: 'pixelFont' }),
        k.pos(WORLD_CONFIG.width / 2 + 80, indicatorY),
        k.color(100, 180, 255),
        k.anchor('left'),
        k.z(10),
    ]);

    // Controls hint
    k.add([
        k.text('Press SPACE or click to start', { size: FONT_SIZES.small, font: 'pixelFont' }),
        k.pos(WORLD_CONFIG.width / 2, WORLD_CONFIG.height - 40),
        k.color(...UI_COLORS.textDim),
        k.anchor('center'),
        k.z(10),
    ]);

    k.onKeyPress('space', () => {
        networkingWorld.start();
    });
});

k.go('menu');
