import sqlite3
import atexit
import shortuuid


class DataBaser:
    def __init__(self):
        # Create connection to database
        self.connection = sqlite3.connect("frisbee.db")
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
    ) -> str:
        # Create UID for player and insert into DB
        uid = shortuuid.uuid(name=player_phone)
        _, numbers, _ = self.get_all_players()
        if player_phone in numbers:
            print(f"Player already in database...")
            return ""

        print(f"Inserting player {player_name} ({player_phone}) into DB; UUID: {uid}")
        self.cursor.execute(
            "INSERT INTO players VALUES (?, ?, ?)",
            (
                uid,
                player_name,
                player_phone,
            ),
        )
        self.connection.commit()
        print(f"Success!")
        return uid

    def get_all_players(self) -> [list, list, list]:
        # Gets the players name, phone number, and uid
        names, numbers, uids = list(), list(), list()
        players = self.cursor.execute("SELECT * FROM players").fetchall()
        for player in players:
            uids.append(player[0])
            names.append(player[1])
            numbers.append(player[2])
        return names, numbers, uids

    def create_event(self):
        """
        Creates an entry in the "events" table that represents an instance of frisbee
        """

        pass


if __name__ == "__main__":
    db = DataBaser()
    db.add_player("Kyle Dalal", "+17347163221")
    db.add_player("Drew DeCagna 🧢", "+19705411007")
    db.add_player("JohnKett.pdf 📄🔒", "+12149842729")
    print(db.get_all_players())
