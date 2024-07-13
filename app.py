import tkinter as tk
from tkinter import messagebox
import json
from app_configurator import AppConfigurator
import pygsheets
import utils


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FDB Post Reservation")
        self.geometry("600x400")

        self.config = self.load_config()
        # self.secrets = self.load_secrets()
        self.configurator = None

        # if not self.secrets:
        #     self.destroy()
        #     return

        # if not self.config:
        #     self.configure_options()

        self.create_status_widgets()

        # Create a button for configuring options
        # self.configure_button = tk.Button(self, text="Configure Options", command=self.configure_options)
        # self.configure_button.pack()

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

    def create_status_widgets(self):
        # Check Google Sheet connection
        if utils.check_google_login():
            self.google_status_label = tk.Label(self, text="Google Sheet: Connected")
        else:
            self.google_status_label = tk.Label(self, text="Google Sheet: Disconnected")
        self.google_status_label.pack()
        self.google_connect_button = tk.Button(self, text="Connect to Google Sheet", command=self.google_connect())
        self.google_connect_button.pack()

    def update_status_widgets(self):
        if utils.check_google_login():
            self.google_status_label.config(text="Google Sheet: Connected")
        else:
            self.google_status_label.config(text="Google Sheet: Disconnected")

    def google_connect(self):
        self.google_creds = utils.google_login()
        self.update_status_widgets()

if __name__ == "__main__":
    app = App()
    app.mainloop()
