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
  private nextTrainNumber!: Text;
  private nextTrainUnit!: Text;
  private followingTrainNumber!: Text;
  private followingTrainUnit!: Text;
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
    this.nextTrainNumber = new Text({
      text: "3",
      style: {
        fill: "#000000",
        fontSize: 120,
        fontWeight: "bold",
      },
      x: 35,
      y: 110,
    });
    this.nextTrainUnit = new Text({
      text: "min",
      style: {
        fill: "#000000",
        fontSize: 36,
        fontWeight: "bold",
      },
      x: 180,
      y: 170,
    });
    this.container.addChild(this.nextTrainNumber);
    this.container.addChild(this.nextTrainUnit);

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
    this.followingTrainNumber = new Text({
      text: "18",
      style: {
        fill: "#333333",
        fontSize: 48,
        fontWeight: "bold",
      },
      x: 450,
      y: 110,
    });
    this.followingTrainUnit = new Text({
      text: "min",
      style: {
        fill: "#333333",
        fontSize: 18,
        fontWeight: "bold",
      },
      x: 520,
      y: 150,
    });
    this.container.addChild(this.followingTrainNumber);
    this.container.addChild(this.followingTrainUnit);

    // Define regions for live updates
    this.regions = [
      {
        id: "next-train",
        x: this.nextTrainNumber.x,
        y: this.nextTrainNumber.y,
        width: this.nextTrainNumber.getBounds().width,
        height: this.nextTrainNumber.getBounds().height,
        element: this.nextTrainNumber,
        updateFunction: () => {
          // Updates handled in subscribe callback
        },
      },
      {
        id: "next-train-unit",
        x: this.nextTrainUnit.x,
        y: this.nextTrainUnit.y,
        width: this.nextTrainUnit.getBounds().width,
        height: this.nextTrainUnit.getBounds().height,
        element: this.nextTrainUnit,
        updateFunction: () => {
          // Updates handled in subscribe callback
        },
      },
      {
        id: "following-train",
        x: this.followingTrainNumber.x,
        y: this.followingTrainNumber.y,
        width: this.followingTrainNumber.getBounds().width,
        height: this.followingTrainNumber.getBounds().height,
        element: this.followingTrainNumber,
        updateFunction: () => {
          // Updates handled in subscribe callback
        },
      },
      {
        id: "following-train-unit",
        x: this.followingTrainUnit.x,
        y: this.followingTrainUnit.y,
        width: this.followingTrainUnit.getBounds().width,
        height: this.followingTrainUnit.getBounds().height,
        element: this.followingTrainUnit,
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
        const nextParts = nextText.split(" ");
        this.nextTrainNumber.text = nextParts[0];
        this.nextTrainUnit.text = nextParts.length > 1 ? nextParts[1] : "";

        const followingText =
          data.followingMinutesUntilArrival === 0
            ? "NOW"
            : `${data.followingMinutesUntilArrival} min`;
        const followingParts = followingText.split(" ");
        this.followingTrainNumber.text = followingParts[0];
        this.followingTrainUnit.text =
          followingParts.length > 1 ? followingParts[1] : "";

        // Send all regions sequentially
        for (const region of this.regions) {
          // Update region dimensions to current element bounds
          region.width = region.element.getBounds().width;
          region.height = region.element.getBounds().height;

          await displayService.sendRegionUpdate(region, this);
        }
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
    const nextParts = nextText.split(" ");
    this.nextTrainNumber.text = nextParts[0];
    this.nextTrainUnit.text = nextParts.length > 1 ? nextParts[1] : "";

    const followingText =
      data.followingMinutesUntilArrival === 0
        ? "NOW"
        : `${data.followingMinutesUntilArrival} min`;
    const followingParts = followingText.split(" ");
    this.followingTrainNumber.text = followingParts[0];
    this.followingTrainUnit.text =
      followingParts.length > 1 ? followingParts[1] : "";
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
