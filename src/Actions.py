import tkinter as tk 
from queue import Queue
import threading  
import ComManager
import cantools 
from tkinter import messagebox, filedialog

class Actions:
    def __init__(self, root, menu, content):
        self.root = root 
        self.menu = menu 
        self.content = content 
        self.dbc_browsed = False
        self.device_connected = False
        self.stop_event = threading.Event()
        self.message_queue = Queue()
        self.sftpmanager = ComManager.SftpManager()
        self.requestthreader = ComManager.RequestThreader()
        self.configure_buttons()
        self.configure_labels()
        self.configure_search()

    def configure_buttons(self):
        self.menu.browse_button.config(command=self.browse_dbc)
        self.menu.verify_button.config(command=self.verify_connection)
        self.menu.start_button.config(command=self.start_recording)
        self.menu.stop_button.config(command=self.stop_recording, state='disabled')

    def configure_labels(self):
        self.dbc_label_text = tk.StringVar()
        self.connection_label_text = tk.StringVar()
        self.connection_label_text.set(f'{ComManager.hostname} - disconnected')
        self.connection_label_text.trace_add('write', self.on_connection_label_change)
        self.menu.display_connection_label.config(textvariable=self.connection_label_text)
        self.menu.display_dbc_label.config(textvariable=self.dbc_label_text) 

    def configure_search(self):
        self.content.search_entry.bind("<FocusIn>", self.on_entry_click)
        self.content.search_entry.bind("<FocusOut>", self.on_focus_out)
        self.content.search_entry.bind("<Return>", lambda event: self.search_items())

    def configure_tree(self):
        self.items = self.tree_items()
        self.content.tree.add_items(self.items)
        self.content.tree.bind('<<TreeviewSelect>>', self.on_tree_change)

    def on_connection_label_change(self, *args):
        if self.connection_label_text.get() == 'Loading...':
            self.requestthreader.thread_identify_request({ComManager.hostname : self.dbc_path}, self.connection_label_text)
        else:
            self.sftpmanager.sftp_upload_dbc_thread(self.dbc_path)
            self.device_connected = True

    def on_entry_click(self, event):
        if self.content.search_var.get() == 'Search a Signal here ...':
            self.content.search_var.set("")
            self.content.search_entry.configure(fg='black')

    def on_focus_out(self, event):
        if self.content.search_var.get() == "":
            self.content.search_var.set('Search a Signal here ...')
            self.content.search_entry.configure(fg='grey')

    def on_tree_change(self, event):
        self.content.tree.check_item(event)
        self.content.graph.clicked_signals = self.content.tree.clicked_list

    def browse_dbc(self):
        self.dbc_path = filedialog.askopenfilename()
        self.dbc_label_text.set(self.dbc_path)
        self.configure_tree()
        self.dbc_browsed = True
        
    def verify_connection(self):
        if not self.dbc_browsed:
            messagebox.showinfo("Warning", "Please choose a dbc file.")
            return
        self.connection_label_text.set('Loading...')

    def search_items(self):
        search_text = self.content.search_var.get().lower()
        self.content.tree.delete(*self.content.tree.get_children())
        if search_text == '':
            self.configure_tree()
        else:
            result = {'canstack2' : {}}
            for message_dict in self.items.values():
                for message, signal_list in message_dict.items():
                    if any(search_text in str(value).lower() for value in signal_list):
                        result['canstack2'][message] = signal_list
            self.content.tree.add_items(result)

    def tree_items(self):
        items = {}
        items[ComManager.hostname] = {}
        dbc = cantools.database.load_file(self.dbc_path)
        for message in dbc.messages:
            items[ComManager.hostname][message.name] = []
            for signal in message.signals:
                items[ComManager.hostname][message.name].append(signal.name) 
        return items

    def start_recording(self):
        if not self.device_connected:
            messagebox.showinfo("Warning", "Please verify the connection of your device.")
            return
        self.menu.stopwatch.start_stopwatch() 
        self.stop_event.clear()
        self.requestthreader.thread_start_request(self.message_queue, self.stop_event)
        self.content.graph.switch_oscilloscope(self.message_queue)
        self.menu.start_button.config(bg='grey', state='disabled')
        self.menu.stop_button.config(bg='red', state='normal')

    def stop_recording(self):
        self.stop_event.set()
        self.menu.stopwatch.stop_stopwatch()
        self.content.graph.switch_oscilloscope()
        self.requestthreader.thread_stop_request()
        self.menu.stop_button.config(bg='grey', state='disabled')
        self.menu.start_button.config(bg='green', state='normal')
