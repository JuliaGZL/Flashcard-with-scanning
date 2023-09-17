# Use DateTime to get and compute time
import datetime
from datetime import date, timedelta
# Import typing to indicate return types
from typing import List
# For generating random numbers
import random

today = date.today()
tmr = today + timedelta(1)

SCHEDULE = [1, 2, 4, 7, 15, 30, 90, 180]


class Card():
    def __init__(self, id: int, term: str, definition: str, box=0, state=0, memor_date=today.isoformat(), finished_memor=False, forgot=False) -> None:
        self.id = id
        self.term = term
        self.definition = definition
        self.memor_date = memor_date

        self.box = box
        self.forgot = forgot
        self.state = state
        self.finished_memor = finished_memor
        self.to_memor = self.is_needed()

        # Doubly linked list node data
        self.next = None
        self.prev = None

    # Gets the date for the next memorization
    def get_await_date(self, pattern=SCHEDULE) -> datetime.datetime:
        if not self.finished_memor:
            memor_date = datetime.datetime.strptime(
                self.memor_date, "%Y-%m-%d").date()
            await_date = memor_date + \
                datetime.timedelta(days=pattern[self.box])
            return await_date
        else:
            raise RuntimeError(
                "Card already memorized, shouldn't use function get_await_date")

    # Gets it is ready to memorize
    def is_needed(self, pattern=SCHEDULE) -> bool:
        if self.finished_memor:
            return False
        else:
            if self.box >= 8:
                self.finished_memor = True
                return False
            else:
                await_date = self.get_await_date(pattern)
                today_date = date.today()
                return today_date <= await_date

    # To String function of Card
    def __repr__(self):
        if self == None:
            return "None"
        else:
            printed = f"Term: {self.term}, Definition: {self.definition}, Box: {self.box}, Prev: {self.prev.term if self.prev else None}, Next: {self.next.term if self.next else None}, State: {self.state}"
            return printed


class CardSet():
    def __init__(self, id: int, title: str, last_date=today.isoformat(), await_date=today.isoformat(), create_date=today.isoformat()) -> None:
        # For building the doubly linked list
        self.head = None
        self.tail = None
        self.count = 0

        # For CardSet's own characteristics
        self.title = title
        self.last_date = last_date
        self.await_date = await_date
        self.CREATE_DATE = create_date
        self.id = id
        self.awaiting = self.is_awaiting()

    # To String function of CardSet
    def __repr__(self):
        if self.head == None:
            printed = "----------\n"
            printed = printed + \
                f"Title: {self.title}, Last date: {self.last_date}\n"
            printed = printed + "----------"
        else:
            printed = "----------\n"
            printed = printed + f"Title: {self.title}" + "\n"
            current = self.head
            while current.next != None:
                printed = printed + current.__repr__() + "\n"
                current = current.next
            printed = printed + current.__repr__() + "\n----------"
        return printed

    # Return True if the card set has some card to be memorized
    def is_awaiting(self):
        today = date.today()
        if today.isoformat() >= self.await_date:
            return True
        else:
            return False

    # Insert a card at the beginning of the card set doubly linked list
    def insert(self, card: Card, mode="beginning") -> None:
        if mode == "beginning":
            if self.head == None:
                self.head = card
                self.tail = card
                self.head.prev = None
                self.head.next = None
                self.count += 1
            else:
                self.head.prev = card
                card.next = self.head
                self.head = card
                self.count += 1
        elif mode == "alphabetical":
            if self.head == None:
                self.head = card
                self.tail = card
                self.count += 1
            else:
                current = self.head
                while current.next != None and card.term < current.next.term:
                    current = current.next
                # If the card is appended to the last position
                if card.term > current.term:
                    self.append(card)
                else:
                    if card == self.head:
                        self.insert(card)
                    else:
                        # If current is at the first card that is greater than parameter
                        card.prev = current.prev
                        current.prev.next = card
                        card.next = current
                        current.prev = card
                        self.count += 1
        elif mode == "default":
            if self.head == None:
                self.head = card
                self.tail = card
                self.count += 1
            else:
                current = self.head
                # If blue card
                if card.memor_date <= today.isoformat():
                    while current.next != None and current.next.memor_date <= today.isoformat() and card.term < current.next.term:
                        current = current.next
                    # If last card
                    if current == self.tail:
                        ''' TODO: cannot exclude the situation where current is just previous of self.tail? '''
                        self.append(card)
                    elif current == self.head:
                        self.insert(card)
                    else:
                        card.prev = current.prev
                        current.prev.next = card
                        card.next = current
                        current.prev = card
                        self.count += 1

                # If black card
                else:
                    while current.next != None and current.next.memor_date <= today.isoformat():
                        current = current.next
                    while current.next != None and card.term < current.next.term:
                        current = current.next
                    if card.term > current.term:
                        self.append(card)
                    else:
                        if current == self.head:
                            self.insert(card)
                        else:
                            # If current is at the first card that is greater than parameter
                            card.prev = current.prev
                            current.prev.next = card
                            card.next = current
                            current.prev = card
                            self.count += 1
        else:
            raise ValueError("Invalid mode, please check input parameter.")

    # Randomly inserts a card into self from start_idx (inclusive) to end_idx (exclusive)
    def random_insert(self, card: Card, start_idx: int, end_idx: int) -> None:
        position = random.randint(start_idx, end_idx)
        new_card = Card(card.id, card.term, card.definition, card.box, card.state,
                        card.memor_date, card.finished_memor)
        self.insert_at(new_card, position)

    # Insert a card at indicated index
    def insert_at(self, card: Card, index: int) -> None:
        if index == 0:
            self.insert(card)
        elif index == -1 or index == self.count:
            self.append(card)
        elif index < 0 or index > self.count:
            raise ValueError(
                f"Index out of range: {index}, size: {self.count}")
        else:
            if index < self.count // 2:
                current = self.head
                for _ in range(index):
                    current = current.next
            else:
                current = self.tail
                for _ in range(self.count - index - 1):
                    current = current.prev
            # Insert before this current node
            current.prev.next = card
            card.prev = current.prev
            card.next = current
            current.prev = card
            self.count += 1

    # Append a card at the end of the card set doubly linked list
    def append(self, card: Card) -> None:
        if self.head == None:
            self.head = card
            self.tail = card
            self.head.prev = None
            self.head.next = None
            self.count += 1
        else:
            self.tail.next = card
            self.tail.next.prev = self.tail
            self.tail = self.tail.next
            self.tail.next = None
            self.count += 1

    # Delete card at index of the card set doubly linked list
    def delete_at(self, index: int) -> None:
        if self.count == 1:
            self.head = None
            self.tail = None
            self.count = 0
        else:
            if index < 0 and index != -1 or index >= self.count:
                raise ValueError(
                    f"Index out of range: {index}, size: {self.count}")
            elif index == 0:
                self.head = self.head.next
                self.head.prev = None
                self.count -= 1
            elif index == -1 or index == self.count - 1:
                self.tail = self.tail.prev
                self.tail.next = None
                self.count -= 1
            else:
                if index < self.count // 2:
                    current = self.head
                    for _ in range(index):
                        current = current.next
                else:
                    current = self.tail
                    for _ in range(self.count - index):
                        current = current.prev
                current.prev.next = current.next
                current.next.prev = current.prev
                del current
                self.count -= 1

    # Delete card in card set doubly linked list
    def delete(self, card: Card) -> None:
        if self.count == 1:
            self.head = None
            self.tail = None
            self.count = 0
        else:
            current = self.head
            while current != card and current.next != None:
                current = current.next
            if self.head == card:
                self.head = self.head.next
                self.head.prev = None
                self.count -= 1
            elif current.next == None and current == card:
                self.tail = self.tail.prev
                self.tail.next = None
                self.count -= 1
            elif current.next != None:
                current.prev.next = current.next
                current.next.prev = current.prev
                del current
                self.count -= 1
            else:
                raise ValueError("Card not in linked list!")

    def sort_default(self) -> None:
        # Check if the linked list only has one or no nodes
        if self.head == None or self.head == self.tail:
            return
        else:
            pass    

    @staticmethod
    # Mode is ["alphabetical, chronological"]
    def sort_cardsets(self, cardsets: list, mode="chronological") -> list:
        if mode == "chronological":
            cardsets.sort(key=lambda cardset: (cardset.last_date, cardset.title))
        elif mode == "alphabetical":
            cardsets.sort(key=lambda cardset: (cardset.title, cardset.last_date))
        else:
            raise ValueError("Invalid mode. Check input parameter.")

if __name__ == "__main__":
    today = date.today()
    cardset = CardSet(id=-1, title="Card Set 1", last_date="",
                      await_date="", create_date="")
    c1 = Card(id=-1, term="Apple", definition="red fruit",
              memor_date=today.isoformat())
    # cardset.random_insert(c1, 0, 0)
    c2 = Card(id=-1, term="Banana", definition="yellow fruit",
              memor_date=today.isoformat())
    c3 = Card(id=-1, term="Cat", definition="Cute animal",
              memor_date=today.isoformat())
    # cardset.random_insert(c3, 0, 1)
    # cardset.random_insert(c2, 0, 2)
    cardset.insert(c3)
    cardset.insert(c2)
    cardset.insert(c1)
    cardset.delete_at(0)
    # cardset.random_insert(c1, 0, 1)
    print(cardset.count)
    cardset.insert_at(c1, 2)
    print(cardset)
