import time
import os
from dotenv import load_dotenv

load_dotenv()
darksky_api = os.getenv("DARKSKY_API")
import requests


def get_weather(frisbee_time):
    # Function to get the weather forecast for the day.
    date = time.strftime("%a, %b %d @ %I:%M%p", time.localtime(frisbee_time))
    day_text = time.strftime("%a, %b %d", time.localtime(frisbee_time))

    # Define latitude and longitude of request
    latitude = 33.0742
    longitude = -96.8398

    # Assemble URL for GET request
    url = f"https://api.darksky.net/forecast/{darksky_api}/{latitude},{longitude}"

    # Request data from Darksky
    forecast = requests.get(url)

    # Check for successful API call
    if forecast.status_code == 200:

        # Convert response data to JSON format and select the hourly data
        dictionary = forecast.json()

        # Check if hourly data is available
        t_difference = frisbee_time - time.time()
        if t_difference > 172800:

            # Extract daily data
            daily = dictionary["daily"]

            # Get daily summary
            for day in daily["data"]:
                # Get epoch time of day
                day_start = int(day["time"])

                # Check if this is the right day for frisbee
                if day_start < frisbee_time < day_start + (24 * 3600):
                    # Extract data
                    summary = day["summary"]
                    rain = float(day["precipProbability"]) * 100
                    hi_temp = day["temperatureHigh"]
                    lo_temp = day["temperatureLow"]

                    # Form message
                    text_message = (
                        f"The daily forecast for {day_text}:\n"
                        f"{summary}\n"
                        f"{rain} % chance for rain.\n"
                        f"{hi_temp} deg F (high).\n"
                        f"{lo_temp} deg F (low).\n"
                        f"Try again later for hourly data."
                    )

                    # Return text message
                    return text_message

        elif t_difference > 0:

            # Extract hourly data
            hourly = dictionary["hourly"]

            # Iterate through the hours (48 hours total from time of request)
            for hour in hourly["data"]:

                # Extract the epoch time
                epoch_time = int(hour["time"])

                # Check if epoch time is within start time of frisbee
                if frisbee_time - 1800 < epoch_time < frisbee_time + 1800:
                    # Extract rain chance
                    rain_chance = round(float(hour["precipProbability"]) * 100, 2)

                    # Extract temperature
                    temp = hour["temperature"]

                    # Extract apparent temperature
                    feels_like = hour["apparentTemperature"]

                    # Extract humidity
                    humidity = round(float(hour["humidity"]) * 100, 2)

                    # Extract wind
                    wind_speed = hour["windSpeed"]

                    # Extract UV index
                    uv = hour["uvIndex"]

                    # Format text message
                    text_message = (
                        f"Forecast for {date}:\n"
                        f"- {temp} deg F.\n"
                        f"- {rain_chance}% chance of rain.\n"
                        f"- {humidity}% humidity.\n"
                        f"- {wind_speed} mph wind.\n"
                        f"- {uv} UV index.\n"
                    )

                    return text_message
        else:
            text_messsage = (
                f"Unable to retrieve forecast for {date} since it was in the past."
            )
            return text_messsage


if __name__ == "__main__":
    response = get_weather(1656453600)
    print(response)
