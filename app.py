import configparser
import tkinter as tk
import json
from app_configurator import AppConfigurator
import pygsheets
import utils
import customtkinter as ctk

# Sets the appearance mode of the application
# "System" sets the appearance same as that of the system
ctk.set_appearance_mode("System")        
 
# Sets the color of the widgets
# Supported themes: green, dark-blue, blue
ctk.set_default_color_theme("green")  

class App(ctk.CTk):
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
        self.test_label = ctk.CTkLabel(self, text=self.settings.get("message"), anchor="w", width=15)
        self.test_label.pack(padx=10, pady=5, anchor='w')
        settings_button = ctk.CTkButton(self, text='Settings', command=self.open_settings_window)
        settings_button.pack(pady=10)


        labelframe = tk.LabelFrame(self, text="Connections")
        labelframe.pack(padx=10, pady=10, anchor='w', fill="x")

        # Google API
        google_label = ctk.CTkLabel(labelframe, text="Google API", anchor="w", width=15)
        google_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.google_status = ctk.CTkLabel(labelframe, text="○", fg_color="black", width=2)  # Placeholder
        self.google_status.grid(row=0, column=1, padx=10, pady=5)
        google_button = ctk.CTkButton(labelframe, text="Connect", command=self.google_connect)
        google_button.grid(row=0, column=2, padx=10, pady=5)

        # Whatsapp API
        whatsapp_label = ctk.CTkLabel(labelframe, text="Whatsapp API", anchor="w", width=15)
        whatsapp_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.whatsapp_status = ctk.CTkLabel(labelframe, text="○", fg_color="black", width=2)  # Placeholder
        self.whatsapp_status.grid(row=1, column=1, padx=10, pady=5)
        whatsapp_button = ctk.CTkButton(labelframe, text="Connect")#, command=lambda: self.connect_api("Whatsapp API"))
        whatsapp_button.grid(row=1, column=2, padx=10, pady=5)
        self.whatsapp_info = ctk.CTkLabel(labelframe, text="", fg_color="black", wraplength=500)
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
        settings_window = ctk.CTkToplevel(self)
        settings_window.title('Settings')

        # Create and populate settings widgets based on self.settings
        # Example:
        message_label = ctk.CTkLabel(settings_window, text='Message:')
        message_entry = ctk.CTkEntry(settings_window, textvariable=ctk.CTkStringVar(value=self.settings.get('message', '')))
        message_label.grid(row=0, column=0, padx=10, pady=5)
        message_entry.grid(row=0, column=1, padx=10, pady=5)

        # Save button
        save_button = ctk.CTkButton(settings_window, text='Save', command=lambda: self.save_settings(settings_window, message_entry.get()))
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
            self.google_status.configure(text="●", fg_color="green")
        else:
            self.google_status.configure(text="●", fg_color="red")

        whatsapp_status, message = utils.check_whatsapp_login("whatsapp_secrets.json", "iliad")
        if whatsapp_status:
            self.whatsapp_status.configure(text="●", fg_color="green")
        else:
            self.whatsapp_status.configure(text="●", fg_color="red")
            if message:
                self.whatsapp_info.configure(text=message)
                self.whatsapp_info.grid()
            else:
                self.whatsapp_info.configure(text="")
                self.whatsapp_info.grid_remove()

    def update_ui(self):
        self.test_label.configure(text=self.settings.get("message"))
        # self.update_status_widgets() # ??

    def google_connect(self):
        self.google_creds = utils.google_login()
        self.update_status_widgets()

if __name__ == "__main__":
    app = App()
    app.mainloop()
