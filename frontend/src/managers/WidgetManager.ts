import { Application, FederatedPointerEvent } from "pixi.js";
import type { Widget } from "../types/widget";
import { WeatherWidget } from "../widgets/WeatherWidget";
import { TransportWidget } from "../widgets/TransportWidget";
import { displayService } from "../services/displayService";

export class WidgetManager {
  private widgets: Widget[] = [];
  private pixiApp: Application | null = null;
  private draggedWidget: Widget | null = null;
  private dragOffset = { x: 0, y: 0 };

  constructor(app: Application) {
    this.pixiApp = app;
    displayService.setPixiApp(app);

    this.setupDragHandlers();
  }

  private setupDragHandlers(): void {
    if (!this.pixiApp) return;

    this.pixiApp.stage.eventMode = "static";
    this.pixiApp.stage.on("pointermove", this.onDragMove.bind(this));
    this.pixiApp.stage.on("pointerup", this.onDragEnd.bind(this));
    this.pixiApp.stage.on("pointerupoutside", this.onDragEnd.bind(this));
  }

  public addWeatherWidget(x?: number, y?: number): Widget {
    // Check if update is in progress
    if (displayService.isCurrentlyUpdating()) {
      console.warn("Update in progress, cannot add weather widget");
      throw new Error("Cannot add widget while update is in progress");
    }

    // Center the widget on the canvas if coordinates not provided
    let finalX = x ?? (800 - 150) / 2; // Center horizontally
    let finalY = y ?? (480 - 110) / 2; // Center vertically

    const widget = new WeatherWidget(finalX, finalY);
    this.widgets.push(widget);

    if (this.pixiApp) {
      this.pixiApp.stage.addChild(widget.container);
      widget.container.on("pointerdown", (event) =>
        this.onDragStart(event, widget)
      );
    }

    // Send full image update since new widget was added
    setTimeout(() => {
      if (this.pixiApp && this.pixiApp.canvas) {
        displayService.sendFullImage(this.pixiApp.canvas);
      }
    }, 100);

    return widget;
  }

  public addTransportWidget(x?: number, y?: number): Widget {
    // Check if update is in progress
    if (displayService.isCurrentlyUpdating()) {
      console.warn("Update in progress, cannot add transport widget");
      throw new Error("Cannot add widget while update is in progress");
    }

    // Center the widget on the canvas if coordinates not provided
    let finalX = x ?? (800 - 600) / 2; // Center horizontally
    let finalY = y ?? (480 - 200) / 2; // Center vertically

    const widget = new TransportWidget(finalX, finalY);
    this.widgets.push(widget);

    if (this.pixiApp) {
      this.pixiApp.stage.addChild(widget.container);
      widget.container.on("pointerdown", (event) =>
        this.onDragStart(event, widget)
      );
    }

    // Send full image update since new widget was added
    setTimeout(() => {
      if (this.pixiApp && this.pixiApp.canvas) {
        displayService.sendFullImage(this.pixiApp.canvas);
      }
    }, 100);

    return widget;
  }

  public clearAllWidgets(): void {
    // Check if update is in progress
    if (displayService.isCurrentlyUpdating()) {
      console.warn("Update in progress, cannot clear widgets");
      return;
    }

    this.widgets.forEach((widget) => {
      widget.destroy();
    });
    this.widgets = [];
  }

  public getWidgetCount(): number {
    return this.widgets.length;
  }

  private onDragStart(event: FederatedPointerEvent, widget: Widget): void {
    // Check if update is in progress
    if (displayService.isCurrentlyUpdating()) {
      console.warn("Update in progress, cannot start dragging");
      return;
    }

    this.draggedWidget = widget;
    const localPos = event.getLocalPosition(widget.container.parent);
    this.dragOffset.x = localPos.x - widget.container.x;
    this.dragOffset.y = localPos.y - widget.container.y;

    // Bring to front by reordering in the stage
    if (this.pixiApp && widget.container.parent) {
      widget.container.parent.removeChild(widget.container);
      this.pixiApp.stage.addChild(widget.container);
    }
  }

  private onDragMove(event: FederatedPointerEvent): void {
    if (!this.draggedWidget || !this.pixiApp) return;

    // Check if update is in progress
    if (displayService.isCurrentlyUpdating()) {
      console.warn("Update in progress, cannot continue dragging");
      return;
    }

    const localPos = event.getLocalPosition(this.pixiApp.stage);
    let newX = localPos.x - this.dragOffset.x;
    let newY = localPos.y - this.dragOffset.y;

    // Constrain to canvas bounds
    newX = Math.max(0, Math.min(800 - this.draggedWidget.width, newX));
    newY = Math.max(0, Math.min(480 - this.draggedWidget.height, newY));

    // Update widget position
    this.draggedWidget.container.x = newX;
    this.draggedWidget.container.y = newY;
    this.draggedWidget.x = newX;
    this.draggedWidget.y = newY;
  }

  private onDragEnd(): void {
    if (this.draggedWidget) {
      // Check if update is in progress
      if (displayService.isCurrentlyUpdating()) {
        console.warn("Update in progress, cannot complete drag operation");
        return;
      }

      // Send full image update since widget has moved to a new position
      if (this.pixiApp && this.pixiApp.canvas) {
        displayService.sendFullImage(this.pixiApp.canvas);
      }

      this.draggedWidget = null;
    }
  }

  public destroy(): void {
    this.clearAllWidgets();
    this.pixiApp = null;
  }
}
