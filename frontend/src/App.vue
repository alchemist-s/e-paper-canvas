<template>
  <div class="app">
    <div class="canvas-container">
      <!-- PixiJS Canvas -->
      <canvas ref="canvasRef"></canvas>
      <!-- Debug Info -->
      <div class="debug-info">
        <p>Counter: {{ counter }}</p>
        <p>Last update: {{ lastUpdateTime }}</p>
        <p>Update count: {{ updateCount }}</p>
      </div>
      <!-- Controls -->
      <div class="controls">
        <button @click="incrementCounter" class="btn">Increment Counter</button>
        <button @click="resetCounter" class="btn">Reset Counter</button>
        <button @click="sendFullImage" class="btn">Send Full Image</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  Application,
  Text,
  Container,
  Rectangle,
  Graphics,
  Sprite,
  Assets,
  Texture,
} from "pixi.js";
import { ref, onMounted } from "vue";

const canvasRef = ref<HTMLCanvasElement | null>(null);
const serverUrl = ref<string>("http://192.168.1.111:8000");
// const serverUrl = ref<string>("http://localhost:8000");
let pixiApp: Application | null = null;
const counter = ref<number>(1);
const lastUpdateTime = ref<string>("");
const updateCount = ref<number>(0);

// Pixi objects
let titleText: Text | null = null;
let counterText: Text | null = null;
let counterContainer: Container | null = null;

const sendRegionUpdate = async (pixiObject: Text): Promise<void> => {
  try {
    if (!canvasRef.value || !pixiApp) return;
    pixiApp.render();
    const tempCanvas = pixiApp.renderer.extract.canvas({
      target: pixiApp.stage,
      /* Because our text is centered via anchor, we need to offset the bounds by the width of the text */
      frame: new Rectangle(
        pixiObject.x + pixiObject.bounds.minX,
        pixiObject.y + pixiObject.bounds.minY,
        pixiObject.bounds.maxX - pixiObject.bounds.minX,
        pixiObject.bounds.maxY - pixiObject.bounds.minY
      ),
      clearColor: 0xffffff,
    });

    const response = await fetch(`${serverUrl.value}/update-regions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        regions: [
          {
            x: pixiObject.x + pixiObject.bounds.minX,
            y: pixiObject.y + pixiObject.bounds.minY,
            width: pixiObject.bounds.maxX - pixiObject.bounds.minX,
            height: pixiObject.bounds.maxY - pixiObject.bounds.minY,
            image_data: tempCanvas.toDataURL
              ? tempCanvas.toDataURL("image/png")
              : "",
          },
        ],
      }),
    });

    if (response.ok) {
      const result = await response.json();
      lastUpdateTime.value = new Date().toLocaleTimeString();
      updateCount.value++;
    } else {
      console.error("Failed to send region update:", response.statusText);
    }
  } catch (error) {
    console.error("Error sending region update:", error);
  }
};

const sendFullImage = async (): Promise<void> => {
  try {
    if (!canvasRef.value || !pixiApp) return;
    pixiApp.render();
    const base64Image = canvasRef.value.toDataURL("image/png");
    await fetch(`${serverUrl.value}/update-display`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ image_data: base64Image }),
    });

    lastUpdateTime.value = new Date().toLocaleTimeString();
    updateCount.value++;
  } catch (error) {
    console.error("Error sending to server:", error);
  }
};

const incrementCounter = (): void => {
  if (counter.value < 10) {
    counter.value++;
    updateCounterText();
  }
};

const resetCounter = (): void => {
  counter.value = 1;
  updateCounterText();
};

const updateCounterText = (): void => {
  if (counterText) {
    counterText.text = counter.value.toString();
    sendRegionUpdate(counterText);
  } else {
    console.error("counterText is null!");
  }
};

onMounted(async () => {
  if (!canvasRef.value) return;

  const app = new Application();
  await app.init({
    resizeTo: canvasRef.value,
    canvas: canvasRef.value,
    background: "#ffffff",
  });

  pixiApp = app;
  titleText = new Text({
    text: "Counter",
    style: {
      fill: "#000000",
      fontSize: 48,
      fontWeight: "bold",
    },
    anchor: 0.5,
    x: 400,
    y: 200,
  });

  counterText = new Text({
    text: counter.value.toString(),
    style: {
      fill: "#000000",
      fontSize: 72,
      fontWeight: "bold",
    },
    anchor: 0.5,
    x: 400,
    y: 300,
  });
  counterContainer = new Container();
  counterContainer.addChild(titleText);
  counterContainer.addChild(counterText);

  app.stage.addChild(counterContainer);

  // Force initial render
  app.render();

  // Send initial full image
  setTimeout(() => {
    sendFullImage();
  }, 100);
});
</script>

<style scoped>
.app {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f0f0f0;
  padding: 20px;
}

.canvas-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

canvas {
  border: 2px solid #333;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  width: 800px;
  height: 480px;
}

.controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.2s;
}

.btn:hover {
  background: #0056b3;
}

.debug-info {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  text-align: center;
}

.debug-info p {
  margin: 5px 0;
  font-size: 14px;
  color: #666;
}
</style>
