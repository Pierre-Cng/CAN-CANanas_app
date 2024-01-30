import tkinter as tk
from tkinter import font as tkfont
from Widget import Stopwatch, Oscilloscope, TreeCheckList
from Actions import Actions

class App:
    def __init__(self, root):
        self.root = root
        self.Menu = Menu(self.root)
        self.Content = Content(self.root)
        self.Actions = Actions(self.root, self.Menu, self.Content)

class Menu:
    def __init__(self, root):
        # Initial setting
        self.root = root
        self.set_frame()
        self.set_font()
        # Select a DBC
        self.browse_button = self.add_button('Select dbc', row=0, column=0)
        self.display_dbc_label = self.add_label(row=0, column=1, weight=5)
        # Configuration choice 
        self.verify_button = self.add_button('Verify Connection', row=1, column=0)
        self.display_connection_label = self.add_label(row = 1, column=1)
        self.add_spacer(2, 3)
        # Recording logs 
        self.start_button = self.add_button('Start Recording', bg='green', row=1, column=3)
        self.stopwatch = Stopwatch(self.frame, self.text_font, row=1, column=4)
        self.stop_button = self.add_button('Stop Recording', bg='grey', row=1, column=5)
    
    def set_font(self):
        self.button_font = tkfont.Font(family='Trebuchet MS', size=12) 
        self.text_font = tkfont.Font(family='Trebuchet MS', size=12)

    def set_frame(self):
        self.frame = tk.Frame(self.root)
        self.frame.configure(bg='#111333', padx=20, pady=10)
        self.frame.pack(fill='both', expand=False)
    
    def add_button(self, text, bg='lightgrey', row=0, column=0):
        button = tk.Button(self.frame, text=text, borderwidth=4, bg=bg, font=self.button_font)
        self.frame.grid_columnconfigure(column, weight=1)
        button.grid(row=row, column=column, sticky="nsew", padx=10, pady=10)
        return button
    
    def add_label(self, text='', row=0, column=0, weight=2):
        label = tk.Label(self.frame, text=text, borderwidth=1, relief="solid", justify="center", font=self.text_font, width=weight*15, height=1, anchor='n')
        self.frame.grid_columnconfigure(column, weight=weight)
        label.grid(row=row, column=column, sticky="nsew", padx=10, pady=10, columnspan=weight)
        return label
        
    def add_spacer(self, column, weight):
        self.frame.grid_columnconfigure(column, weight=weight)

class Content:
    def __init__(self, root):
        self.root = root
        self.set_frame()
        self.set_tree()
        self.graph = Oscilloscope(self.frame)
    
    def set_frame(self):
        self.frame = tk.Frame(self.root)
        self.frame.configure(padx=20, pady=50)
        self.frame.pack(fill="both", expand=False)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=40)  

    def set_tree(self):
        self.search_var = tk.StringVar(value='Search a Signal here ...')
        self.search_entry = tk.Entry(self.frame, textvariable=self.search_var, fg='grey')
        self.frame.grid_columnconfigure(0, weight=1)
        self.search_entry.grid(row=0, column=0, sticky="nsew", padx=30, pady=10)
        self.tree = TreeCheckList(self.frame)
        self.frame.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=30, pady=10)
