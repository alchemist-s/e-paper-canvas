import { ref } from "vue";
import type { WeatherData, HourlyForecast } from "../types/widget";

class WeatherService {
  private data = ref<WeatherData>({
    current: {
      temperature: "22°C",
      condition: "Sunny",
      humidity: "65%",
      wind: "15 km/h",
    },
    hourly: [],
  });

  private updateInterval: number | null = null;
  private subscribers: ((data: WeatherData) => void)[] = [];

  constructor() {
    this.startUpdates();
  }

  public subscribe(callback: (data: WeatherData) => void): () => void {
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

  public getData(): WeatherData {
    return this.data.value;
  }

  private generateHourlyForecast(): HourlyForecast[] {
    const conditions = [
      "Sunny",
      "Cloudy",
      "Rainy",
      "Partly Cloudy",
      "Overcast",
      "Light Rain",
    ];
    const temperatures = Array.from({ length: 15 }, (_, i) => i + 10); // 10-25°C

    const hourly: HourlyForecast[] = [];
    const now = new Date();

    for (let i = 1; i <= 6; i++) {
      const forecastTime = new Date(now.getTime() + i * 60 * 60 * 1000);
      const hour = forecastTime.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });

      hourly.push({
        hour,
        temperature: `${
          temperatures[Math.floor(Math.random() * temperatures.length)]
        }°C`,
        condition: conditions[Math.floor(Math.random() * conditions.length)],
      });
    }

    return hourly;
  }

  private async fetchWeatherData(): Promise<WeatherData> {
    // In a real app, this would fetch from a weather API
    // For now, we'll simulate with random data
    const conditions = [
      "Sunny",
      "Cloudy",
      "Rainy",
      "Partly Cloudy",
      "Overcast",
    ];
    const temperatures = Array.from({ length: 20 }, (_, i) => i + 10); // 10-30°C

    return {
      current: {
        temperature: `${
          temperatures[Math.floor(Math.random() * temperatures.length)]
        }°C`,
        condition: conditions[Math.floor(Math.random() * conditions.length)],
        humidity: `${Math.floor(Math.random() * 40) + 40}%`,
        wind: `${Math.floor(Math.random() * 25) + 5} km/h`,
      },
      hourly: this.generateHourlyForecast(),
    };
  }

  private async updateData(): Promise<void> {
    try {
      const newData = await this.fetchWeatherData();
      this.data.value = newData;

      // Notify all subscribers
      this.subscribers.forEach((callback) => callback(newData));
    } catch (error) {
      console.error("Failed to update weather data:", error);
    }
  }

  private startUpdates(): void {
    // Update every 5 minutes
    this.updateInterval = setInterval(() => {
      this.updateData();
    }, 5 * 60 * 1000);
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
export const weatherService = new WeatherService();
