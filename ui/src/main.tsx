import kaplay from 'kaplay';

const k = kaplay({
  width: 800,
  height: 600,
  background: [135, 206, 235],
  global: false,
});

const character1 = k.add([
  k.rect(40, 40),
  k.color(255, 100, 100),
  k.pos(200, 200),
  k.area(),
  {
    speed: 100,
    direction: k.vec2(1, 0),
    changeDirectionTimer: 0,
    changeInterval: 2,
  },
]);

const character2 = k.add([
  k.rect(40, 40),
  k.color(100, 100, 255),
  k.pos(400, 300),
  k.area(),
  {
    speed: 100,
    direction: k.vec2(-1, 0),
    changeDirectionTimer: 0,
    changeInterval: 2,
  },
]);

function getRandomDirection() {
  const angle = k.rand(0, Math.PI * 2);
  return k.vec2(Math.cos(angle), Math.sin(angle));
}

function updateCharacter(character: typeof character1) {
  const deltaTime = k.dt();
  character.changeDirectionTimer += deltaTime;

  if (character.changeDirectionTimer >= character.changeInterval) {
    character.direction = getRandomDirection();
    character.changeDirectionTimer = 0;
    character.changeInterval = k.rand(1, 3);
  }

  const newPos = character.pos.add(character.direction.scale(character.speed * deltaTime));

  if (newPos.x < 20 || newPos.x > 780) {
    character.direction.x *= -1;
  }
  if (newPos.y < 20 || newPos.y > 580) {
    character.direction.y *= -1;
  }

  character.pos = character.pos.add(character.direction.scale(character.speed * deltaTime));

  character.pos.x = k.clamp(character.pos.x, 20, 780);
  character.pos.y = k.clamp(character.pos.y, 20, 580);
}

k.onUpdate(() => {
  updateCharacter(character1);
  updateCharacter(character2);
});
