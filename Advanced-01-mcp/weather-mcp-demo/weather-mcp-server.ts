#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";

// 날씨 데이터 타입 정의
interface WeatherData {
  location: string;
  temperature: number;
  condition: string;
  humidity: number;
  windSpeed: number;
}

// 간단한 시뮬레이션 날씨 데이터 (실제 API 대신)
// 실제 환경에서는 OpenWeatherMap API 같은 걸 사용하면 됩니다
function getWeatherData(location: string, units: string = "metric"): WeatherData {
  // 시뮬레이션 데이터 생성
  const cities: Record<string, WeatherData> = {
    "seoul": {
      location: "Seoul, KR",
      temperature: units === "metric" ? 15 : 59,
      condition: "Clear sky",
      humidity: 65,
      windSpeed: units === "metric" ? 3.5 : 7.8
    },
    "tokyo": {
      location: "Tokyo, JP",
      temperature: units === "metric" ? 18 : 64,
      condition: "Partly cloudy",
      humidity: 70,
      windSpeed: units === "metric" ? 4.2 : 9.4
    },
    "new york": {
      location: "New York, US",
      temperature: units === "metric" ? 12 : 54,
      condition: "Light rain",
      humidity: 80,
      windSpeed: units === "metric" ? 5.5 : 12.3
    },
    "london": {
      location: "London, UK",
      temperature: units === "metric" ? 10 : 50,
      condition: "Foggy",
      humidity: 85,
      windSpeed: units === "metric" ? 3.0 : 6.7
    },
    "paris": {
      location: "Paris, FR",
      temperature: units === "metric" ? 14 : 57,
      condition: "Overcast",
      humidity: 72,
      windSpeed: units === "metric" ? 4.0 : 8.9
    }
  };

  const cityKey = location.toLowerCase();
  const weather = cities[cityKey] || {
    location: location,
    temperature: units === "metric" ? 20 : 68,
    condition: "Unknown",
    humidity: 60,
    windSpeed: units === "metric" ? 3.0 : 6.7
  };

  return weather;
}

// MCP 서버 생성
const server = new Server(
  {
    name: "weather-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tools 목록 정의 (Function Calling의 JSON Schema!)
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "get_current_weather",
        description: "Get the current weather for a specified location. Supports major cities worldwide.",
        inputSchema: {
          type: "object",
          properties: {
            location: {
              type: "string",
              description: "The city name (e.g., 'Seoul', 'Tokyo', 'New York')",
            },
            units: {
              type: "string",
              enum: ["metric", "imperial"],
              description: "Temperature units: 'metric' for Celsius, 'imperial' for Fahrenheit",
              default: "metric",
            },
          },
          required: ["location"],
        },
      } as Tool,
      {
        name: "get_forecast",
        description: "Get a 3-day weather forecast for a specified location",
        inputSchema: {
          type: "object",
          properties: {
            location: {
              type: "string",
              description: "The city name",
            },
            units: {
              type: "string",
              enum: ["metric", "imperial"],
              default: "metric",
            },
          },
          required: ["location"],
        },
      } as Tool,
    ],
  };
});

// Tool 실행 핸들러 (실제 Function Calling!)
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "get_current_weather") {
    const location = String(args?.location || "Seoul");
    const units = String(args?.units || "metric");

    const weather = getWeatherData(location, units);
    const tempUnit = units === "metric" ? "°C" : "°F";
    const speedUnit = units === "metric" ? "m/s" : "mph";

    return {
      content: [
        {
          type: "text",
          text: `Current weather in ${weather.location}:
🌡️  Temperature: ${weather.temperature}${tempUnit}
☁️  Condition: ${weather.condition}
💧 Humidity: ${weather.humidity}%
💨 Wind Speed: ${weather.windSpeed} ${speedUnit}`,
        },
      ],
    };
  }

  if (name === "get_forecast") {
    const location = String(args?.location || "Seoul");
    const units = String(args?.units || "metric");
    const tempUnit = units === "metric" ? "°C" : "°F";

    // 간단한 3일 예보 시뮬레이션
    const baseWeather = getWeatherData(location, units);
    
    return {
      content: [
        {
          type: "text",
          text: `3-Day Forecast for ${baseWeather.location}:

📅 Today: ${baseWeather.temperature}${tempUnit}, ${baseWeather.condition}
📅 Tomorrow: ${baseWeather.temperature + 2}${tempUnit}, Partly cloudy
📅 Day 3: ${baseWeather.temperature - 1}${tempUnit}, Light rain`,
        },
      ],
    };
  }

  throw new Error(`Unknown tool: ${name}`);
});

// 서버 실행
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Weather MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
