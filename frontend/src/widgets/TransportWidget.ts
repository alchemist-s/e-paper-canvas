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
  public width: number = 600;
  public height: number = 200;
  public regions: WidgetRegion[] = [];

  private unsubscribe: (() => void) | null = null;
  private nextTrainText!: Text;
  private followingTrainText!: Text;
  private previousData: any = null;
  private isInitialized: boolean = false;

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
      .roundRect(0, 0, this.width, this.height, 16)
      .fill();

    this.container.addChild(background);

    // Title
    const title = new Text({
      text: "RHODES TO CENTRAL",
      style: {
        fill: "#333333",
        fontSize: 28,
        fontWeight: "bold",
      },
      x: 35,
      y: 30,
    });
    this.container.addChild(title);

    // Next train section (left side)
    const nextLabel = new Text({
      text: "NEXT",
      style: {
        fill: "#666666",
        fontSize: 24,
        fontWeight: "bold",
      },
      x: 35,
      y: 80,
    });
    this.container.addChild(nextLabel);

    // Next train minutes (very large and prominent)
    this.nextTrainText = new Text({
      text: "3 min",
      style: {
        fill: "#000000",
        fontSize: 120,
        fontWeight: "bold",
      },
      x: 35,
      y: 110,
    });
    this.container.addChild(this.nextTrainText);

    // Following train section (right side)
    const followingLabel = new Text({
      text: "THEN",
      style: {
        fill: "#666666",
        fontSize: 20,
        fontWeight: "bold",
      },
      x: 450,
      y: 80,
    });
    this.container.addChild(followingLabel);

    // Following train minutes (smaller than NEXT)
    this.followingTrainText = new Text({
      text: "18 min",
      style: {
        fill: "#333333",
        fontSize: 48,
        fontWeight: "bold",
      },
      x: 450,
      y: 110,
    });
    this.container.addChild(this.followingTrainText);

    // Define regions for live updates
    this.regions = [
      {
        id: "next-train-combined",
        x: this.nextTrainText.x - 20,
        y: this.nextTrainText.y,
        width: this.nextTrainText.getBounds().width + 40,
        height: this.nextTrainText.getBounds().height,
        element: this.nextTrainText, // Use text element as reference
        updateFunction: () => {
          // Updates handled in subscribe callback
        },
      },
      {
        id: "following-train-combined",
        x: this.followingTrainText.x - 20,
        y: this.followingTrainText.y,
        width: this.followingTrainText.getBounds().width + 40,
        height: this.followingTrainText.getBounds().height,
        element: this.followingTrainText, // Use text element as reference
        updateFunction: () => {
          // Updates handled in subscribe callback
        },
      },
    ];
  }

  private subscribeToData(): void {
    this.unsubscribe = transportService.subscribe(async (data) => {
      // Check if data has changed
      const hasChanged =
        this.previousData === null ||
        this.previousData.minutesUntilArrival !== data.minutesUntilArrival;

      this.updateDisplay(data);

      // Only update regions if data has changed AND widget is initialized
      if (hasChanged && this.isInitialized) {
        console.log("Sending region updates for transport widget");

        // Update all text elements first
        const nextText =
          data.minutesUntilArrival === 0
            ? "NOW"
            : `${data.minutesUntilArrival} min`;
        this.nextTrainText.text = nextText;

        const followingText =
          data.followingMinutesUntilArrival === 0
            ? "NOW"
            : `${data.followingMinutesUntilArrival} min`;
        this.followingTrainText.text = followingText;

        // Force a small delay to ensure text changes are applied
        await new Promise((resolve) => setTimeout(resolve, 5));

        // Update region dimensions to current element bounds
        for (const region of this.regions) {
          if (region.id === "next-train-combined") {
            // Combined region for next train (text) with horizontal padding
            region.x = this.nextTrainText.x - 20;
            region.y = this.nextTrainText.y;
            region.width = this.nextTrainText.getBounds().width + 40;
            region.height = this.nextTrainText.getBounds().height;
            console.log(
              `Updated next-train-combined region: ${region.width}x${region.height} for text "${this.nextTrainText.text}"`
            );
          } else if (region.id === "following-train-combined") {
            // Combined region for following train (text) with horizontal padding
            region.x = this.followingTrainText.x - 20;
            region.y = this.followingTrainText.y;
            region.width = this.followingTrainText.getBounds().width + 40;
            region.height = this.followingTrainText.getBounds().height;
            console.log(
              `Updated following-train-combined region: ${region.width}x${region.height} for text "${this.followingTrainText.text}"`
            );
          }
        }

        // Send all regions in a single batch update
        await displayService.sendMultipleRegionUpdates(this.regions, this);
      }

      // Store current data for next comparison
      this.previousData = { ...data };
    });

    // Mark widget as initialized after a delay to allow full image update to complete
    setTimeout(() => {
      this.isInitialized = true;
      console.log("Transport widget initialized");
    }, 200);
  }

  private updateDisplay(data: any): void {
    const nextText =
      data.minutesUntilArrival === 0
        ? "NOW"
        : `${data.minutesUntilArrival} min`;
    this.nextTrainText.text = nextText;

    const followingText =
      data.followingMinutesUntilArrival === 0
        ? "NOW"
        : `${data.followingMinutesUntilArrival} min`;
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
