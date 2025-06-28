import { ref, onUnmounted } from "vue";
import { displayService } from "../services/displayService";
import type { Widget } from "../types/widget";

export function useWidgetUpdates() {
  const updateCount = ref(0);
  const lastUpdateTime = ref("");
  const isUpdating = ref(false);

  // Update stats from display service
  const updateStats = () => {
    updateCount.value = displayService.getUpdateCount();
    lastUpdateTime.value = displayService.getLastUpdateTime();
  };

  // Subscribe to update state changes
  const unsubscribe = displayService.onUpdateStateChange((updating) => {
    isUpdating.value = updating;
  });

  // Update all regions for a widget
  const updateWidgetRegions = async (widget: Widget): Promise<void> => {
    if (isUpdating.value) {
      console.warn("Update in progress, skipping widget region update");
      return;
    }

    for (const region of widget.regions) {
      await displayService.sendRegionUpdate(region, widget);
    }
    updateStats();
  };

  // Update specific region
  const updateRegion = async (region: any, widget: Widget): Promise<void> => {
    if (isUpdating.value) {
      console.warn("Update in progress, skipping region update");
      return;
    }

    await displayService.sendRegionUpdate(region, widget);
    updateStats();
  };

  // Send full image update
  const sendFullImage = async (canvas: HTMLCanvasElement): Promise<void> => {
    if (isUpdating.value) {
      console.warn("Update in progress, skipping full image update");
      return;
    }

    await displayService.sendFullImage(canvas);
    updateStats();
  };

  // Start periodic stats updates
  const statsInterval = setInterval(updateStats, 1000);

  onUnmounted(() => {
    if (statsInterval) {
      clearInterval(statsInterval);
    }
    if (unsubscribe) {
      unsubscribe();
    }
  });

  return {
    updateCount,
    lastUpdateTime,
    isUpdating,
    updateWidgetRegions,
    updateRegion,
    sendFullImage,
    updateStats,
  };
}
