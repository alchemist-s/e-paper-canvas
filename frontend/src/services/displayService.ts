import { Application, Rectangle } from "pixi.js";
import type { WidgetRegion, Widget } from "../types/widget";

class DisplayService {
  private serverUrl: string;
  private pixiApp: Application | null = null;
  private updateCount: number = 0;
  private lastUpdateTime: string = "";
  private isUpdating: boolean = false;
  private updateCallbacks: ((isUpdating: boolean) => void)[] = [];

  constructor(serverUrl: string = "http://192.168.1.111:8000") {
    this.serverUrl = serverUrl;
  }

  public setPixiApp(app: Application): void {
    this.pixiApp = app;
  }

  public isCurrentlyUpdating(): boolean {
    return this.isUpdating;
  }

  public onUpdateStateChange(
    callback: (isUpdating: boolean) => void
  ): () => void {
    this.updateCallbacks.push(callback);
    // Immediately call with current state
    callback(this.isUpdating);

    // Return unsubscribe function
    return () => {
      const index = this.updateCallbacks.indexOf(callback);
      if (index > -1) {
        this.updateCallbacks.splice(index, 1);
      }
    };
  }

  private setUpdateState(isUpdating: boolean): void {
    this.isUpdating = isUpdating;
    this.updateCallbacks.forEach((callback) => callback(isUpdating));
  }

  public async sendRegionUpdate(
    region: WidgetRegion,
    widget: Widget
  ): Promise<void> {
    if (this.isUpdating) {
      console.warn("Update in progress, skipping region update");
      return;
    }

    try {
      this.setUpdateState(true);

      if (!this.pixiApp) return;

      // Call the region's update function to ensure content is current
      if (region.updateFunction) {
        region.updateFunction();
      }

      // Force a rerender to ensure all text changes are applied
      this.pixiApp.render();

      // Add a small delay to ensure text rendering is complete
      await new Promise((resolve) => setTimeout(resolve, 10));

      // Force another render to capture any pending changes
      this.pixiApp.render();

      console.log(`Force rerender completed for region: ${region.id}`);

      const tempCanvas = this.pixiApp.renderer.extract.canvas({
        target: this.pixiApp.stage,
        frame: new Rectangle(
          widget.x + region.x,
          widget.y + region.y,
          region.width,
          region.height
        ),
        clearColor: 0xffffff,
      });
      const response = await fetch(`${this.serverUrl}/update-regions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          regions: [
            {
              x: widget.x + region.x,
              y: widget.y + region.y,
              width: region.width,
              height: region.height,
              image_data: tempCanvas.toDataURL
                ? tempCanvas.toDataURL("image/png")
                : "",
            },
          ],
        }),
      });

      if (response.ok) {
        const result = await response.json();
        this.lastUpdateTime = new Date().toLocaleTimeString();
        this.updateCount++;
      } else {
        console.error("Failed to send region update:", response.statusText);
      }
    } catch (error) {
      console.error("Error sending region update:", error);
    } finally {
      this.setUpdateState(false);
    }
  }

  public async sendMultipleRegionUpdates(
    regions: WidgetRegion[],
    widget: Widget
  ): Promise<void> {
    if (this.isUpdating) {
      console.warn("Update in progress, skipping multiple region updates");
      return;
    }

    if (regions.length === 0) return;

    try {
      this.setUpdateState(true);

      if (!this.pixiApp) return;

      // Call all region update functions to ensure content is current
      for (const region of regions) {
        if (region.updateFunction) {
          region.updateFunction();
        }
      }

      // Force a rerender to ensure all text changes are applied
      this.pixiApp.render();

      // Add a small delay to ensure text rendering is complete
      await new Promise((resolve) => setTimeout(resolve, 10));

      // Force another render to capture any pending changes
      this.pixiApp.render();

      console.log(`Force rerender completed for ${regions.length} regions`);

      // Extract all regions
      const regionUpdates = [];
      for (const region of regions) {
        const tempCanvas = this.pixiApp.renderer.extract.canvas({
          target: this.pixiApp.stage,
          frame: new Rectangle(
            widget.x + region.x,
            widget.y + region.y,
            region.width,
            region.height
          ),
          clearColor: 0xffffff,
        });

        regionUpdates.push({
          x: widget.x + region.x,
          y: widget.y + region.y,
          width: region.width,
          height: region.height,
          image_data: tempCanvas.toDataURL
            ? tempCanvas.toDataURL("image/png")
            : "",
        });
      }

      const response = await fetch(`${this.serverUrl}/update-regions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          regions: regionUpdates,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        this.lastUpdateTime = new Date().toLocaleTimeString();
        this.updateCount++;
      } else {
        console.error(
          "Failed to send multiple region updates:",
          response.statusText
        );
      }
    } catch (error) {
      console.error("Error sending multiple region updates:", error);
    } finally {
      this.setUpdateState(false);
    }
  }

  public async sendFullImage(canvas: HTMLCanvasElement): Promise<void> {
    if (this.isUpdating) {
      console.warn("Update in progress, skipping full image update");
      return;
    }

    try {
      this.setUpdateState(true);

      if (!this.pixiApp) return;
      this.pixiApp.render();
      const base64Image = canvas.toDataURL("image/png");
      await fetch(`${this.serverUrl}/update-display`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ image_data: base64Image }),
      });

      this.lastUpdateTime = new Date().toLocaleTimeString();
      this.updateCount++;
    } catch (error) {
      console.error("Error sending to server:", error);
    } finally {
      this.setUpdateState(false);
    }
  }

  public getUpdateCount(): number {
    return this.updateCount;
  }

  public getLastUpdateTime(): string {
    return this.lastUpdateTime;
  }
}

// Export singleton instance
export const displayService = new DisplayService();
