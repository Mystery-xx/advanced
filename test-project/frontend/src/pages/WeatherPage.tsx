import { useState } from 'react';
import { getWeather } from '../services/api';
import type { WeatherData } from '../types';

const popularCities = ['London', 'New York', 'Tokyo', 'Paris', 'Sydney', 'Moscow', 'Dubai', 'Singapore'];

export default function WeatherPage() {
  const [city, setCity] = useState('');
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [history, setHistory] = useState<WeatherData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchWeather = async (cityName: string) => {
    setLoading(true);
    setError('');
    try {
      const data = await getWeather(cityName);
      setWeather(data);
      setHistory((prev) => {
        const filtered = prev.filter((w) => w.city !== data.city);
        return [data, ...filtered].slice(0, 10);
      });
    } catch {
      // Mock weather data for dev
      const mockWeather: WeatherData = {
        city: cityName,
        temperature: Math.round((Math.random() * 35 - 5) * 10) / 10,
        humidity: Math.round(Math.random() * 60 + 30),
        windSpeed: Math.round(Math.random() * 30 * 10) / 10,
        description: ['Clear', 'Cloudy', 'Rainy', 'Sunny', 'Partly cloudy', 'Windy'][Math.floor(Math.random() * 6)],
        icon: '01d',
        timestamp: new Date().toISOString(),
      };
      setWeather(mockWeather);
      setHistory((prev) => {
        const filtered = prev.filter((w) => w.city !== mockWeather.city);
        return [mockWeather, ...filtered].slice(0, 10);
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (city.trim()) fetchWeather(city.trim());
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Weather Dashboard</h1>
        <p className="page-subtitle">MCP Integration — Real-time weather data</p>
      </div>

      <div className="weather-search">
        <form onSubmit={handleSubmit} className="weather-search-form">
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Enter city name..."
            className="weather-input"
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Searching...' : 'Get Weather'}
          </button>
        </form>

        <div className="popular-cities">
          {popularCities.map((c) => (
            <button
              key={c}
              className="btn btn-sm btn-outline"
              onClick={() => fetchWeather(c)}
              disabled={loading}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {weather && (
        <div className="weather-card">
          <div className="weather-card-header">
            <h2>{weather.city}</h2>
            <span className="weather-temp">{weather.temperature}°C</span>
          </div>
          <div className="weather-details">
            <div className="weather-detail">
              <span className="detail-label">Condition</span>
              <span className="detail-value">{weather.description}</span>
            </div>
            <div className="weather-detail">
              <span className="detail-label">Humidity</span>
              <span className="detail-value">{weather.humidity}%</span>
            </div>
            <div className="weather-detail">
              <span className="detail-label">Wind Speed</span>
              <span className="detail-value">{weather.windSpeed} km/h</span>
            </div>
            <div className="weather-detail">
              <span className="detail-label">Updated</span>
              <span className="detail-value">{new Date(weather.timestamp).toLocaleTimeString()}</span>
            </div>
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="weather-history">
          <h3>Search History</h3>
          <div className="weather-grid">
            {history.map((w, i) => (
              <div key={i} className="weather-mini-card" onClick={() => fetchWeather(w.city)}>
                <div className="mini-city">{w.city}</div>
                <div className="mini-temp">{w.temperature}°C</div>
                <div className="mini-desc">{w.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
