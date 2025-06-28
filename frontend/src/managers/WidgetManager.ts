import { Application, FederatedPointerEvent, Graphics } from "pixi.js";
import type { Widget } from "../types/widget";
import { WeatherWidget } from "../widgets/WeatherWidget";
import { TransportWidget } from "../widgets/TransportWidget";
import { displayService } from "../services/displayService";
import { GridService } from "../services/gridService";

export class WidgetManager {
  private widgets: Widget[] = [];
  private pixiApp: Application | null = null;
  private draggedWidget: Widget | null = null;
  private dragOffset = { x: 0, y: 0 };
  private gridService: GridService;
  private showGrid: boolean = false;
  private gridVisualization: Graphics | null = null;
  private snapPreview: Graphics | null = null;

  constructor(app: Application) {
    this.pixiApp = app;
    displayService.setPixiApp(app);

    // Initialize grid with 20px padding and 50px cell size for higher resolution
    this.gridService = new GridService({
      cellSize: 10,
      padding: 20,
      width: 800,
      height: 480,
    });

    this.setupDragHandlers();
    this.createGridVisualization();
    this.createSnapPreview();
  }

  private setupDragHandlers(): void {
    if (!this.pixiApp) return;

    this.pixiApp.stage.eventMode = "static";
    this.pixiApp.stage.on("pointermove", this.onDragMove.bind(this));
    this.pixiApp.stage.on("pointerup", this.onDragEnd.bind(this));
    this.pixiApp.stage.on("pointerupoutside", this.onDragEnd.bind(this));
  }

  private createGridVisualization(): void {
    if (!this.pixiApp) return;

    this.gridVisualization = new Graphics();
    this.pixiApp.stage.addChild(this.gridVisualization);
    this.updateGridVisualization();
  }

  private createSnapPreview(): void {
    if (!this.pixiApp) return;

    this.snapPreview = new Graphics();
    this.pixiApp.stage.addChild(this.snapPreview);
  }

  private updateGridVisualization(): void {
    if (!this.gridVisualization) return;

    this.gridVisualization.clear();

    if (!this.showGrid) return;

    // Draw grid lines with better visibility
    this.gridVisualization.setStrokeStyle({
      width: 2,
      color: 0xdddddd,
      alpha: 0.5,
    });

    // Draw grid points at intersections using the new symmetric method
    this.gridVisualization.setStrokeStyle({
      width: 0,
    });
    this.gridVisualization.setFillStyle({
      color: 0x666666,
      alpha: 0.8,
    });

    const gridPoints = this.gridService.getGridPoints();
    gridPoints.forEach((point) => {
      if (this.gridVisualization) {
        this.gridVisualization.circle(point.x, point.y, 1);
        this.gridVisualization.fill();
      }
    });
  }

  private updateSnapPreview(
    x: number,
    y: number,
    width: number,
    height: number,
    isValid: boolean
  ): void {
    if (!this.snapPreview) return;

    this.snapPreview.clear();

    if (!this.draggedWidget) return;

    // Draw snap preview
    this.snapPreview.setStrokeStyle({
      width: 3,
      color: isValid ? 0x00ff00 : 0xff0000,
      alpha: 0.7,
    });
    this.snapPreview.setFillStyle({
      color: isValid ? 0x00ff00 : 0xff0000,
      alpha: 0.1,
    });
    this.snapPreview.roundRect(x, y, width, height, 8);
    this.snapPreview.fill();
  }

  public toggleGrid(): void {
    this.showGrid = !this.showGrid;
    this.updateGridVisualization();
  }

  public addWeatherWidget(x?: number, y?: number): Widget {
    // Check if update is in progress
    if (displayService.isCurrentlyUpdating()) {
      console.warn("Update in progress, cannot add weather widget");
      throw new Error("Cannot add widget while update is in progress");
    }

    // Find a free position if coordinates not provided
    let finalX = x ?? 20;
    let finalY = y ?? 20;

    if (x === undefined || y === undefined) {
      const freePosition = this.gridService.findNearestFreePosition(
        20,
        20,
        300,
        200
      );
      finalX = freePosition.x;
      finalY = freePosition.y;
    }

    const widget = new WeatherWidget(finalX, finalY);
    this.widgets.push(widget);

    if (this.pixiApp) {
      this.pixiApp.stage.addChild(widget.container);
      widget.container.on("pointerdown", (event) =>
        this.onDragStart(event, widget)
      );
    }

    // Reserve grid space
    this.gridService.reserveGridSpace(
      finalX,
      finalY,
      widget.width,
      widget.height,
      widget.id
    );

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

    // Find a free position if coordinates not provided
    let finalX = x ?? 240;
    let finalY = y ?? 20;

    if (x === undefined || y === undefined) {
      const freePosition = this.gridService.findNearestFreePosition(
        240,
        20,
        200,
        150
      );
      finalX = freePosition.x;
      finalY = freePosition.y;
    }

    const widget = new TransportWidget(finalX, finalY);
    this.widgets.push(widget);

    if (this.pixiApp) {
      this.pixiApp.stage.addChild(widget.container);
      widget.container.on("pointerdown", (event) =>
        this.onDragStart(event, widget)
      );
    }

    // Reserve grid space
    this.gridService.reserveGridSpace(
      finalX,
      finalY,
      widget.width,
      widget.height,
      widget.id
    );

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
      this.gridService.releaseGridSpace(widget.id);
      widget.destroy();
    });
    this.widgets = [];
  }

  public getWidgets(): Widget[] {
    return this.widgets;
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

    // Release grid space temporarily
    this.gridService.releaseGridSpace(widget.id);

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

    // Snap to grid with more responsive behavior
    const snapped = this.gridService.snapToGrid(newX, newY);

    // Check if the snapped position is valid
    const isValid = this.gridService.canPlaceWidget(
      snapped.x,
      snapped.y,
      this.draggedWidget.width,
      this.draggedWidget.height,
      this.draggedWidget.id
    );

    if (isValid) {
      newX = snapped.x;
      newY = snapped.y;
    } else {
      // Find nearest free position
      const nearestFree = this.gridService.findNearestFreePosition(
        newX,
        newY,
        this.draggedWidget.width,
        this.draggedWidget.height
      );
      newX = nearestFree.x;
      newY = nearestFree.y;
    }

    // Constrain to canvas bounds
    newX = Math.max(20, Math.min(800 - this.draggedWidget.width - 20, newX));
    newY = Math.max(20, Math.min(480 - this.draggedWidget.height - 20, newY));

    // Update widget position
    this.draggedWidget.container.x = newX;
    this.draggedWidget.container.y = newY;
    this.draggedWidget.x = newX;
    this.draggedWidget.y = newY;

    // Update snap preview
    this.updateSnapPreview(
      newX,
      newY,
      this.draggedWidget.width,
      this.draggedWidget.height,
      isValid
    );
  }

  private onDragEnd(): void {
    if (this.draggedWidget) {
      // Check if update is in progress
      if (displayService.isCurrentlyUpdating()) {
        console.warn("Update in progress, cannot complete drag operation");
        // Reset the widget to its original position or handle gracefully
        return;
      }

      // Hide snap preview
      if (this.snapPreview) {
        this.snapPreview.clear();
      }

      // Reserve the new grid space
      this.gridService.reserveGridSpace(
        this.draggedWidget.x,
        this.draggedWidget.y,
        this.draggedWidget.width,
        this.draggedWidget.height,
        this.draggedWidget.id
      );

      // Send full image update since widget has moved to a new position
      if (this.pixiApp && this.pixiApp.canvas) {
        displayService.sendFullImage(this.pixiApp.canvas);
      }

      this.draggedWidget = null;
    }
  }

  public destroy(): void {
    this.clearAllWidgets();
    if (this.gridVisualization) {
      this.gridVisualization.destroy();
    }
    if (this.snapPreview) {
      this.snapPreview.destroy();
    }
    this.pixiApp = null;
  }
}
