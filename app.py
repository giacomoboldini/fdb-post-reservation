import configparser
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

        # Load settings from settings.ini
        self.settings = self.load_settings()

        self.create_widgets()
        self.update_ui()
        self.update_status_widgets()

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

        # Test
        self.test_label = tk.Label(self, text=self.settings.get("message"), anchor="w", width=15)
        self.test_label.pack(padx=10, pady=5, anchor='w')
        settings_button = tk.Button(self, text='Settings', command=self.open_settings_window)
        settings_button.pack(pady=10)


        labelframe = tk.LabelFrame(self, text="Connections")
        labelframe.pack(padx=10, pady=10, anchor='w', fill="x")

        # Google API
        google_label = tk.Label(labelframe, text="Google API", anchor="w", width=15)
        google_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.google_status = tk.Label(labelframe, text="○", fg="black", width=2)  # Placeholder
        self.google_status.grid(row=0, column=1, padx=10, pady=5)
        google_button = tk.Button(labelframe, text="Connect", command=self.google_connect)
        google_button.grid(row=0, column=2, padx=10, pady=5)

        # Whatsapp API
        whatsapp_label = tk.Label(labelframe, text="Whatsapp API", anchor="w", width=15)
        whatsapp_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.whatsapp_status = tk.Label(labelframe, text="○", fg="black", width=2)  # Placeholder
        self.whatsapp_status.grid(row=1, column=1, padx=10, pady=5)
        whatsapp_button = tk.Button(labelframe, text="Connect")#, command=lambda: self.connect_api("Whatsapp API"))
        whatsapp_button.grid(row=1, column=2, padx=10, pady=5)
        self.whatsapp_info = tk.Label(labelframe, text="", fg="black", wraplength=500)
        self.whatsapp_info.grid(row=2, column=0, columnspan=3, padx=10, pady=0, sticky="w")
        self.whatsapp_info.grid_remove()

    def load_settings(self):
        config = configparser.ConfigParser()
        config.read('settings.ini')
        settings = {}

        if 'General' in config:
            settings['message'] = config['General'].get('message', '')
            # Add more settings as needed

        return settings

    def open_settings_window(self):
        settings_window = tk.Toplevel(self)
        settings_window.title('Settings')

        # Create and populate settings widgets based on self.settings
        # Example:
        message_label = tk.Label(settings_window, text='Message:')
        message_entry = tk.Entry(settings_window, textvariable=tk.StringVar(value=self.settings.get('message', '')))
        message_label.grid(row=0, column=0, padx=10, pady=5)
        message_entry.grid(row=0, column=1, padx=10, pady=5)

        # Save button
        save_button = tk.Button(settings_window, text='Save', command=lambda: self.save_settings(settings_window, message_entry.get()))
        save_button.grid(row=1, column=1, pady=10)

    def save_settings(self, settings_window, new_message):
        # Update settings dictionary
        self.settings['message'] = new_message

        # Save settings to settings.ini
        config = configparser.ConfigParser()
        config['General'] = {'message': new_message}

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
        if utils.check_google_login():
            self.google_status.config(text="●", fg="green")
        else:
            self.google_status.config(text="●", fg="red")

        whatsapp_status, message = utils.check_whatsapp_login("whatsapp_secrets.json", "iliad")
        if whatsapp_status:
            self.whatsapp_status.config(text="●", fg="green")
        else:
            self.whatsapp_status.config(text="●", fg="red")
            if message:
                self.whatsapp_info.config(text=message)
                self.whatsapp_info.grid()
            else:
                self.whatsapp_info.config(text="")
                self.whatsapp_info.grid_remove()

    def update_ui(self):
        self.test_label.config(text=self.settings.get("message"))
        # self.update_status_widgets() # ??

    def google_connect(self):
        self.google_creds = utils.google_login()
        self.update_status_widgets()

if __name__ == "__main__":
    app = App()
    app.mainloop()
