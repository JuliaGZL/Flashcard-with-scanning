# Import SQLite3 to build database
import sqlite3
# Import Card and CardSet for performing functions on and with them
from cards import Card, CardSet
# Import typing to indicate return types
from typing import List

from datetime import date, timedelta

SCHEDULE = [1, 2, 4, 7, 15, 30, 90, 180]
today = date.today()


class Database():
    # Initialize database
    def __init__(self):
        # Establish connection
        self.db = sqlite3.connect("flashcard.db")
        # Initialize cursor of connection
        self.cursor = self.db.cursor()
        # Creates the tables if the tables do not exist
        self.initialize_db()

    # Initialize when there is no database
    def initialize_db(self) -> None:
        # Check if tables exists in the user's file (basically, initializing for first time usage)
        self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='cardsets'")
        results = self.cursor.fetchall()
        if not (len(results) == 1 and results[0][0] == 'cardsets'):
            print("Cardsets do not exist")
            # Create cardsets table if table does not exist
            self.cursor.execute('''CREATE TABLE cardsets
                                (id INTEGER PRIMARY KEY,
                                title TEXT,
                                last_date TEXT,
                                await_date TEXT,
                                create_date TEXT)''')
        self.cursor.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='cards'")
        results = self.cursor.fetchall()
        if not (len(results) == 1 and results[0][0] == 'cards'):
            print("Cards do not exist")
            # Creates cards table if table does not exist
            self.cursor.execute('''CREATE TABLE cards
                                (id INTEGER PRIMARY KEY,
                                term TEXT,
                                def TEXT,
                                memor_date TEXT,
                                box INTEGER,
                                finished_memor BOOLEAN,
                                cardset_id INTEGER,
                                FOREIGN KEY (cardset_id) REFERENCES cardsets(id))''')

    # Add a card into cards table
    def add_card(self, card: Card, foreign_key: int) -> None:
        self.cursor.execute('''INSERT INTO cards (term, def, memor_date, box, finished_memor, cardset_id)
                                VALUES (?, ?, ?, ?, ?, ?)''',
                            (card.term, card.definition, card.memor_date, card.box, card.finished_memor, foreign_key))
        self.db.commit()

    # Add a card set into cardsets table, and add its cards into cards table
    def add_cardset(self, cardset: CardSet) -> None:
        self.cursor.execute('''INSERT INTO cardsets (title, last_date, await_date, create_date)
                            VALUES (?, ?, ?, ?)''',
                            (cardset.title, cardset.last_date, cardset.await_date, cardset.CREATE_DATE))
        self.db.commit()
        # Get the primary key value of the last inserted row
        cardset_id = self.cursor.lastrowid
        # Add all cards of cardset
        current = cardset.head
        while current.next != None:
            self.add_card(current, cardset_id)
            current = current.next
        self.add_card(current, cardset_id)

    # Get all card sets (their cards)
    def get_all_cardsets(self) -> List[CardSet]:
        self.cursor.execute("SELECT * FROM cardsets")
        temp_sets = self.cursor.fetchall()
        sets = []
        for temp_set in temp_sets:
            cardset = CardSet(id=temp_set[0], title=temp_set[1], last_date=temp_set[2],
                              await_date=temp_set[3], create_date=temp_set[4])
            sets.append(cardset)
        return sets

    # Inputs empty card set, card set id and sort mode, returns the linked list with its cards
    def get_set_cards(self, cardset: CardSet, foreign_key: int, mode="beginning") -> CardSet:
        self.cursor.execute(
            f"SELECT * FROM cards WHERE cardset_id = '{foreign_key}'")
        # Get all cards with the card set id foreign_key
        temp_cards = self.cursor.fetchall()
        for i, card in enumerate(temp_cards):
            c = Card(id=card[0], term=card[1], definition=card[2],
                     memor_date=card[3], box=card[4], finished_memor=card[5])
            cardset.insert(c, mode)
        return cardset

    # Get a single card set without its cards
    def get_cardset(self, cardset_id) -> CardSet:
        self.cursor.execute(f"SELECT * FROM cardsets WHERE id={cardset_id}")
        temp_set = self.cursor.fetchall()[0]
        cardset = CardSet(
            id=temp_set[0], title=temp_set[1], last_date=temp_set[2], await_date=temp_set[3], create_date=temp_set[4])
        return cardset

    # Delete a card set in "cardsets" table by its id
    def delete_cardset(self, id) -> None:
        self.delete_cards(id)
        self.cursor.execute(f"DELETE FROM cardsets WHERE id = {id}")
        self.db.commit()

    # Delete all cards in "cards" table of a card set by the cardset id
    def delete_cards(self, cardset_id) -> None:
        self.cursor.execute(
            f"DELETE FROM cards WHERE cardset_id = {cardset_id}")
        self.db.commit()

    # Delete all cards by their id
    def delete_cards_id(self, ids: List[int]) -> None:
        for id in ids:
            self.cursor.execute(f"DELETE FROM cards WHERE id= {id}")
        self.db.commit()

    # Delete a card in "cards" table by its id
    def delete_card(self, card_id) -> None:
        self.cursor.execute(f"DELETE FROM cards WHERE id = {card_id}")
        self.db.commit()

    # Update the data of a card set and its cards in "cardsets" and "cards" table
    def set_cardset(self, cardset_id: int, cardset: CardSet) -> None:
        self.cursor.execute(f"UPDATE cardsets SET title='{cardset.title}', last_date = '{cardset.last_date}', \
                            await_date='{cardset.await_date}' WHERE id={cardset_id}")
        # Updates all cards inside card set
        self.set_cardset_cards(cardset_id, cardset)

    # Update the data of a card set's cards in "cards" table
    def set_cardset_cards(self, cardset_id: int, cardset: CardSet) -> None:
        self.cursor.execute(
            f"SELECT id FROM cards WHERE cardset_id={cardset_id}")
        ids = self.cursor.fetchall()
        i = 0
        current = cardset.head
        while current.next != None and i < len(ids):
            self.set_card(card_id=ids[i][0], card=current)
            i += 1
            current = current.next
        # The user cannot delete cards in this process, so the two only cases are
        # 1) Length of new = Length of old, should update the last current
        # 2) Length of new > length of old, the last current is already updated
        if current.next == None:
            self.set_card(ids[-1][0], current)
        # If the user added more cards
        while current.next != None:
            current = current.next
            self.add_card(current, cardset_id)

    # Update a card in "cards" table
    def set_card(self, card_id, card: Card) -> None:
        self.cursor.execute(
            f"UPDATE cards SET term='{card.term}', def='{card.definition}', memor_date='{card.memor_date}', \
                 box='{card.box}', finished_memor={card.finished_memor} WHERE id={card_id}")
        self.db.commit()

    # Update memor_date of card
    def set_card_memor(self, card_id: int, memor_date: str) -> None:
        self.cursor.execute(
            f"UPDATE cards SET memor_date='{memor_date}' WHERE id={card_id}")
        self.db.commit()

    # Set the last_date of card set
    def set_last_date(self, cardset_id: int, last_date: str) -> None:
        self.cursor.execute(
            f"UPDATE cardsets SET last_date='{last_date}' WHERE id={cardset_id}")
        self.db.commit()

    # Set the await_date of card set
    def set_await_date(self, cardset_id: int, await_date: str) -> None:
        self.cursor.execute(
            f"UPDATE cardsets SET await_date='{await_date}' WHERE id={cardset_id}")
        self.db.commit()

    def set_box(self, card_id: int, box_num: int, cardset: CardSet) -> None:
        interval = SCHEDULE[box_num]
        memor_date = (today + timedelta(interval)).isoformat()
        # Update the single card's box and memor_date
        self.cursor.execute(
            f"UPDATE cards SET box={box_num}, memor_date='{memor_date}' WHERE id={card_id}")
        if memor_date > cardset.await_date:
            # Updates cardset if necessary
            self.cursor.execute(
                f"UPDATE cardsets SET await_date='{memor_date}' WHERE id={cardset.id}")

    # Print all rows of "cardsets" table

    def print_cardsets(self) -> None:
        self.cursor.execute("SELECT * FROM cardsets")
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)

    # Print all rows of "cards" table, given row number, and print all cards if cardset_id = -1
    def print_cards(self, cardset_id=-1) -> None:
        if cardset_id == -1:
            self.cursor.execute("SELECT * FROM cards")
        else:
            self.cursor.execute(
                f"SELECT * FROM cards WHERE cardset_id={cardset_id}")
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)

    # Ends connection with database
    def end_connection(self) -> None:
        # Saves all updates
        self.db.commit()
        # Close connection with database flashcard.db
        self.db.close()

    def re_allocate_idxs(self) -> None:
        self.db.execute("VACUUM")
        self.db.commit()

if __name__ == "__main__":
    db = Database()
    db.re_allocate_idxs()
    db.print_cards()
    # db.set_await_date(1, "2023-03-18")
    # cardsets = db.get_all_cardsets()
    # cardset = cardsets[0]
    # cardset = db.get_set_cards(cardset, cardset.id)
    # current = cardset.head
    # while current != None:
    #     self.cardset.insert(current, mode="priority")

    # cardset2 = CardSet(
    #     cardset.id, cardset.title, cardset.last_date, cardset.await_date, cardset.CREATE_DATE)
