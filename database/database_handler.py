import sqlite3
import atexit
import shortuuid
import os


class DataBaser:
    EXISTING_PLAYER = 0
    SUCCESS = 1
    ERROR = 2

    def __init__(self):
        # Create connection to database
        self.working_dir = os.path.abspath(os.path.dirname(__file__))
        self.database_path = os.path.join(self.working_dir, "frisbee.db")
        self.connection = sqlite3.connect(os.path.join(self.working_dir, "frisbee.db"))
        self.cursor = self.connection.cursor()

        # Ensure the connection is closed when program is terminated
        atexit.register(self.close_connection)

    def close_connection(self):
        print(f"Closing db connection...")
        self.connection.commit()
        self.cursor.close()
        self.connection.close()
        print(f"Closed db connection.")

    def add_player(
        self,
        player_name: str,
        player_phone: str,
    ) -> int:

        # Insert player into database
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()

            # Create UID for player and insert into DB
            uid = shortuuid.uuid(name=player_phone)
            address_book = self.get_address_book()
            if player_phone in address_book:
                print(f"Player already in database...")
                if player_name != address_book[player_phone]:
                    print(
                        f"Player exists with different name, {address_book[player_phone]}. Updating to {player_name}"
                    )
                    self.update_player_name(player_name, player_phone)
                return DataBaser.SUCCESS

            print(
                f"Inserting player {player_name} ({player_phone}) into DB; UUID: {uid}"
            )
            cursor.execute(
                "INSERT INTO players VALUES (?, ?, ?)", (uid, player_name, player_phone)
            )
            connection.commit()
        return DataBaser.SUCCESS

    def update_player_name(self, player_name: str, player_phone: str) -> int:
        # Insert player into database
        print(f"Updating player {player_name} ({player_phone}) in DB")
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE players SET name = ? WHERE number = ?",
                (player_name, player_phone),
            )
            connection.commit()
        return DataBaser.SUCCESS

    def remove_player(self, player_phone: str) -> int:
        # Delete player from database
        print(f"Deleting {player_phone} from address book")
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM players WHERE number = ?", player_phone)
            connection.commit()
        return DataBaser.SUCCESS

    def get_all_players(self) -> [list, list, list]:
        # Gets the players name, phone number, and uid
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            names, numbers, uids = list(), list(), list()
            players = cursor.execute("SELECT * FROM players").fetchall()
            for player in players:
                uids.append(player[0])
                names.append(player[1])
                numbers.append(player[2])
            return names, numbers, uids

    def get_address_book(self) -> dict:
        # Gets the players name by phone number key
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            names, numbers, uids = list(), list(), list()
            players = cursor.execute("SELECT * FROM players").fetchall()
            for player in players:
                names.append(player[1])
                numbers.append(player[2])
            return {i: j for i, j in zip(numbers, names)}

    def get_unknown_numbers(self) -> list:
        # Gets the numbers of the unknown players
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            names, numbers, uids = list(), list(), list()
            players = cursor.execute(
                "SELECT * FROM players WHERE name = 'UNKNOWN'"
            ).fetchall()
            for player in players:
                uids.append(player[0])
                names.append(player[1])
                numbers.append(player[2])
            return numbers

    def create_event(self, epoch_time):
        """
        TODO: Creates an entry in the "games" table that represents an instance of frisbee
        """
        pass

    def get_next_event(self) -> int:
        # Returns the epoch time of the next frisbee event
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            time = cursor.execute(
                "SELECT timestamp FROM games ORDER BY timestamp DESC"
            ).fetchone()
            return time[0]

    def add_response(self, number, frisbee_time, attendance):
        # Add response to responses table
        print(f"Adding response of {attendance} from {number} to records.")
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO responses VALUES (?, ?, ?)",
                (number, frisbee_time, attendance),
            )
            connection.commit()
            return

    def update_response(self, number, frisbee_time, attendance):
        # Add response to responses table
        print(f"Updating response of {attendance} from {number} to records.")
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE responses SET attendance = ? WHERE player_number = ? AND game_id = ?",
                (
                    attendance,
                    number,
                    frisbee_time,
                ),
            )
            connection.commit()
            return

    def get_attendees(self, epoch_time):
        print(f"Querying for attendees @ {epoch_time}")
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            attendees = cursor.execute(
                "SELECT player_number "
                "FROM responses "
                "WHERE game_id=? AND attendance=1",
                (epoch_time,),
            ).fetchall()
            return [attendee[0] for attendee in attendees]

    def get_respondants(self, epoch_time):
        print(f"Querying for attendees @ {epoch_time}")
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.cursor()
            attendees = cursor.execute(
                "SELECT player_number FROM responses WHERE game_id=?",
                (epoch_time,),
            ).fetchall()
            return [attendee[0] for attendee in attendees]


if __name__ == "__main__":
    db = DataBaser()
    db.add_player("Kyle Dalal", "+17347163221")
    db.add_player("Drew DeCagna 🧢", "+19705411007")
    db.add_player("JohnKett.pdf 📄🔒", "+12149842729")
    print(db.get_all_players())
    print(db.get_next_event())
