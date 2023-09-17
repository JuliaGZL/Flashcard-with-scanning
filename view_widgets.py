import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from cards import Card, CardSet
from datetime import date

''' Word Widgets '''

ctk.set_appearance_mode("light")
today = date.today()


class CardSetWidget(ctk.CTkFrame):
    def __init__(self, master, cardset: CardSet, idx: int, *args):
        super().__init__(master, *args, fg_color="white")
        # Initialize data
        self.cardset = cardset
        self.title = cardset.title
        self.last_date = cardset.last_date
        self.CREATE_DATE = cardset.CREATE_DATE
        self.cardset_id = cardset.id
        self.await_date = cardset.await_date
        self.idx = idx
        self.today = date.today()

        # Widgets
        self.title_lbl = ctk.CTkLabel(self, text=f"Title: {self.title}", wraplength=350)
        self.last_date_lbl = ctk.CTkLabel(
            self, text=f"Last date: {self.last_date}")
        self.create_date_lbl = ctk.CTkLabel(
            self, text=f"Create date: {self.CREATE_DATE}")
        self.separator = ttk.Separator(self, orient="horizontal")

        # Packing widgets
        self.title_lbl.pack(padx=5, pady=7)
        self.separator.pack(fill="x")
        self.last_date_lbl.pack(padx=5, pady=5)
        self.create_date_lbl.pack(padx=5, pady=5)

        # Binding widgets
        self.title_lbl.bind(
            "<Button-1>", lambda event: self.master.master.master.master.click_cardset(event, self.idx))
        self.separator.bind(
            "<Button-1>", lambda event: self.master.master.master.master.click_cardset(event, self.idx))
        self.last_date_lbl.bind(
            "<Button-1>", lambda event: self.master.master.master.master.click_cardset(event, self.idx))
        self.create_date_lbl.bind(
            "<Button-1>", lambda event: self.master.master.master.master.click_cardset(event, self.idx))
        self.bind(
            "<Button-1>", lambda event: self.master.master.master.master.click_cardset(event, self.idx))

        # Change background color
        self.configure(fg_color="white")
        if self.today.isoformat() >= self.await_date:
            self.change_color("blue")
        else:
            self.change_color("default")

    # Change border color of CardSetWidget
    def change_color(self, color: str) -> None:
        if color == "blue":
            self.configure(border_color="#C9EBFF", border_width=3)
        elif color == "default":
            self.configure(border_color="black", border_width=3)
        elif color == "green":
            self.configure(border_color="#c0e1c5", border_width=3)
        else:
            raise ValueError("Color indicated does not exist!")


class TextListWidget(ctk.CTkFrame):
    def __init__(self, master, text: str, *args):
        super().__init__(master, *args)
        # Initialize data
        self.text = text
        self.width = 600

        # Widgets
        self.text_lbl = ctk.CTkLabel(self, text=self.text, wraplength=500)
        self.separator = ttk.Separator(self)

        # Packing
        self.text_lbl.pack(side=ctk.TOP, padx=5, pady=5)
        self.separator.pack(side=ctk.BOTTOM, padx=5, pady=3)


class WordWidget(ctk.CTkFrame):
    def __init__(self, master, card: Card, *args):
        super().__init__(master, fg_color="#f2f2f2", *args)
        self.configure(width=40, border_color="dark_color")
        self.card = card
        self.separator = ttk.Separator(self, orient="horizontal")
        self.lblTerm = ctk.CTkLabel(
            self, text=card.term, width=1224, bg_color="transparent", wraplength=1200)
        self.lblDef = ctk.CTkLabel(
            self, text=card.definition, width=1224, bg_color="transparent", wraplength=1200)
        self.card_id = card.id

        if self.card.memor_date <= today.isoformat():
            self.configure(border_color="#C9EBFF", border_width=2)
            print("Blue")
        else:
            self.configure(border_color="black", border_width=2)
            print("Black")

        if type(self) == WordWidget:
            self.pack_components()

    def pack_components(self) -> None:
        self.lblTerm.pack(padx=5, pady=5)
        self.separator.pack(fill="x")
        self.lblDef.pack(padx=5, pady=5)

    def to_WordDelWidget(self, master, del_var=tk.BooleanVar):
        return WordDelWidget(master, self.card, del_var)


class WordDelWidget(WordWidget):
    def __init__(self, master, card: Card, del_var: tk.BooleanVar, *args):
        super().__init__(master, card, *args)
        self.del_var = del_var
        self.checkDel = ttk.Checkbutton(
            self, variable=self.del_var, onvalue=True, offvalue=False)
        if type(self) == WordDelWidget:
            self.pack_card()

    def pack_card(self):
        super().pack_components()

    def pack_all_components(self):
        self.checkDel.pack(side=tk.LEFT)
        super().pack_components()

    def hide_checkboxes(self):
        self.checkDel.pack_forget()

    def show_checkboxes(self):
        self.checkDel.pack(side=tk.LEFT)


class WordEntryWidget(WordWidget):
    def __init__(self, master, card: Card, *args):
        super().__init__(master, card, *args)
        self.term_txt = ctk.CTkEntry(self, width=1224)
        self.def_txt = ctk.CTkEntry(self, width=1224)
        self.term_txt.insert(0, self.card.term)
        self.def_txt.insert(0, self.card.definition)
        if type(self) == WordEntryWidget:
            self.pack_components()

    def pack_components(self) -> None:
        self.term_txt.pack(padx=5, pady=5)
        self.separator.pack()
        self.def_txt.pack(padx=5, pady=5)


''' Automatic adding - centry table '''


if __name__ == "__main__":
    main = tk.Tk()
    var = tk.BooleanVar()
    # test_widget = WordWidget(main, Card(-1, "Test", "Def"))
    # test_widget.pack()
    # test2 = WordEntryWidget(main, Card(-1, "Test", "Def"))
    test_widget = TextListWidget(main, "Test this text")
    test_widget.pack()

    main.mainloop()
