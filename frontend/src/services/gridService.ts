import type { GridPoint, GridConfig } from "../types/widget";

export class GridService {
  private grid: GridPoint[][] = [];
  private config: GridConfig;

  constructor(config: GridConfig) {
    this.config = config;
    this.initializeGrid();
  }

  private initializeGrid(): void {
    // Calculate available space after padding
    const availableWidth = this.config.width - this.config.padding * 2;
    const availableHeight = this.config.height - this.config.padding * 2;

    // Calculate number of cells that fit
    const cols = Math.floor(availableWidth / this.config.cellSize);
    const rows = Math.floor(availableHeight / this.config.cellSize);

    // Calculate centering offsets to make grid symmetric
    const totalGridWidth = cols * this.config.cellSize;
    const totalGridHeight = rows * this.config.cellSize;
    const offsetX = (availableWidth - totalGridWidth) / 2;
    const offsetY = (availableHeight - totalGridHeight) / 2;

    this.grid = [];
    for (let row = 0; row < rows; row++) {
      this.grid[row] = [];
      for (let col = 0; col < cols; col++) {
        this.grid[row][col] = {
          x: this.config.padding + offsetX + col * this.config.cellSize,
          y: this.config.padding + offsetY + row * this.config.cellSize,
          occupied: false,
        };
      }
    }
  }

  public snapToGrid(x: number, y: number): { x: number; y: number } {
    // Calculate available space and offsets
    const availableWidth = this.config.width - this.config.padding * 2;
    const availableHeight = this.config.height - this.config.padding * 2;
    const cols = Math.floor(availableWidth / this.config.cellSize);
    const rows = Math.floor(availableHeight / this.config.cellSize);
    const totalGridWidth = cols * this.config.cellSize;
    const totalGridHeight = rows * this.config.cellSize;
    const offsetX = (availableWidth - totalGridWidth) / 2;
    const offsetY = (availableHeight - totalGridHeight) / 2;

    // Calculate grid position
    const adjustedX = x - this.config.padding - offsetX;
    const adjustedY = y - this.config.padding - offsetY;
    const col = Math.round(adjustedX / this.config.cellSize);
    const row = Math.round(adjustedY / this.config.cellSize);

    // Clamp to grid bounds
    const clampedCol = Math.max(0, Math.min(cols - 1, col));
    const clampedRow = Math.max(0, Math.min(rows - 1, row));

    const snappedX =
      this.config.padding + offsetX + clampedCol * this.config.cellSize;
    const snappedY =
      this.config.padding + offsetY + clampedRow * this.config.cellSize;

    return { x: snappedX, y: snappedY };
  }

  public canPlaceWidget(
    x: number,
    y: number,
    width: number,
    height: number,
    excludeWidgetId?: string
  ): boolean {
    // Calculate available space and offsets
    const availableWidth = this.config.width - this.config.padding * 2;
    const availableHeight = this.config.height - this.config.padding * 2;
    const cols = Math.floor(availableWidth / this.config.cellSize);
    const rows = Math.floor(availableHeight / this.config.cellSize);
    const totalGridWidth = cols * this.config.cellSize;
    const totalGridHeight = rows * this.config.cellSize;
    const offsetX = (availableWidth - totalGridWidth) / 2;
    const offsetY = (availableHeight - totalGridHeight) / 2;

    const startCol = Math.floor(
      (x - this.config.padding - offsetX) / this.config.cellSize
    );
    const startRow = Math.floor(
      (y - this.config.padding - offsetY) / this.config.cellSize
    );
    const endCol = Math.ceil(
      (x + width - this.config.padding - offsetX) / this.config.cellSize
    );
    const endRow = Math.ceil(
      (y + height - this.config.padding - offsetY) / this.config.cellSize
    );

    // Check bounds
    if (startCol < 0 || startRow < 0 || endCol > cols || endRow > rows) {
      return false;
    }

    // Check if cells are occupied by other widgets
    for (let row = startRow; row < endRow; row++) {
      for (let col = startCol; col < endCol; col++) {
        if (
          this.grid[row]?.[col]?.occupied &&
          this.grid[row][col].widgetId !== excludeWidgetId
        ) {
          return false;
        }
      }
    }

    return true;
  }

  public reserveGridSpace(
    x: number,
    y: number,
    width: number,
    height: number,
    widgetId: string
  ): void {
    // Calculate available space and offsets
    const availableWidth = this.config.width - this.config.padding * 2;
    const availableHeight = this.config.height - this.config.padding * 2;
    const cols = Math.floor(availableWidth / this.config.cellSize);
    const rows = Math.floor(availableHeight / this.config.cellSize);
    const totalGridWidth = cols * this.config.cellSize;
    const totalGridHeight = rows * this.config.cellSize;
    const offsetX = (availableWidth - totalGridWidth) / 2;
    const offsetY = (availableHeight - totalGridHeight) / 2;

    const startCol = Math.floor(
      (x - this.config.padding - offsetX) / this.config.cellSize
    );
    const startRow = Math.floor(
      (y - this.config.padding - offsetY) / this.config.cellSize
    );
    const endCol = Math.ceil(
      (x + width - this.config.padding - offsetX) / this.config.cellSize
    );
    const endRow = Math.ceil(
      (y + height - this.config.padding - offsetY) / this.config.cellSize
    );

    for (let row = startRow; row < endRow; row++) {
      for (let col = startCol; col < endCol; col++) {
        if (this.grid[row]?.[col]) {
          this.grid[row][col].occupied = true;
          this.grid[row][col].widgetId = widgetId;
        }
      }
    }
  }

  public releaseGridSpace(widgetId: string): void {
    for (let row = 0; row < this.grid.length; row++) {
      for (let col = 0; col < this.grid[row].length; col++) {
        if (this.grid[row][col].widgetId === widgetId) {
          this.grid[row][col].occupied = false;
          this.grid[row][col].widgetId = undefined;
        }
      }
    }
  }

  public findNearestFreePosition(
    x: number,
    y: number,
    width: number,
    height: number
  ): { x: number; y: number } {
    const snapped = this.snapToGrid(x, y);

    if (this.canPlaceWidget(snapped.x, snapped.y, width, height)) {
      return snapped;
    }

    // Search in expanding circles for the nearest free position
    const maxRadius =
      Math.max(
        Math.ceil(width / this.config.cellSize),
        Math.ceil(height / this.config.cellSize)
      ) * 2;

    for (let radius = 1; radius <= maxRadius; radius++) {
      for (let dx = -radius; dx <= radius; dx++) {
        for (let dy = -radius; dy <= radius; dy++) {
          if (Math.abs(dx) === radius || Math.abs(dy) === radius) {
            const testX = snapped.x + dx * this.config.cellSize;
            const testY = snapped.y + dy * this.config.cellSize;

            if (this.canPlaceWidget(testX, testY, width, height)) {
              return { x: testX, y: testY };
            }
          }
        }
      }
    }

    // If no free position found, return original snapped position
    return snapped;
  }

  public getGridVisualization(): {
    x: number;
    y: number;
    width: number;
    height: number;
  }[] {
    const cells: { x: number; y: number; width: number; height: number }[] = [];

    for (let row = 0; row < this.grid.length; row++) {
      for (let col = 0; col < this.grid[row].length; col++) {
        const cell = this.grid[row][col];
        cells.push({
          x: cell.x,
          y: cell.y,
          width: this.config.cellSize,
          height: this.config.cellSize,
        });
      }
    }

    return cells;
  }

  public getGridPoints(): { x: number; y: number }[] {
    const points: { x: number; y: number }[] = [];

    // Calculate available space and offsets
    const availableWidth = this.config.width - this.config.padding * 2;
    const availableHeight = this.config.height - this.config.padding * 2;
    const cols = Math.floor(availableWidth / this.config.cellSize);
    const rows = Math.floor(availableHeight / this.config.cellSize);
    const totalGridWidth = cols * this.config.cellSize;
    const totalGridHeight = rows * this.config.cellSize;
    const offsetX = (availableWidth - totalGridWidth) / 2;
    const offsetY = (availableHeight - totalGridHeight) / 2;

    // Add points at grid intersections
    for (let row = 0; row <= rows; row++) {
      for (let col = 0; col <= cols; col++) {
        const x = this.config.padding + offsetX + col * this.config.cellSize;
        const y = this.config.padding + offsetY + row * this.config.cellSize;
        points.push({ x, y });
      }
    }

    return points;
  }

  public getConfig(): GridConfig {
    return this.config;
  }
}
