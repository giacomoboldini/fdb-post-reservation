import configparser
import tkinter as tk
from tkinter import messagebox, ttk
import json
from app_configurator import AppConfigurator
import pygsheets
import utils
import pandastable as pdt
import pandas as pd
from connection import GoogleConnection, WhatsAppConnection
import logging

# TODO-FIX: get data works despite google api not connected - CHECK

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PHONE_NUMBER_KEY = "iliad" # "iliad" or "test" - Default phone number key for WhatsApp connection

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("FDB Post Reservation")
        self.geometry("1000x600")

        self.settings = self.load_settings()
        self.google_connection = GoogleConnection(
            creds_file=self.settings.get("API").get("google_cred_file"),
            token_file=self.settings.get("API").get("google_token_file"))
        self.whatsapp_connection = WhatsAppConnection(
            token_file=self.settings.get("API").get("whatsapp_token_file"),
            phone_number_key=PHONE_NUMBER_KEY)

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

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)  # Ensures row 2 (table area) expands vertically

        # Connections LabelFrame
        connections_frame = tk.LabelFrame(self, text="Connections")
        connections_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

        # Configure grid for connections_frame
        connections_frame.grid_columnconfigure(0, weight=1)
        connections_frame.grid_columnconfigure(1, weight=0)
        connections_frame.grid_columnconfigure(2, weight=4)
        connections_frame.grid_columnconfigure(3, weight=1)

        # Google API
        google_label = tk.Label(connections_frame, text="Google API", anchor="w", width=13)
        google_label.grid(row=0, column=0, padx=(5,0), pady=5, sticky="w")
        self.google_status = tk.Label(connections_frame, text="●", fg="black", width=2)  # Example status
        self.google_status.grid(row=0, column=1, padx=0, pady=5, sticky="w")
        self.google_info = tk.Label(connections_frame, text="", fg="black", width=30, anchor="w")
        self.google_info.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        google_button = tk.Button(connections_frame, text="Connect", command=self.google_connect)
        google_button.grid(row=0, column=3, padx=5, pady=5, sticky="e")

        # Whatsapp API
        whatsapp_label = tk.Label(connections_frame, text="Whatsapp API", anchor="w", width=13)
        whatsapp_label.grid(row=1, column=0, padx=(5,0), pady=5, sticky="w")
        self.whatsapp_status = tk.Label(connections_frame, text="●", fg="black", width=2)  # Example status
        self.whatsapp_status.grid(row=1, column=1, padx=0, pady=5, sticky="w")
        self.whatsapp_info = tk.Label(connections_frame, text="", fg="black", width=30, anchor="w")
        self.whatsapp_info.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
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
        get_data_frame = tk.Frame(self)
        get_data_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        day_label = tk.Label(get_data_frame, text="Select Day:")
        day_label.pack(side="left", padx=(0,10), pady=5)
        self.day_combobox = ttk.Combobox(get_data_frame, values=[], state="readonly", height=5)
        self.day_combobox.pack(side="left", padx=(10,0), pady=5)
        self.day_combobox.bind("<<ComboboxSelected>>", self.on_combobox_selected)

        # Get data button
        self.get_data_button = tk.Button(get_data_frame, text="Get Data", command=self.get_data, state="disabled")
        self.get_data_button.pack(side="right", padx=(10,0), pady=5)

        # Table
        self.table_frame = tk.Frame(self, height=400, relief="solid", bd=1)
        self.table_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.df_table = pdt.Table(self.table_frame, dataframe=pd.DataFrame(), editable=False)
        self.df_table.show()

        # Action buttons
        action_frame = tk.Frame(self)
        action_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.button_send = tk.Button(action_frame, text="Send WhatsApp", width=15, state="disabled", command=self.send_whatsapp)
        self.button_send.pack(side="right", padx=(10,0), pady=5)
        self.button_map = tk.Button(action_frame, text="Gen Map PDF", width=15, state="disabled", command=self.generate_map)
        self.button_map.pack(side="right", padx=(10,0), pady=5)
        self.button_label = tk.Button(action_frame, text="Gen Labels PDF", width=15, state="disabled", command=self.generate_labels)
        self.button_label.pack(side="right", padx=(10,0), pady=5)

    def on_combobox_selected(self, event):
        if self.google_connection.get_state() and self.day_combobox.get():
            self.get_data_button.config(state="normal")
        self.my_clear_table(self.df_table)

    def generate_labels(self):
        """
        Generate the pdf with the labels starting from the data in the table.

        Returns:
            None
        """
        df = self.df_table.model.df
        day = self.day_combobox.get()
        if df.empty or not day:
            messagebox.showwarning("Missing data", "Failed to generate labels because no data or day selected.")
            return
        
        loading_message = tk.Toplevel(self)
        loading_message.title("Generating")
        tk.Label(loading_message, text="Generating Labels PDF, please wait...").pack(padx=20, pady=20)
        loading_message.update()

        utils.generate_table_labels_pdf(df, day, "out")

        loading_message.destroy()
        # Show success message
        messagebox.showinfo("Completato", "File PDF generato con successo:\nout/labels.pdf")

    def generate_map(self):
        """
        Generate the map pdf with the locations of the reservations.
        Needs the Google API credentials to work.

        Returns:
            None
        """
        day = self.day_combobox.get()
        if not day:
            messagebox.showwarning("Missing Data", "Failed to generate map because no day selected.")
            return

        loading_message = tk.Toplevel(self)
        loading_message.title("Generating")
        tk.Label(loading_message, text="Generating Map PDF, please wait...").pack(padx=20, pady=20)
        loading_message.update()

        pdf_file_path = utils.google_generate_pdf_map(self.google_connection.get_credentials(), self.settings.get("sheets").get("file_id"), self.settings.get("day-" + day).get("sheet_id"), "out", day + "-map")
        loading_message.destroy()
        if pdf_file_path is None:
            messagebox.showerror("Error", "Failed to generate map PDF.")
            return
        # Show success message
        messagebox.showinfo("Completato", f"File PDF generato con successo:\n{pdf_file_path}")

    def get_data(self):
        """
        Download the data from the Google Sheets, save it in a dataframe and
        show it in the table.
        Needs the Google API credentials to work.

        Returns:
            None
        """
        print("Getting data... " + self.day_combobox.get())
        day = self.day_combobox.get()
        # TODO: remove because button should be disabled if no day is selected
        if not day:
            messagebox.showwarning("No Day Selected", "Please select a day.")
            return

        # Show loading message box
        loading_message = tk.Toplevel(self)
        loading_message.title("Loading")
        tk.Label(loading_message, text="Loading data, please wait...").pack(padx=20, pady=20)
        loading_message.update()

        try:
            # Get data from Google Sheets
            file_id = self.settings.get("sheets").get("file_id")
            day_settings = self.settings.get("day-" + day)
            if not day_settings:
                messagebox.showwarning("Day Not Configured", "Day not configured.")
                return

            df, error = utils.google_download_worksheet(self.google_connection.get_credentials(), file_id, day_settings.get("sheet_name"))

            if df is None:
                messagebox.showerror("Error", "Failed to get data: " + error)
            if not df.empty:
                print(df)
                self.df_table.model.df = df
                self.df_table.show()
                self.df_table.redraw()
                self.button_send.config(state="normal")
                self.button_map.config(state="normal")
                self.button_label.config(state="normal")
        finally:
            self.update_idletasks()
            # Close loading message box
            loading_message.destroy()
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

        for conn, status_label, info_label in [
                (self.google_connection, self.google_status, self.google_info),
                (self.whatsapp_connection, self.whatsapp_status, self.whatsapp_info)]:

            state = conn.get_state()
            message = conn.get_message()

            status_label.config(text="●", fg=("red" if not state else "green"))
            status_label.config(text="●", fg=("red" if not state else "green"))

            if len(message) > 50:
                truncated_message = (message[:50] + '...')
                info_label.config(text=truncated_message)
                self.tooltip = utils.bind_tooltip(self, info_label, message)
            else:
                info_label.config(text=message)

    def update_ui(self):
        self.settings = self.load_settings()
        self.update_status_widgets()
        google_state = self.google_connection.get_state()
        for button in [self.button_send, self.button_map, self.button_label, self.get_data_button]:
            button.config(state="disabled" if not google_state else "normal")

        self.test_label.config(text=self.settings.get("Other", {}).get("message", ""))
        self.day_combobox.config(values=self.settings.get("sheets").get("days").split(", "))

    def google_connect(self):
        self.google_connection.connect(
            self.settings.get("API").get("google_cred_file"),
            self.settings.get("API").get("google_token_file"))
        self.update_status_widgets()
        google_state = self.google_connection.get_state()
        for button in [self.button_send, self.button_map, self.button_label, self.get_data_button]:
            button.config(state="disabled" if not google_state else "normal")

    def whatsapp_connect(self):
        self.whatsapp_connection.connect(
            self.settings.get("API").get("whatsapp_token_file"),
            PHONE_NUMBER_KEY)
        self.update_status_widgets()

    def my_clear_table(self, table: pdt.Table):
        if table.model.df.empty:
            return
        table.clearTable()

    def send_whatsapp(self):
        """
        Send the message to the phone numbers in the table.
        Needs the WhatsApp API credentials to work.

        Returns:
            None
        """
        df = self.df_table.model.df
        day = self.day_combobox.get()
        if df.empty or not day:
            messagebox.showwarning("Missing data", "Failed to send WhatsApp because no data or day selected.")
            return

        # Check connection state before proceeding
        if not self.whatsapp_connection.get_state():
            messagebox.showwarning("WhatsApp Not Connected", "Please connect to WhatsApp first.")
            return

        # Clean the dataframe
        df = df[df["Tavolo/i"].notna()]
        df = df[df["Telefono"].notna()]
        df["Telefono"] = df["Telefono"].astype(str).apply(lambda x: "+39" + x.split(".")[0])

        # Show the dataframe in an external window before sending
        preview_window = tk.Toplevel(self)
        preview_window.title("Dataframe Preview")
        preview_window.geometry("800x400")
        tk.Label(preview_window, text="Dataframe for message sending:").pack(pady=5)
        table_frame = tk.Frame(preview_window)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        preview_table = pdt.Table(table_frame, dataframe=df, editable=False)
        preview_table.show()

        def continue_and_close():
            preview_window.destroy()
            # Continue with sending after closing preview

        continue_button = tk.Button(preview_window, text="Continue", command=continue_and_close)
        continue_button.pack(pady=10)

        # Wait for the preview window to close before continuing
        self.wait_window(preview_window)

        # skipped = []
        # image_filename = os.path.join(os.path.dirname(__file__), "out", f"{day}.png")


        logger.info(f"Sending WhatsApp messages for day: {day}")
        success = utils.send_whatsapp_messages(self.whatsapp_connection, df, day, True)
        if success:
            messagebox.showinfo("WhatsApp", "All messages sent successfully.")
        else:
            messagebox.showwarning("WhatsApp", "Some messages failed to send. Check the logs.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
