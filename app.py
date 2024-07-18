import configparser
import tkinter as tk
from tkinter import messagebox, ttk
import json
from app_configurator import AppConfigurator
import pygsheets
import utils
import pandastable as pdt
import pandas as pd

# TODO: unify login with credentials (google)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FDB Post Reservation")
        self.geometry("1000x600")

        # Load settings from settings.ini
        self.settings = self.load_settings()

        # Create widgets
        self.create_widgets()

        # Fill with the data
        self.update_ui()

        # self.config = self.load_config()
        # self.secrets = self.load_secrets()
        # self.configurator = None

        # if not self.secrets:
        #     self.destroy()
        #     return

        # if not self.config:
        #     self.configure_options()

        # self.create_status_widgets()

        # Create a button for configuring options
        # self.configure_button = tk.Button(self, text="Configure Options", command=self.configure_options)
        # self.configure_button.pack()

    def create_widgets(self) -> None:


        # self.grid_columnconfigure(0, weight=1)
        # self.grid_columnconfigure(1, weight=1)

        # Connections LabelFrame
        connections_frame = tk.LabelFrame(self, text="Connections")
        connections_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        # Configure grid for connections_frame
        # connections_frame.grid_columnconfigure(0, weight=1)
        # connections_frame.grid_columnconfigure(1, weight=0)
        # connections_frame.grid_columnconfigure(2, weight=4)
        # connections_frame.grid_columnconfigure(3, weight=1)

        # Google API
        google_label = tk.Label(connections_frame, text="Google API", anchor="w", width=13)
        google_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.google_status = tk.Label(connections_frame, text="●", fg="green", width=2)  # Example status
        self.google_status.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.google_info = tk.Label(connections_frame, text="", fg="black", width=30, anchor="w")
        self.google_info.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        google_button = tk.Button(connections_frame, text="Connect", command=self.google_connect)
        google_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

        # Whatsapp API
        whatsapp_label = tk.Label(connections_frame, text="Whatsapp API", anchor="w", width=13)
        whatsapp_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.whatsapp_status = tk.Label(connections_frame, text="●", fg="green", width=2)  # Example status
        self.whatsapp_status.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.whatsapp_info = tk.Label(connections_frame, text="", fg="black", width=30, anchor="w")
        self.whatsapp_info.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        whatsapp_button = tk.Button(connections_frame, text="Connect", command=self.whatsapp_connect)
        whatsapp_button.grid(row=1, column=3, padx=5, pady=5, sticky="e")

        # Settings LabelFrame
        settings_frame = tk.LabelFrame(self, text="Settings")
        settings_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")

        self.test_label = tk.Label(settings_frame, text=self.settings["Other"]["message"], anchor="w", width=15)
        self.test_label.pack(padx=10, pady=5, anchor='w')
        settings_button = tk.Button(settings_frame, text='Settings', command=self.open_settings_window)
        settings_button.pack(pady=10, anchor='e')

        # Select day (dropdown)
        day_label = tk.Label(self, text="Select Day:")
        day_label.grid(row=1, column=0, padx=10, pady=5)
        self.day_combobox = ttk.Combobox(self, values=[])
        self.day_combobox.grid(row=1, column=1, padx=10, pady=5)

        # Get data button
        get_data_button = tk.Button(self, text="Get Data", command=self.get_data)
        get_data_button.grid(row=2, column=0, padx=10, pady=5, columnspan=2)

        # Table
        self.table_frame = tk.Frame(self, height=400)
        self.table_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

    def get_data(self):
        print("Getting data... " + self.day_combobox.get())
        day = self.day_combobox.get()
        if not day:
            messagebox.showwarning("No Day Selected", "Please select a day.")
            return
        # Get data from Google Sheets
        file_id = self.settings.get("sheets").get("file_id")
        day_settings = self.settings.get("day-" + day)
        if not day_settings:
            messagebox.showwarning("Day Not Configured", "Day not configured.")
            return
        print(day_settings)
        df = utils.download_worksheet(file_id, day_settings.get("sheet_name"), self.settings.get("API").get("google_cred_file"))
        print(df)
        table = pdt.Table(self.table_frame, dataframe=df)
        table.show()

        return

    def load_settings(self) -> dict:
        config = configparser.ConfigParser()
        config.read('settings.ini')
        settings = dict()
        for section in config.sections():
            items=config.items(section)
            settings[section]=dict(items)
        return settings

    def open_settings_window(self):
        settings_window = tk.Toplevel(self)
        settings_window.title('Settings')

        print(self.settings)

        # For each category (except sheet-* and general)
        entries = {}
        row = 0
        for sect in self.settings:
            if sect not in ["General"]:
                entries[sect] = {}
                sect_label = tk.Label(settings_window, text=sect)
                sect_label.grid(row=row, column=0, columnspan=2, padx=10, pady=5)
                row = row + 1

                for key, val in self.settings[sect].items():
                    label = tk.Label(settings_window, text=key)
                    entries[sect][key] = tk.Entry(settings_window, textvariable=tk.StringVar(value=val))
                    label.grid(row=row, column=0, padx=10, pady=5)
                    entries[sect][key].grid(row=row, column=1, padx=10, pady=5)
                    row = row + 1


        # Create and populate settings widgets based on self.settings
        # Example:
        # message_label = tk.Label(settings_window, text='Message:')
        # message_entry = tk.Entry(settings_window, textvariable=tk.StringVar(value=self.settings.get('message', '')))
        # message_label.grid(row=0, column=0, padx=10, pady=5)
        # message_entry.grid(row=0, column=1, padx=10, pady=5)

        # Save button
        save_button = tk.Button(settings_window, text='Save', command=lambda: self.save_settings(settings_window, entries))
        save_button.grid(row=row, column=0, columnspan=2, pady=10)

    def save_settings(self, settings_window, entries):
        settings = dict()
        config = configparser.ConfigParser()

        for sect in entries:
            config.add_section(sect)
            settings[sect] = dict()
            for key in entries[sect]:
                val = entries[sect][key].get()
                config.set(sect,key,val)
                settings[sect] = val
        self.settings = settings
        print(config)
        # Save settings to settings.ini
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)

        # Close settings window
        settings_window.destroy()
        self.update_ui()

    def load_secrets(self):
        try:
            with open('secrets.json', 'r') as f:
                secrets = json.load(f)
                return secrets
        except FileNotFoundError:
            messagebox.showerror("Secrets File Not Found", "Please create a secrets.json file.")
            return {}

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                return config
        except FileNotFoundError:
            messagebox.showwarning("Config File Not Found", "Please configure the app.")
            return {}

    def save_config(self, config):
        try:
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
                messagebox.showinfo("Config Saved", "Configuration saved successfully.")
        except Exception as e:
            messagebox.showerror("Error Saving Config", f"Error: {str(e)}")

    def configure_options(self):
        if not self.configurator:
            self.configurator = AppConfigurator(self, self.config)
        else:
            self.configurator.deiconify()

    def submit_selection(self):
        self.day_selection.update_config()
        self.save_config(self.config)
        selected_days = self.day_selection.get_selected_days()
        if selected_days:
            messagebox.showinfo("Selected Days", f"Selected days: {', '.join(selected_days)}")
        else:
            messagebox.showwarning("No Selection", "Please select at least one day.")

    def update_status_widgets(self):
        google_status, goole_message = utils.check_google_login(self.settings["API"]["google_token_file"])

        if google_status:
            self.google_status.config(text="●", fg="green")
            self.google_creds = utils.google_login(self.settings["API"]["google_cred_file"], self.settings["API"]["google_token_file"])
            print("Google login successful")
        else:
            self.google_status.config(text="●", fg="red")
            print("Google login failed")
        if goole_message:
            self.google_info.config(text=goole_message)
            self.google_info.grid()
        else:
            self.google_info.config(text="")
            # self.whatsapp_info.grid_remove()
        whatsapp_status, whatsapp_message = utils.check_whatsapp_login(self.settings.get("API").get("whatsapp_token_file"), "iliad")

        if whatsapp_status:
            self.whatsapp_status.config(text="●", fg="green")
        else:
            self.whatsapp_status.config(text="●", fg="red")
        if whatsapp_message:
            self.whatsapp_info.config(text=whatsapp_message)
            self.whatsapp_info.grid()
        else:
            self.whatsapp_info.config(text="")
            # self.whatsapp_info.grid_remove()

    def update_ui(self):
        self.settings = self.load_settings()
        self.update_status_widgets()
        self.test_label.config(text=self.settings.get("message"))
        self.day_combobox.config(values=self.settings.get("sheets").get("days").split(", "))

    def google_connect(self):
        self.google_creds = utils.google_login(self.settings["API"]["google_cred_file"], self.settings["API"]["google_token_file"])
        self.update_status_widgets()

    def whatsapp_connect(self):
        # Try to reconnect...
        self.whatsapp_creds = utils.whatsapp_login(self.settings["API"]["whatsapp_token_file"], "iliad")
        # Show a message on how to connect to WhatsApp
        message = "You need to configure Whastapp API and then create " + \
            "a JSON file in the format:\n" + \
            "{\n" + \
            "  \"access_token\": \"[access_token]\"\n" + \
            "  \"account_id\": \"[account_id]\"\n" + \
            "  \"phone_number_id\": {\n" + \
            "    \"id1\": \"[phone_number_id1]\"\n" + \
            "    \"id2\": \"[phone_number_id2]\"\n" + \
            "    ...\n" + \
            "  }\n"
        messagebox.showinfo("WhatsApp API", message)
        self.update_status_widgets()

if __name__ == "__main__":
    app = App()
    app.mainloop()
