<template>
  <div class="app">
    <div class="canvas-container">
      <!-- PixiJS Canvas -->
      <canvas ref="canvasRef"></canvas>
      <!-- Update Status -->
      <div class="update-status" :class="{ updating: isUpdating }">
        <p v-if="isUpdating">🔄 Update in progress...</p>
        <p v-else>✅ Ready</p>
      </div>
      <!-- Controls -->
      <div class="controls">
        <button @click="addWeatherWidget" class="btn" :disabled="isUpdating">
          Add Weather Widget
        </button>
        <button @click="addTransportWidget" class="btn" :disabled="isUpdating">
          Add Transport Widget
        </button>
        <button
          @click="sendFullImageToServer"
          class="btn"
          :disabled="isUpdating"
        >
          Send Full Image
        </button>
        <button @click="clearAllWidgets" class="btn" :disabled="isUpdating">
          Clear All
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Application } from "pixi.js";
import { ref, onMounted, onUnmounted } from "vue";
import { WidgetManager } from "./managers/WidgetManager";
import { useWidgetUpdates } from "./composables/useWidgetUpdates";

// Canvas reference
const canvasRef = ref<HTMLCanvasElement | null>(null);

// Widget manager
let widgetManager: WidgetManager | null = null;

// Widget updates composable
const { sendFullImage, isUpdating } = useWidgetUpdates();

// Computed widget count
const widgetCount = ref(0);

// Widget management functions
const addWeatherWidget = () => {
  if (widgetManager) {
    try {
      widgetManager.addWeatherWidget();
      widgetCount.value = widgetManager.getWidgetCount();
    } catch (error) {
      console.error("Failed to add weather widget:", error);
    }
  }
};

const addTransportWidget = () => {
  if (widgetManager) {
    try {
      widgetManager.addTransportWidget();
      widgetCount.value = widgetManager.getWidgetCount();
    } catch (error) {
      console.error("Failed to add transport widget:", error);
    }
  }
};

const clearAllWidgets = () => {
  if (widgetManager) {
    widgetManager.clearAllWidgets();
    widgetCount.value = widgetManager.getWidgetCount();
  }
};

const sendFullImageToServer = async () => {
  if (canvasRef.value) {
    await sendFullImage(canvasRef.value);
  }
};

onMounted(async () => {
  if (!canvasRef.value) return;

  // Initialize PixiJS application
  const app = new Application();
  await app.init({
    resizeTo: canvasRef.value,
    canvas: canvasRef.value,
    background: "#ffffff",
  });

  // Initialize widget manager
  widgetManager = new WidgetManager(app);

  // Force initial render
  app.render();

  // Send initial full image
  setTimeout(() => {
    sendFullImageToServer();
  }, 100);
});

onUnmounted(() => {
  if (widgetManager) {
    widgetManager.destroy();
  }
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

.update-status {
  background: #f8f9fa;
  padding: 10px 20px;
  border-radius: 4px;
  border: 1px solid #dee2e6;
  text-align: center;
  transition: all 0.3s ease;
}

.update-status.updating {
  background: #fff3cd;
  border-color: #ffeaa7;
  color: #856404;
}

.update-status p {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
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

.btn:hover:not(:disabled) {
  background: #0056b3;
}

.btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-secondary {
  background: #6c757d;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
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
