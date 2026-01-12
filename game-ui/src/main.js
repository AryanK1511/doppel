import { k } from './kplayCtx.js';

k.loadSprite(
  'bean',
  'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiIGZpbGw9IiM0Y2FmNTAiLz48L3N2Zz4='
);

k.scene('game', () => {
  const player = k.add([k.sprite('bean'), k.pos(80, 80), k.area(), k.body()]);

  k.add([
    k.rect(k.width(), 48),
    k.pos(0, k.height() - 48),
    k.area(),
    k.body({ isStatic: true }),
    k.color(127, 200, 255),
  ]);

  for (let i = 0; i < 3; i++) {
    const x = k.rand(0, k.width());
    const y = k.rand(0, k.height() / 2);
    k.add([k.rect(48, 48), k.pos(x, y), k.area(), k.body({ isStatic: true }), k.color(255, 180, 255), 'platform']);
  }

  k.onKeyPress('space', () => {
    if (player.isGrounded()) {
      player.jump();
    }
  });

  k.onKeyDown('left', () => {
    player.move(-200, 0);
  });

  k.onKeyDown('right', () => {
    player.move(200, 0);
  });

  player.onCollide('platform', () => {
    k.addKaboom(player.pos);
    k.shake(5);
  });
});

k.go('game');
