import { SPEECH_BUBBLE_CONFIG, FONT_SIZES, AGENT_COLORS } from '../config.js';

export function createSpeechBubble(k, text, speakerName, role) {
    const maxWidth = SPEECH_BUBBLE_CONFIG.maxWidth;
    const padding = SPEECH_BUBBLE_CONFIG.padding;
    const fontSize = SPEECH_BUBBLE_CONFIG.fontSize;

    // Show more text for better readability
    const displayText = text.length > 150 ? text.substring(0, 150) + '...' : text;

    const lines = wrapText(displayText, maxWidth - padding * 2, fontSize);
    const textHeight = lines.length * (fontSize + 6);
    const headerHeight = fontSize + 12;
    const bubbleHeight = textHeight + padding * 2 + headerHeight;
    const bubbleWidth = maxWidth;

    const roleColor = AGENT_COLORS[role] || [150, 150, 150];
    const isRecruiter = role === 'recruiter';

    // Main bubble container
    const bubble = k.add([
        k.rect(bubbleWidth, bubbleHeight, { radius: 12 }),
        k.pos(0, 0),
        k.color(255, 255, 255),
        k.outline(3, k.Color.fromArray([...roleColor, 255])),
        k.anchor('bot'),
        k.z(100),
        k.opacity(0),
        'speechBubble',
    ]);

    // Fade in animation
    k.tween(0, 1, 0.2, (v) => bubble.opacity = v);

    // Header background
    bubble.add([
        k.rect(bubbleWidth - 4, headerHeight, { radius: [10, 10, 0, 0] }),
        k.pos(0, -bubbleHeight + 2 + headerHeight / 2),
        k.color(...roleColor),
        k.anchor('center'),
        k.opacity(0.15),
    ]);

    // Role icon
    const roleIcon = isRecruiter ? 'R' : 'C';
    bubble.add([
        k.circle(12),
        k.pos(-bubbleWidth / 2 + padding + 12, -bubbleHeight + padding + headerHeight / 2),
        k.color(...roleColor),
        k.anchor('center'),
    ]);

    bubble.add([
        k.text(roleIcon, { size: FONT_SIZES.tiny, font: 'pixelFont' }),
        k.pos(-bubbleWidth / 2 + padding + 12, -bubbleHeight + padding + headerHeight / 2),
        k.color(255, 255, 255),
        k.anchor('center'),
    ]);

    // Speaker name
    bubble.add([
        k.text(speakerName, { size: fontSize, font: 'pixelFont' }),
        k.pos(-bubbleWidth / 2 + padding + 30, -bubbleHeight + padding + headerHeight / 2),
        k.color(...roleColor),
        k.anchor('left'),
    ]);

    // Message text - each line
    lines.forEach((line, i) => {
        bubble.add([
            k.text(line, { size: fontSize, font: 'pixelFont' }),
            k.pos(
                -bubbleWidth / 2 + padding,
                -bubbleHeight + headerHeight + padding + 8 + i * (fontSize + 6)
            ),
            k.color(...SPEECH_BUBBLE_CONFIG.textColor),
            k.anchor('topleft'),
        ]);
    });

    // Speech bubble pointer (triangle)
    bubble.add([
        k.polygon([
            k.vec2(-12, 0),
            k.vec2(12, 0),
            k.vec2(0, 16),
        ]),
        k.pos(0, 0),
        k.color(255, 255, 255),
        k.anchor('top'),
    ]);

    // Pointer outline
    bubble.add([
        k.polygon([
            k.vec2(-14, -2),
            k.vec2(14, -2),
            k.vec2(0, 18),
        ]),
        k.pos(0, 0),
        k.color(...roleColor),
        k.anchor('top'),
        k.z(-1),
    ]);

    return bubble;
}

function wrapText(text, maxWidth, fontSize) {
    const words = text.split(' ');
    const lines = [];
    let currentLine = '';
    // Adjusted for better character estimation with pixel font
    const charsPerLine = Math.floor(maxWidth / (fontSize * 0.55));

    for (const word of words) {
        const testLine = currentLine ? `${currentLine} ${word}` : word;
        if (testLine.length > charsPerLine) {
            if (currentLine) {
                lines.push(currentLine);
                currentLine = word;
            } else {
                // Word is too long, break it
                lines.push(word.substring(0, charsPerLine));
                currentLine = word.substring(charsPerLine);
            }
        } else {
            currentLine = testLine;
        }
    }

    if (currentLine) {
        lines.push(currentLine);
    }

    // Allow more lines for better readability
    return lines.slice(0, 5);
}
