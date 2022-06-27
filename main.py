from twilio.rest import Client
from flask import Flask, request, render_template
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import requests
import time
import os
import copy

# Load credentials from APIs securely
load_dotenv()
darksky_api = os.getenv("DARKSKY_API")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER")

# Create global variables
global players, frisbee_time, accepted_players
accepted_players = set()
unknown_players = set()
frisbee_time = 1581102000

# Initialize flask app
app = Flask(__name__)


# Twilio will only POST requests to the flask server but redundancy is good.
@app.route('/sms', methods=['GET', 'POST'])
def sms_response():
    # Get global variables
    global players, frisbee_time, accepted_players
    players = get_player_dictionary()

    # Set date in string format
    date = time.strftime("%a, %b %d @ %I:%M%p", time.localtime(frisbee_time))

    # Get body of text message
    body = str(request.values.get('Body', None))
    upper_body = copy.deepcopy(body)

    # Get the number who sent the response
    who_dis = str(request.values.get('From', None))

    # Get legible name
    try:
        who_sent = players[who_dis]
    except KeyError:
        who_sent = 'New Person'

    # Print message to console
    print(f'{time.time()} - {who_dis} - {who_sent} - {body}\n')

    # Log response
    with open(str(frisbee_time) + '.txt', 'a+') as fp:
        fp.write(f'{time.time()} - {who_dis} - {who_sent} - {body}\n')

    # Create a response instance
    response = MessagingResponse()

    # Check if number is NOT in the directory
    if who_dis not in players.keys():

        # If person is not in the unknown_players list, this is the first time they have sent a message
        if who_dis not in unknown_players:

            # Send response requesting name information from frisbee system
            response.message('Hi! The automated frisbee system doesn\'t have your information yet.'
                             ' Please respond with your first and last name to register.')

            # Add player to list of potential candidates
            unknown_players.add(who_dis)

            # Return string of response
            return str(response)

        else:

            # If they are in the unknown_players list, they have already received the initial message.
            print(f'Adding {who_dis} to the frisbee list with name: {body}')

            # Remove them from list of unknown players
            unknown_players.remove(who_dis)

            # Send text message of registration confirmation
            response.message(f'Thanks for registering with the automatic frisbee messaging system. '
                             f'You\'ve registered as: {body}\n'
                             f'Next frisbee is scheduled for {date}.\n'
                             f'Reply "Y" to confirm attendance, "STATUS" for confirmed players, or '
                             f'"WEATHER" for the current forecast.')

            # Open the distribution list and append the number and body to the file
            with open('twilio.txt', 'a') as fp:
                fp.write(f'{who_dis}:{body}\n')
                print(f'Added {body} to the distribution list.')

            # Reload player dictionary with new entry
            players = get_player_dictionary()

            # Return string of response
            return str(response)

    # Strip any spaces from the request (thanks Derrick)
    body = body.strip().lower()

    # Check for yes, no, status, or stop
    if body == 'y' or body == 'yes':

        # Send response
        response.message('You\'re in! See you at frisbee.\n'
                         'Reply "STATUS" to see confirmed players.\n'
                         'Reply "WEATHER" to recieve the current forecast.\n'
                         'Reply "N" to change your mind.')

        # Add number to set
        accepted_players.add(who_dis)

    # Check for negative attendance
    elif body == 'n' or body == 'no':
        # Send response
        response.message('No problem! Thanks for responding.\n'
                         'If you change your mind, reply "Y" to accept.')

        # Check if player in confirmed set; remove them if so
        if who_dis in accepted_players:
            accepted_players.remove(who_dis)

    elif body == 'status':
        # Get people attending
        attendees = create_message_of_attendees()

        # Send list
        response.message(attendees)

    elif body == 'stop':
        # Reply
        response.message('Understood. Removing you from distribution list.')

        # Remove from list
        remove_person(who_dis)

    elif body == 'weather':

        # Get current forecast
        forecast = get_weather()
        response.message(forecast)

    elif 'rename' in body:
        # Get requested name
        new_name = upper_body[body.find(':') + 1:]

        # Change name in player dictionary
        change_name(who_dis, new_name)

        # Send response
        response.message(f'Changing your new name to: {new_name}')

    elif ':(' in body:
        response.message('It\'s okay. I\'m sad too, and I\'m a python script.')

    # Admin controls
    elif who_dis == '+17347163221':

        if 'reload' in body:
            # Function in case program crashes. It will parse log messages and reconstruct accepted players set
            past_players = parse_log()
            for player in past_players:
                accepted_players.add(player)

            # Send message with new list of players
            response.message(
                f'ADMIN: Confirmation repopulated with {len(past_players)} previously confirmed player(s).')

        # Change frisbee time remotely
        elif 'next' in body:
            # Update frisbee time
            frisbee_time += (24 * 7 * 3600)
            date = time.strftime("%a, %b %d @ %I:%M%p", time.localtime(frisbee_time))

            # Clear accepted players
            accepted_players = set()

            # Send confirmation
            response.message(f'ADMIN: Changed next frisbee time to {date}.')

            # Trigger frisbee system
        elif 'send' in body:
            # Get forecast data and format text message
            weather = get_weather()

            # Send text messages to everyone on distribution list
            send_text(weather, forreal=True)

            # Send confirmation
            response.message(f'ADMIN: You sent frisbee notice for {date} to {len(players)} people.')

        elif 'cancel:weather' in body:
            # Create twilio client
            client = Client(twilio_sid, twilio_token)

            # Create cancellation message
            cancellation = 'Unfortunately, due to weather conditions, frisbee has been cancelled for today :('

            # Send cancellations to each person in the accepted list
            for person in accepted_players:
                message = client.messages.create(
                    body=cancellation,
                    from_=twilio_number,
                    to=person)
                print(f'Sent cancellation notice to: {person}')

            # Send confirmation
            response.message(f'Sent cancellation to {len(accepted_players)} confirmed players.')

        else:
            response.message(f'ADMIN: Unrecognized command: {body}')
    elif 'rip' in body:
        response.message('in peace.')
    else:
        # Catch exceptions
        response.message(f'Response of "{body}" not recognized. Concerned about phishing? '
                         f'Check the source code on Gitlab: https://gitlab.com/snippets/1923217. '
                         f'Something go wrong? Contact Kyle.')
        if who_dis == '+12145434718':
            response.message('PS: Stop trying to stress test my code, Ryan.')

    # Return string of response for Flask server
    return str(response)


def change_name(number, new_name):
    # Remove number from address list
    remove_person(number)

    # Add number with new name to list
    with open('twilio.txt', 'a') as fp:
        fp.write(f'{number}:{new_name}\n')


def parse_log():
    # Parses log from current frisbee time for confirmations and returns them as a list

    # Create return list for players
    past = []

    # Open log from the past
    with open(f'{frisbee_time}.txt', 'r') as log_file:

        # Iterate thru lines
        for line in log_file.readlines():

            # Check if confirmation
            if '- y' in line.lower() and 'New' not in line:
                # Grab index of start of phone number
                n = line.find('+')

                # Extract phone number
                who = line[n:n + 12]

                # Append to return lists
                past.append(who)
    return past


def create_message_of_attendees():
    global players, accepted_players
    # Create blank message
    attendees = ''

    # Parses set of confirmed attendees and builds a text message of people
    for number in accepted_players:
        # Match person with accepted players
        name = players[number]

        # Add to message
        attendees += (' - ' + name + '\n')

    # Check if there is anyone
    if len(attendees) == 0:
        return 'There are no confirmed players yet. You could be the first!'
    else:
        attendees = 'Confirmed attendees:\n' + attendees
        return attendees


def remove_person(number):
    # Remove a phone number from the distribution list

    # Get global player list
    global players

    # Open the old list and read all the lines
    with open('twilio.txt', 'r') as old_file:
        lines = old_file.readlines()

    # Reopen the same file while overwriting
    with open('twilio.txt', 'w') as new_file:
        for line in lines:
            # Check if number is in the line; if not, write it back to distribution list
            if number not in line:
                new_file.write(line)

    # Reload player dictionary
    players = get_player_dictionary()

@app.route("/", methods=["GET"])
def landing():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_player():
    player_name = request.form.get("name")
    player_number = request.form.get("number")
    print(f'Received info: {player_name}//{player_number}')


def get_player_dictionary():
    # Function to read contact list and reload players into memory

    # Create return player dictionary
    players_dict = dict()

    # Read in numbers from text file
    with open('twilio.txt') as fp:
        # Iterate thru lines
        for line in fp.readlines():

            # Skip empty lines
            if len(line) < 9:
                continue

            # Split on spaces
            splits = line.split(':')
            number = splits[0]
            person = splits[1].strip()

            # Add to player dictionary
            players_dict[number] = person

    # Return dictionary
    return players_dict


def send_text(weather, forreal=False):
    # Define global variables
    global players

    # Combine intro with weather text
    intro = '🤾🥏❓\n'
    outro = f'Reply "Y" to accept.\n' \
            f'Reply "N" to decline.\n' \
            f'Reply "STATUS" to see confirmed players.\n' \
            f'Reply "WEATHER" to see current weather forecast.\n' \
            f'Reply "STOP" to opt-out.'
    message_text = intro + weather + outro
    print(message_text)

    # Create twilio client
    client = Client(twilio_sid, twilio_token)

    # Load player dictionary
    players = get_player_dictionary()

    # Iterate thru dictionary
    for number in players.keys():

        # Send text message
        if forreal is True:
            pass
            # message = client.messages.create(
            #     body=message_text,
            #     from_=twilio_number,
            #     to=number)

        # Print success message
        print(f'Sent text message to {number} - {players[number]}')


def get_weather():
    # Get global variable
    global frisbee_time

    # Function to get the weather forecast for the day.
    date = time.strftime("%a, %b %d @ %I:%M%p", time.localtime(frisbee_time))
    day_text = time.strftime("%a, %b %d", time.localtime(frisbee_time))

    # Define latitude and longitude of request
    latitude = 33.0742
    longitude = -96.8398

    # Assemble URL for GET request
    url = f'https://api.darksky.net/forecast/{darksky_api}/{latitude},{longitude}'

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
            daily = dictionary['daily']

            # Get daily summary
            for day in daily['data']:
                # Get epoch time of day
                day_start = int(day['time'])

                # Check if this is the right day for frisbee
                if day_start < frisbee_time < day_start + (24 * 3600):
                    # Extract data
                    summary = day['summary']
                    rain = float(day['precipProbability']) * 100
                    hi_temp = day['temperatureHigh']
                    lo_temp = day['temperatureLow']

                    # Form message
                    text_message = f'The daily forecast for {day_text}:\n' \
                                   f'{summary}\n' \
                                   f'{rain} % chance for rain.\n' \
                                   f'{hi_temp} deg F (high).\n' \
                                   f'{lo_temp} deg F (low).\n' \
                                   f'Try again later for hourly data.'

                    # Return text message
                    return text_message
        elif t_difference > 0:

            # Extract hourly data
            hourly = dictionary['hourly']

            # Iterate thru the hours (48 hours total from time of request)
            for hour in hourly['data']:

                # Extract the epoch time
                epoch_time = int(hour['time'])

                # Check if epoch time is within start time of frisbee
                if frisbee_time - 1800 < epoch_time < frisbee_time + 1800:
                    # Extract rain chance
                    rain_chance = float(hour['precipProbability']) * 100

                    # Extract temperature
                    temp = hour['temperature']

                    # Extract apparent temperature
                    feels_like = hour['apparentTemperature']

                    # Extract humidity
                    humidity = float(hour['humidity']) * 100

                    # Extract wind
                    wind_speed = hour['windSpeed']

                    # Extract UV index
                    uv = hour['uvIndex']

                    # Format text message
                    text_message = f'Forecast for {date}:\n' \
                                   f'- {temp} deg F.\n' \
                                   f'- {rain_chance}% chance of rain.\n' \
                                   f'- {humidity}% humidity.\n' \
                                   f'- {wind_speed} mph wind.\n' \
                                   f'- {uv} UV index.\n'

                    return text_message
        else:
            text_messsage = f'Unable to retrieve forecast for {date} since it was in the past.'
            return text_messsage


if __name__ == '__main__':
    # Run flask server for response
    app.run()
