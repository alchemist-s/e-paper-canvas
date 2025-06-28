import { Container, Text, Graphics } from "pixi.js";
import type { Widget, WidgetRegion } from "../types/widget";
import { transportService } from "../services/transportService";
import { displayService } from "../services/displayService";

export class TransportWidget implements Widget {
  public id: string;
  public container: Container;
  public type: "transport" = "transport";
  public x: number;
  public y: number;
  public width: number = 300;
  public height: number = 100;
  public regions: WidgetRegion[] = [];

  private unsubscribe: (() => void) | null = null;
  private nextTrainText!: Text;
  private followingTrainText!: Text;

  constructor(x: number, y: number) {
    this.id = `transport-${Date.now()}-${Math.random()}`;
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
      text: "RHODES TO CENTRAL",
      style: {
        fill: "#333333",
        fontSize: 12,
        fontWeight: "bold",
      },
      x: 15,
      y: 10,
    });
    this.container.addChild(title);

    // Next train section (left side)
    const nextLabel = new Text({
      text: "NEXT",
      style: {
        fill: "#666666",
        fontSize: 10,
        fontWeight: "bold",
      },
      x: 15,
      y: 30,
    });
    this.container.addChild(nextLabel);

    // Next train minutes (large and prominent)
    this.nextTrainText = new Text({
      text: "3 min",
      style: {
        fill: "#000000",
        fontSize: 36,
        fontWeight: "bold",
      },
      x: 15,
      y: 45,
    });
    this.container.addChild(this.nextTrainText);

    // Following train section (right side)
    const followingLabel = new Text({
      text: "THEN",
      style: {
        fill: "#666666",
        fontSize: 10,
        fontWeight: "bold",
      },
      x: 160,
      y: 30,
    });
    this.container.addChild(followingLabel);

    // Following train minutes
    this.followingTrainText = new Text({
      text: "18 min",
      style: {
        fill: "#333333",
        fontSize: 24,
        fontWeight: "bold",
      },
      x: 160,
      y: 45,
    });
    this.container.addChild(this.followingTrainText);

    // Define regions for live updates
    this.regions = [
      {
        id: "next-train",
        x: 15,
        y: 45,
        width: 60,
        height: 36,
        element: this.nextTrainText,
        updateFunction: () => {
          const data = transportService.getData();
          const nextText =
            data.minutesUntilArrival === 0
              ? "NOW"
              : `${data.minutesUntilArrival} min`;
          this.nextTrainText.text = nextText;
        },
      },
      {
        id: "following-train",
        x: 160,
        y: 45,
        width: 50,
        height: 24,
        element: this.followingTrainText,
        updateFunction: () => {
          const data = transportService.getData();
          // Calculate following train time (next train + 15 minutes)
          const followingMinutes = data.minutesUntilArrival + 15;
          const followingText =
            followingMinutes === 0 ? "NOW" : `${followingMinutes} min`;
          this.followingTrainText.text = followingText;
        },
      },
    ];
  }

  private subscribeToData(): void {
    this.unsubscribe = transportService.subscribe((data) => {
      this.updateDisplay(data);
      // Update regions after display update
      this.regions.forEach((region) => {
        displayService.sendRegionUpdate(region, this);
      });
    });
  }

  private updateDisplay(data: any): void {
    const nextText =
      data.minutesUntilArrival === 0
        ? "NOW"
        : `${data.minutesUntilArrival} min`;
    this.nextTrainText.text = nextText;

    // Calculate following train time (next train + 15 minutes)
    const followingMinutes = data.minutesUntilArrival + 15;
    const followingText =
      followingMinutes === 0 ? "NOW" : `${followingMinutes} min`;
    this.followingTrainText.text = followingText;
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
