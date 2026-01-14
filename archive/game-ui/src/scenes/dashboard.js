import { getConversation, getConversations, getMatches } from '../api.js';
import { WORLD_CONFIG, UI_COLORS, FONT_SIZES, AGENT_COLORS } from '../config.js';

export function initDashboard(k) {
    let conversations = [];
    let matches = [];
    let selectedConversation = null;

    k.scene('dashboard', async () => {
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
            k.color(...UI_COLORS.secondary),
            k.anchor('topleft'),
            k.z(51),
            k.opacity(0.6),
        ]);

        k.add([
            k.text('DASHBOARD', { size: FONT_SIZES.heading, font: 'pixelFont' }),
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

        // Refresh button
        const refreshBtn = k.add([
            k.rect(120, 45, { radius: 8 }),
            k.pos(WORLD_CONFIG.width - 80, 40),
            k.color(...UI_COLORS.success),
            k.anchor('center'),
            k.area(),
            k.z(52),
        ]);

        refreshBtn.add([
            k.text('Refresh', { size: FONT_SIZES.body, font: 'pixelFont' }),
            k.pos(0, 0),
            k.color(255, 255, 255),
            k.anchor('center'),
        ]);

        refreshBtn.onClick(loadData);

        // Tab buttons
        let currentTab = 'matches';

        const tabMatches = k.add([
            k.rect(160, 50, { radius: 8 }),
            k.pos(WORLD_CONFIG.width / 2 - 100, 120),
            k.color(...UI_COLORS.primary),
            k.anchor('center'),
            k.area(),
            k.z(50),
            'tabBtn',
        ]);

        tabMatches.add([
            k.text('Matches', { size: FONT_SIZES.body, font: 'pixelFont' }),
            k.pos(0, 0),
            k.color(255, 255, 255),
            k.anchor('center'),
        ]);

        const tabConvos = k.add([
            k.rect(180, 50, { radius: 8 }),
            k.pos(WORLD_CONFIG.width / 2 + 100, 120),
            k.color(...UI_COLORS.panelLight),
            k.anchor('center'),
            k.area(),
            k.z(50),
            'tabBtn',
        ]);

        tabConvos.add([
            k.text('All Conversations', { size: FONT_SIZES.body, font: 'pixelFont' }),
            k.pos(0, 0),
            k.color(...UI_COLORS.textMuted),
            k.anchor('center'),
        ]);

        // List panel (left side)
        const listPanel = k.add([
            k.rect(500, WORLD_CONFIG.height - 200),
            k.pos(30, 160),
            k.color(...UI_COLORS.panel),
            k.anchor('topleft'),
            k.z(10),
        ]);

        const listContainer = k.add([k.pos(40, 175), k.z(15)]);

        // Detail panel (right side)
        const detailPanel = k.add([
            k.rect(620, WORLD_CONFIG.height - 200),
            k.pos(560, 160),
            k.color(...UI_COLORS.panel),
            k.anchor('topleft'),
            k.z(10),
        ]);

        k.add([
            k.text('Conversation Details', { size: FONT_SIZES.subheading, font: 'pixelFont' }),
            k.pos(870, 185),
            k.color(255, 255, 255),
            k.anchor('center'),
            k.z(15),
        ]);

        const detailContent = k.add([k.pos(580, 220), k.z(15)]);

        async function loadData() {
            try {
                conversations = await getConversations();
                matches = await getMatches();
                renderList();
            } catch (e) {
                console.error('Failed to load data:', e);
            }
        }

        function renderList() {
            listContainer.children.forEach((c) => c.destroy());

            const items = currentTab === 'matches' ? matches : conversations;

            if (items.length === 0) {
                listContainer.add([
                    k.text('No data yet...', { size: FONT_SIZES.body, font: 'pixelFont' }),
                    k.pos(20, 50),
                    k.color(...UI_COLORS.textDim),
                ]);
                listContainer.add([
                    k.text('Start the simulation and spawn agents!', { size: FONT_SIZES.small, font: 'pixelFont' }),
                    k.pos(20, 80),
                    k.color(...UI_COLORS.textDim),
                ]);
                return;
            }

            items.slice(0, 10).forEach((item, i) => {
                const itemBg = listContainer.add([
                    k.rect(470, 70, { radius: 8 }),
                    k.pos(0, i * 80),
                    k.color(...UI_COLORS.panelLight),
                    k.area(),
                    k.z(16),
                ]);

                if (currentTab === 'matches') {
                    const scoreColor =
                        item.score >= 7
                            ? UI_COLORS.success
                            : item.score >= 5
                              ? UI_COLORS.warning
                              : UI_COLORS.danger;

                    // Score badge
                    itemBg.add([
                        k.rect(50, 50, { radius: 8 }),
                        k.pos(15, 10),
                        k.color(...scoreColor),
                        k.opacity(0.2),
                    ]);

                    itemBg.add([
                        k.text(`${item.score}`, { size: FONT_SIZES.subheading, font: 'pixelFont' }),
                        k.pos(40, 25),
                        k.color(...scoreColor),
                        k.anchor('center'),
                    ]);

                    itemBg.add([
                        k.text('/10', { size: FONT_SIZES.tiny, font: 'pixelFont' }),
                        k.pos(40, 45),
                        k.color(...scoreColor),
                        k.anchor('center'),
                    ]);

                    // Names
                    itemBg.add([
                        k.text(item.recruiter_name, { size: FONT_SIZES.body, font: 'pixelFont' }),
                        k.pos(80, 18),
                        k.color(...AGENT_COLORS.recruiter),
                    ]);

                    itemBg.add([
                        k.text('matched with', { size: FONT_SIZES.tiny, font: 'pixelFont' }),
                        k.pos(80, 40),
                        k.color(...UI_COLORS.textDim),
                    ]);

                    itemBg.add([
                        k.text(item.candidate_name, { size: FONT_SIZES.body, font: 'pixelFont' }),
                        k.pos(180, 40),
                        k.color(...AGENT_COLORS.candidate),
                    ]);

                    // Decision badge
                    const decisionColor = item.decision === 'GOOD FIT' ? UI_COLORS.success : UI_COLORS.danger;
                    itemBg.add([
                        k.rect(100, 28, { radius: 4 }),
                        k.pos(355, 21),
                        k.color(...decisionColor),
                        k.opacity(0.3),
                    ]);

                    itemBg.add([
                        k.text(item.decision || 'N/A', { size: FONT_SIZES.tiny, font: 'pixelFont' }),
                        k.pos(405, 35),
                        k.color(...decisionColor),
                        k.anchor('center'),
                    ]);
                } else {
                    const statusColor =
                        item.status === 'completed' ? UI_COLORS.success : UI_COLORS.warning;

                    // Status indicator
                    itemBg.add([
                        k.circle(8),
                        k.pos(25, 35),
                        k.color(...statusColor),
                        k.anchor('center'),
                    ]);

                    // Names
                    itemBg.add([
                        k.text(item.recruiter_name || 'Unknown', { size: FONT_SIZES.body, font: 'pixelFont' }),
                        k.pos(50, 15),
                        k.color(...AGENT_COLORS.recruiter),
                    ]);

                    itemBg.add([
                        k.text('with', { size: FONT_SIZES.tiny, font: 'pixelFont' }),
                        k.pos(50, 38),
                        k.color(...UI_COLORS.textDim),
                    ]);

                    itemBg.add([
                        k.text(item.candidate_name || 'Unknown', { size: FONT_SIZES.body, font: 'pixelFont' }),
                        k.pos(90, 38),
                        k.color(...AGENT_COLORS.candidate),
                    ]);

                    // Score or status
                    const scoreText = item.match_score
                        ? `Score: ${item.match_score}/10`
                        : item.status;
                    itemBg.add([
                        k.text(scoreText, { size: FONT_SIZES.small, font: 'pixelFont' }),
                        k.pos(350, 35),
                        k.color(...statusColor),
                    ]);
                }

                itemBg.onClick(async () => {
                    const convId = item.conversation_id;
                    await showConversationDetail(convId);
                });

                itemBg.onHover(() => {
                    itemBg.color = k.Color.fromArray([55, 55, 75, 255]);
                });

                itemBg.onHoverEnd(() => {
                    itemBg.color = k.Color.fromArray([...UI_COLORS.panelLight, 255]);
                });
            });
        }

        async function showConversationDetail(conversationId) {
            detailContent.children.forEach((c) => c.destroy());

            try {
                const convo = await getConversation(conversationId);
                selectedConversation = convo;

                // Participants
                detailContent.add([
                    k.text('Participants', { size: FONT_SIZES.body, font: 'pixelFont' }),
                    k.pos(0, 0),
                    k.color(...UI_COLORS.textMuted),
                ]);

                // Recruiter
                detailContent.add([
                    k.circle(10),
                    k.pos(10, 35),
                    k.color(...AGENT_COLORS.recruiter),
                    k.anchor('center'),
                ]);
                detailContent.add([
                    k.text(convo.recruiter?.name || 'Unknown Recruiter', { size: FONT_SIZES.body, font: 'pixelFont' }),
                    k.pos(30, 28),
                    k.color(...AGENT_COLORS.recruiter),
                ]);

                // Candidate
                detailContent.add([
                    k.circle(10),
                    k.pos(10, 65),
                    k.color(...AGENT_COLORS.candidate),
                    k.anchor('center'),
                ]);
                detailContent.add([
                    k.text(convo.candidate?.name || 'Unknown Candidate', { size: FONT_SIZES.body, font: 'pixelFont' }),
                    k.pos(30, 58),
                    k.color(...AGENT_COLORS.candidate),
                ]);

                // Match score
                if (convo.match_score) {
                    const scoreColor =
                        convo.match_score >= 7
                            ? UI_COLORS.success
                            : convo.match_score >= 5
                              ? UI_COLORS.warning
                              : UI_COLORS.danger;

                    detailContent.add([
                        k.rect(150, 60, { radius: 8 }),
                        k.pos(400, 10),
                        k.color(...scoreColor),
                        k.opacity(0.15),
                    ]);

                    detailContent.add([
                        k.text(`${convo.match_score}/10`, { size: FONT_SIZES.heading, font: 'pixelFont' }),
                        k.pos(475, 25),
                        k.color(...scoreColor),
                        k.anchor('center'),
                    ]);

                    detailContent.add([
                        k.text(convo.decision || 'Pending', { size: FONT_SIZES.tiny, font: 'pixelFont' }),
                        k.pos(475, 52),
                        k.color(...scoreColor),
                        k.anchor('center'),
                    ]);
                }

                // Transcript header
                detailContent.add([
                    k.rect(580, 2),
                    k.pos(0, 95),
                    k.color(...UI_COLORS.panelBorder),
                    k.opacity(0.3),
                ]);

                detailContent.add([
                    k.text('Conversation Transcript', { size: FONT_SIZES.body, font: 'pixelFont' }),
                    k.pos(0, 115),
                    k.color(...UI_COLORS.textMuted),
                ]);

                // Messages
                const maxMessages = 8;
                const messageStartY = 150;

                convo.messages.slice(0, maxMessages).forEach((msg, i) => {
                    const roleColor =
                        msg.role === 'recruiter' ? AGENT_COLORS.recruiter : AGENT_COLORS.candidate;
                    const truncatedContent =
                        msg.content.length > 55
                            ? msg.content.substring(0, 55) + '...'
                            : msg.content;

                    const msgY = messageStartY + i * 55;

                    // Message background
                    detailContent.add([
                        k.rect(580, 48, { radius: 6 }),
                        k.pos(0, msgY),
                        k.color(...UI_COLORS.panelLight),
                        k.opacity(0.5),
                    ]);

                    // Role indicator
                    detailContent.add([
                        k.rect(4, 40, { radius: 2 }),
                        k.pos(5, msgY + 4),
                        k.color(...roleColor),
                    ]);

                    // Speaker name
                    detailContent.add([
                        k.text(msg.speaker_name, { size: FONT_SIZES.small, font: 'pixelFont' }),
                        k.pos(20, msgY + 8),
                        k.color(...roleColor),
                    ]);

                    // Message content
                    detailContent.add([
                        k.text(truncatedContent, { size: FONT_SIZES.small, font: 'pixelFont' }),
                        k.pos(20, msgY + 28),
                        k.color(...UI_COLORS.text),
                    ]);
                });

                if (convo.messages.length > maxMessages) {
                    detailContent.add([
                        k.text(`... and ${convo.messages.length - maxMessages} more messages`, {
                            size: FONT_SIZES.small,
                            font: 'pixelFont',
                        }),
                        k.pos(0, messageStartY + maxMessages * 55 + 10),
                        k.color(...UI_COLORS.textDim),
                    ]);
                }
            } catch (e) {
                console.error('Failed to load conversation:', e);
                detailContent.add([
                    k.text('Failed to load conversation details', { size: FONT_SIZES.body, font: 'pixelFont' }),
                    k.pos(0, 50),
                    k.color(...UI_COLORS.danger),
                ]);
            }
        }

        tabMatches.onClick(() => {
            currentTab = 'matches';
            tabMatches.color = k.Color.fromArray([...UI_COLORS.primary, 255]);
            tabConvos.color = k.Color.fromArray([...UI_COLORS.panelLight, 255]);
            renderList();
        });

        tabConvos.onClick(() => {
            currentTab = 'conversations';
            tabConvos.color = k.Color.fromArray([...UI_COLORS.primary, 255]);
            tabMatches.color = k.Color.fromArray([...UI_COLORS.panelLight, 255]);
            renderList();
        });

        // Keyboard shortcuts
        k.onKeyPress('escape', () => {
            k.go('networking');
        });

        await loadData();
    });

    return {
        start: () => k.go('dashboard'),
    };
}
