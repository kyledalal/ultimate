from twilio.rest import Client
from flask import Flask, redirect, render_template, request, url_for
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import threading
import time
import os
import copy
import re
from database.database_handler import DataBaser
from weather import get_weather

# Load credentials from APIs securely
load_dotenv()
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER")


class EventManager:
    def __init__(self, port=7111):

        # Create database object
        self.databasedgod = DataBaser()

        # Create flask app + run it
        self.app = Flask(__name__)
        self.port = port
        self.thread = threading.Thread(
            target=self.start,
            args=[],
        )
        self.thread.start()

        # Add routes
        self.app.add_url_rule(
            rule="/",
            endpoint="index",
            view_func=self.index,
            methods=["GET"],
        )
        self.app.add_url_rule(
            rule="/register",
            endpoint="register",
            view_func=self.register,
            methods=["POST"],
        )
        self.app.add_url_rule(
            rule="/error",
            endpoint="error",
            view_func=self.error,
            methods=["GET"],
        )
        self.app.add_url_rule(
            rule="/sms",
            endpoint="sms",
            view_func=self.sms,
            methods=["POST"],
        )

        # Twilio client
        self.client = Client(twilio_sid, twilio_token)

    def start(self):
        self.app.run(
            host="0.0.0.0",
            port=self.port,
            debug=True,
            threaded=True,
            use_reloader=False,
        )

    @staticmethod
    def index():
        return render_template("index.html")

    @staticmethod
    def error():
        return render_template("error.html")

    def register(self):
        # Parse reponse from form
        player_name = request.form.get("name")
        player_number = request.form.get("number")
        # Shameless copying of digit-only string parsing (https://stackoverflow.com/a/1249424/11155402)
        player_number = re.sub(r"\D", "", player_number)

        # Check to ensure phone number is valid -> assumes 10-digit phone number
        if len(player_number) != 10:
            print(f"Bad phone number! Length: {len(player_number)}")
            return redirect(url_for("error"))

        else:
            # Add country code for phone number
            player_number = "+1" + player_number
        print(f"Received info: {player_name}: {player_number}")

        # Add the player to the database
        response = self.databasedgod.add_player(
            player_name=player_name,
            player_phone=player_number,
        )

        if response == DataBaser.SUCCESS:
            self.send_welcome_text(player_name, player_number)
            return "Success!"

    def send_text(self, message_text, destination):
        message = self.client.messages.create(
            body=message_text, from_=twilio_number, to=destination
        )
        print(
            f"Send message to {destination} with data: {message_text}\n"
            f"Message status: {message.status}"
        )

    def send_welcome_text(self, player_name, player_number):
        print(f"Welcome {player_name} @ {player_number}")
        frisbee_time = self.databasedgod.get_next_event()
        date = time.strftime("%a, %b %d @ %I:%M%p", time.localtime(frisbee_time))
        message = (
            f"Thanks for registering with the automatic frisbee messaging system. \n"
            f"You've registered as: {player_name}\n"
            f"Next frisbee is scheduled for {date}.\n"
            f"Reply 'Y' to confirm attendance, 'STATUS' for confirmed players, 'WEATHER' for the forecast."
        )
        self.send_text(
            message_text=message,
            destination=player_number,
        )

    def send_registration_text(self, player_number):
        # TODO: This flow
        message = (
            "Uh oh! I don't have your information yet. Please respond with your name."
        )
        self.send_text(message, player_number)

    def sms(self):
        # Set date in string format
        frisbee_time = self.databasedgod.get_next_event()
        date = time.strftime("%a, %b %d @ %I:%M%p", time.localtime(frisbee_time))

        # Get body and sender from incoming text message
        body = str(request.values.get("Body", None))
        sender_number = str(request.values.get("From", None))

        # Identify player
        address_book = self.databasedgod.get_address_book()

        # Send registration text if not in system
        if sender_number not in address_book:
            self.send_registration_text(sender_number)
            self.databasedgod.add_player("UNKNOWN", sender_number)
            return

        sender = address_book[sender_number]

        # Check if response was received from this person before or not
        respondants = self.databasedgod.get_respondants(frisbee_time)
        if sender_number in respondants:
            first_response = False
        else:
            first_response = True
        print(f"{time.time()} - {sender} - {sender_number} - {body}\n")

        # Create a response instance
        response = MessagingResponse()

        # Strip any spaces from the request (thanks Derrick)
        body = body.strip().lower()

        # Check for yes, no, status, or stop
        if body == "y" or body == "yes":

            # Send response
            response.message(
                "You're in! See you at frisbee.\n"
                'Reply "STATUS" to see confirmed players.\n'
                'Reply "WEATHER" to recieve the current forecast.\n'
                'Reply "N" to change your mind.'
            )

            # Add number to set
            if first_response:
                self.databasedgod.add_response(sender_number, frisbee_time, 1)
            else:
                self.databasedgod.update_response(sender_number, frisbee_time, 1)

        # Check for negative attendance
        elif body == "n" or body == "no":
            # Send response
            response.message(
                "No problem! Thanks for responding.\n"
                'If you change your mind, just reply "Y" to accept.'
            )
            # Add number to set
            if first_response:
                self.databasedgod.add_response(sender_number, frisbee_time, 0)
            else:
                self.databasedgod.update_response(sender_number, frisbee_time, 0)

        elif body == "status":
            # Get people attending
            message = self.create_attendee_list()
            response.message(message)

        elif body == "stop":
            # Remove from address book
            response.message("Understood. Removing you from distribution list.")
            self.databasedgod.remove_player(sender_number)

        elif body == "weather":
            # Get current forecast
            forecast = get_weather(frisbee_time)
            response.message(forecast)

        else:
            response_dict = {
                ":(": "It's okay. I'm sad too, and I'm a python script.",
                "rip": "in peace",
            }
            for key in response_dict:
                if key in body:
                    response.message(response_dict[key])
                    return str(response)

            # Catch exceptions
            response.message(
                f'Response of "{body}" not recognized. Concerned about phishing? \n'
                f"Check the source code at https://github.com/kyledalal/ultimate \n"
                f"Something go wrong? Contact Kyle."
            )

        # Return string of response for Flask server
        return str(response)

    def create_attendee_list(self):
        address_book = self.databasedgod.get_address_book()
        frisbee_time = self.databasedgod.get_next_event()
        attendees = self.databasedgod.get_attendees(frisbee_time)

        print(
            f"Address Book: {address_book}\n"
            f"Frisbee time: {frisbee_time}\n"
            f"Attendees: {attendees}"
        )

        # Check if there is anyone
        if len(attendees) == 0:
            return "There are no confirmed players yet. You could be the first!"
        else:
            message = ""
            for attendee in attendees:
                message += " - " + address_book[attendee] + "\n"
            return "Confirmed attendees: \n" + message


if __name__ == "__main__":

    # Create database object
    events = EventManager()
