import time
import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# Load API keys
load_dotenv()
darksky_api = os.getenv("DARKSKY_API")
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER")


def admin_control(requesting_number):

    who_dis == "+17347163221"

    if "reload" in body:
        # Function in case program crashes. It will parse log messages and reconstruct accepted players set
        past_players = parse_log()
        for player in past_players:
            accepted_players.add(player)

        # Send message with new list of players
        response.message(
            f"ADMIN: Confirmation repopulated with {len(past_players)} previously confirmed player(s)."
        )

    # Change frisbee time remotely
    elif "next" in body:
        # Update frisbee time
        frisbee_time += 24 * 7 * 3600
        date = time.strftime("%a, %b %d @ %I:%M%p", time.localtime(frisbee_time))

        # Clear accepted players
        accepted_players = set()

        # Send confirmation
        response.message(f"ADMIN: Changed next frisbee time to {date}.")

        # Trigger frisbee system
    elif "send" in body:
        # Get forecast data and format text message
        weather = get_weather()

        # Send text messages to everyone on distribution list
        send_text(weather, forreal=True)

        # Send confirmation
        response.message(
            f"ADMIN: You sent frisbee notice for {date} to {len(players)} people."
        )

    elif "cancel:weather" in body:
        # Create twilio client
        client = Client(twilio_sid, twilio_token)

        # Create cancellation message
        cancellation = "Unfortunately, due to weather conditions, frisbee has been cancelled for today :("

        # Send cancellations to each person in the accepted list
        for person in accepted_players:
            message = client.messages.create(
                body=cancellation, from_=twilio_number, to=person
            )
            print(f"Sent cancellation notice to: {person}")

        # Send confirmation
        response.message(
            f"Sent cancellation to {len(accepted_players)} confirmed players."
        )

    else:
        response.message(f"ADMIN: Unrecognized command: {body}")

    # @app.route("/", methods=["GET"])

    # Twilio will only POST requests to the flask server but redundancy is good.
    @app.route("/sms", methods=["GET", "POST"])
    def change_name(number, new_name):
        # Remove number from address list
        remove_person(number)

        # Add number with new name to list
        with open("twilio.txt", "a") as fp:
            fp.write(f"{number}:{new_name}\n")

    def parse_log():
        # Parses log from current frisbee time for confirmations and returns them as a list

        # Create return list for players
        past = []

        # Open log from the past
        with open(f"{frisbee_time}.txt", "r") as log_file:

            # Iterate thru lines
            for line in log_file.readlines():

                # Check if confirmation
                if "- y" in line.lower() and "New" not in line:
                    # Grab index of start of phone number
                    n = line.find("+")

                    # Extract phone number
                    who = line[n : n + 12]

                    # Append to return lists
                    past.append(who)
        return past

    def create_message_of_attendees():
        # Create blank message
        attendees = ""

        # Parses set of confirmed attendees and builds a text message of people
        for number in accepted_players:
            # Match person with accepted players
            name = players[number]

            # Add to message
            attendees += " - " + name + "\n"

        # Check if there is anyone
        if len(attendees) == 0:
            return "There are no confirmed players yet. You could be the first!"
        else:
            attendees = "Confirmed attendees:\n" + attendees
            return attendees

    def remove_person(number):
        # Remove a phone number from the distribution list

        # Get global player list
        global players

        # Open the old list and read all the lines
        with open("twilio.txt", "r") as old_file:
            lines = old_file.readlines()

        # Reopen the same file while overwriting
        with open("twilio.txt", "w") as new_file:
            for line in lines:
                # Check if number is in the line; if not, write it back to distribution list
                if number not in line:
                    new_file.write(line)

        # Reload player dictionary
        players = get_player_dictionary()

    def get_player_dictionary():
        # Function to read contact list and reload players into memory

        # Create return player dictionary
        players_dict = dict()

        # Read in numbers from text file
        with open("twilio.txt") as fp:
            # Iterate thru lines
            for line in fp.readlines():

                # Skip empty lines
                if len(line) < 9:
                    continue

                # Split on spaces
                splits = line.split(":")
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
        intro = "🤾🥏❓\n"
        outro = (
            f'Reply "Y" to accept.\n'
            f'Reply "N" to decline.\n'
            f'Reply "STATUS" to see confirmed players.\n'
            f'Reply "WEATHER" to see current weather forecast.\n'
            f'Reply "STOP" to opt-out.'
        )
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
                message = client.messages.create(
                    body=message_text, from_=twilio_number, to=number
                )

            # Print success message
            print(f"Sent text message to {number} - {players[number]}")
