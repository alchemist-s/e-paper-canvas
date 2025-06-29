import { Container, Text, Graphics } from "pixi.js";
import type { Widget, WidgetRegion } from "../types/widget";
import { weatherService } from "../services/weatherService";
import { displayService } from "../services/displayService";

export class WeatherWidget implements Widget {
  public id: string;
  public container: Container;
  public type: "weather" = "weather";
  public x: number;
  public y: number;
  public width: number = 150;
  public height: number = 110;
  public regions: WidgetRegion[] = [];

  private unsubscribe: (() => void) | null = null;
  private currentTempText!: Text;
  private currentConditionText!: Text;

  constructor(x: number, y: number) {
    this.id = `weather-${Date.now()}-${Math.random()}`;
    this.x = x;
    this.y = y;

    this.container = new Container();
    this.container.x = x;
    this.container.y = y;
    this.container.eventMode = "static";
    this.container.cursor = "pointer";

    this.createWidget();
    this.subscribeToData();
  }

  private createWidget(): void {
    // Background
    const background = new Graphics()
      .fill(0xffffff)
      .roundRect(0, 0, this.width, this.height, 8)
      .fill();

    this.container.addChild(background);

    // Title
    const title = new Text({
      text: "Weather",
      style: {
        fill: "#000000",
        fontSize: 16,
        fontWeight: "bold",
      },
      x: 10,
      y: 10,
    });
    this.container.addChild(title);

    // Current weather section (left side)
    const currentLabel = new Text({
      text: "Current:",
      style: {
        fill: "#000000",
        fontSize: 14,
        fontWeight: "bold",
      },
      x: 10,
      y: 35,
    });
    this.container.addChild(currentLabel);

    // Current temperature
    this.currentTempText = new Text({
      text: "22°C",
      style: {
        fill: "#000000",
        fontSize: 24,
        fontWeight: "bold",
      },
      x: 10,
      y: 55,
    });
    this.container.addChild(this.currentTempText);

    // Current condition
    this.currentConditionText = new Text({
      text: "Sunny",
      style: {
        fill: "#333333",
        fontSize: 14,
      },
      x: 10,
      y: 85,
    });
    this.container.addChild(this.currentConditionText);

    // Define regions for live updates
    this.regions = [
      {
        id: "current-temp",
        x: 10,
        y: 55,
        width: 80,
        height: 30,
        element: this.currentTempText,
        updateFunction: () => {
          this.currentTempText.text =
            weatherService.getData().current.temperature;
        },
      },
      {
        id: "current-condition",
        x: 10,
        y: 85,
        width: 100,
        height: 20,
        element: this.currentConditionText,
        updateFunction: () => {
          this.currentConditionText.text =
            weatherService.getData().current.condition;
        },
      },
    ];
  }

  private subscribeToData(): void {
    this.unsubscribe = weatherService.subscribe((data) => {
      this.updateDisplay(data);
      // Update all regions in a single batch
      displayService.sendMultipleRegionUpdates(this.regions, this);
    });
  }

  private updateDisplay(data: any): void {
    // Update current weather
    this.currentTempText.text = data.current.temperature;
    this.currentConditionText.text = data.current.condition;
  }

  public async updateData(): Promise<void> {
    // This could trigger a manual refresh if needed
    // For now, the service handles automatic updates
  }

  public destroy(): void {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }

    if (this.container.parent) {
      this.container.parent.removeChild(this.container);
    }

    this.container.destroy({ children: true });
  }
}
