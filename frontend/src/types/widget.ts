import { Container, Text, Graphics } from "pixi.js";

export interface WidgetRegion {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  element: Text | Graphics | Container;
  updateFunction: () => void;
}

export interface Widget {
  id: string;
  container: Container;
  type: "weather" | "transport" | "time";
  x: number;
  y: number;
  width: number;
  height: number;
  regions: WidgetRegion[];
  updateData: () => Promise<void>;
  destroy: () => void;
}

export interface HourlyForecast {
  hour: string;
  temperature: string;
  condition: string;
  icon?: string;
}

export interface WeatherData {
  current: {
    temperature: string;
    condition: string;
    humidity: string;
    wind: string;
  };
  hourly: HourlyForecast[];
}

export interface TransportData {
  nextTrain: string;
  destination: string;
  platform: string;
  status: string;
  minutesUntilArrival: number;
}

export interface TimeData {
  time: string;
  date: string;
  weekday: string;
  month: string;
  year: string;
}

export interface GridPoint {
  x: number;
  y: number;
  occupied: boolean;
  widgetId?: string;
}

export interface GridConfig {
  cellSize: number;
  padding: number;
  width: number;
  height: number;
}
