import { ref } from "vue";
import type { TransportData } from "../types/widget";

class TransportService {
  private data = ref<TransportData>({
    nextTrain: "Loading...",
    destination: "Loading...",
    platform: "Loading...",
    status: "Loading...",
    minutesUntilArrival: 0,
  });

  private updateInterval: number | null = null;
  private subscribers: ((data: TransportData) => void)[] = [];
  private apiBaseUrl = "http://localhost:8000"; // FastAPI server URL

  constructor() {
    this.startUpdates();
  }

  public subscribe(callback: (data: TransportData) => void): () => void {
    this.subscribers.push(callback);
    // Immediately call with current data
    callback(this.data.value);

    // Return unsubscribe function
    return () => {
      const index = this.subscribers.indexOf(callback);
      if (index > -1) {
        this.subscribers.splice(index, 1);
      }
    };
  }

  public getData(): TransportData {
    return this.data.value;
  }

  private async fetchTransportData(): Promise<TransportData> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/transport/summary`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      return {
        nextTrain: data.nextTrain || "No trains",
        destination: data.destination || "N/A",
        platform: data.platform || "N/A",
        status: data.status || "No service",
        minutesUntilArrival: data.minutesUntilArrival || 0,
      };
    } catch (error) {
      console.error("Failed to fetch transport data:", error);
      // Return fallback data on error
      return {
        nextTrain: "Error",
        destination: "N/A",
        platform: "N/A",
        status: "API Error",
        minutesUntilArrival: 0,
      };
    }
  }

  private async updateData(): Promise<void> {
    try {
      const newData = await this.fetchTransportData();
      this.data.value = newData;

      // Notify all subscribers
      this.subscribers.forEach((callback) => callback(newData));
    } catch (error) {
      console.error("Failed to update transport data:", error);
    }
  }

  private startUpdates(): void {
    // Update every 30 seconds for transport data
    this.updateInterval = setInterval(() => {
      this.updateData();
    }, 30 * 1000);

    // Initial update
    this.updateData();
  }

  public destroy(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
    this.subscribers = [];
  }
}

// Export singleton instance
export const transportService = new TransportService();
