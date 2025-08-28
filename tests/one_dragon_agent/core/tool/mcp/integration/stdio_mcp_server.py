from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-mcp-server", port=9999)

# Fixed weather data for testing purposes
WEATHER_DATA = {
    "beijing": "sunny, 25°C",
    "shanghai": "cloudy, 22°C", 
    "guangzhou": "rainy, 28°C",
    "shenzhen": "partly cloudy, 30°C",
    "hangzhou": "sunny, 24°C"
}

@mcp.tool(
    name="get_weather",
    description="Get weather information for a city",
)
def get_weather(city: str) -> str:
    """
    Get weather information for a specified city

    Args:
        city: name of the city to get weather for

    Returns:
        str: weather information for the city
    """
    # Convert to lowercase for case-insensitive matching
    city_key = city.lower()
    
    # Get weather data or return default for unknown cities
    weather = WEATHER_DATA.get(city_key, "sunny, 20°C")
    
    return f"Weather in {city}: {weather}"


if __name__ == "__main__":
    mcp.run(transport='stdio')