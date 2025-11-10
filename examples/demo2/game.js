document.addEventListener("DOMContentLoaded", () => {
  const startScreen = document.getElementById("start-screen");
  const gameContainer = document.getElementById("game-container");
  const gameOverScreen = document.getElementById("game-over-screen");
  const startButton = document.getElementById("start-button");
  const restartButton = document.getElementById("restart-button");
  const finalScore = document.getElementById("final-score");
  const canvas = document.getElementById("game-canvas");
  const ctx = canvas.getContext("2d");

  let bird, pipes, score, animationId;
  const gravity = 0.2;
  const birdWidth = 34;
  const birdHeight = 24;
  const pipeWidth = 52;
  const pipeGap = 360;

  canvas.width = 960;
  canvas.height = 640;

  function init() {
    bird = { x: 50, y: canvas.height / 2, velocity: 0 };
    pipes = [];
    score = 0;
    spawnPipes();
  }

  function startGame() {
    startScreen.classList.add("hidden");
    gameContainer.classList.remove("hidden");
    init();
    gameLoop();
  }

  function gameLoop() {
    update();
    draw();
    if (!checkCollision()) {
      animationId = requestAnimationFrame(gameLoop);
    } else {
      endGame();
    }
  }

  function update() {
    bird.velocity += gravity;
    bird.y += bird.velocity;

    if (bird.y + birdHeight >= canvas.height) {
      bird.y = canvas.height - birdHeight;
      endGame();
    }

    pipes.forEach((pipe) => {
      pipe.x -= 1;
    });

    if (pipes[0].x < -pipeWidth) {
      pipes.shift();
      pipes.shift();
      spawnPipes();
      score++;
    }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw bird
    ctx.fillStyle = "#ffeb3b";
    ctx.fillRect(bird.x, bird.y, birdWidth, birdHeight);

    // Draw pipes
    ctx.fillStyle = "#8bc34a";
    pipes.forEach((pipe) => {
      ctx.fillRect(pipe.x, pipe.y, pipeWidth, pipe.height);
    });

    // Draw score
    ctx.fillStyle = "#fff";
    ctx.font = "20px Arial";
    ctx.fillText(`Score: ${score}`, 10, 25);
  }

  function spawnPipes() {
    const pipeHeight =
      Math.floor(Math.random() * (canvas.height - pipeGap - 20)) + 20;
    const pipeY2 = pipeHeight + pipeGap;

    pipes.push({ x: canvas.width, y: 0, height: pipeHeight });
    pipes.push({ x: canvas.width, y: pipeY2, height: canvas.height - pipeY2 });
  }

  function checkCollision() {
    for (let i = 0; i < pipes.length; i++) {
      const pipe = pipes[i];
      if (
        bird.x < pipe.x + pipeWidth &&
        bird.x + birdWidth > pipe.x &&
        bird.y < pipe.y + pipe.height &&
        bird.y + birdHeight > pipe.y
      ) {
        return true;
      }
    }
    return false;
  }

  function endGame() {
    cancelAnimationFrame(animationId);
    gameContainer.classList.add("hidden");
    gameOverScreen.classList.remove("hidden");
    finalScore.textContent = score;
  }

  function restartGame() {
    gameOverScreen.classList.add("hidden");
    startScreen.classList.remove("hidden");
  }

  function flap() {
    bird.velocity = -8;
  }

  startButton.addEventListener("click", startGame);
  restartButton.addEventListener("click", restartGame);
  document.addEventListener("keydown", (e) => {
    if (e.code === "Space") {
      flap();
    }
  });
  document.addEventListener("touchstart", flap);
});
