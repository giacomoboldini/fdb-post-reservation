import configparser
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import json
import utils
import pandastable as pdt
import pandas as pd
from connection import GoogleConnection, WhatsAppConnection
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("FDB Post Reservation")

        self._has_data = False

        self.settings = self.load_settings()
        saved_geo = self.settings.get("App", {}).get("window_geometry", "1000x600")
        self.geometry(saved_geo)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        api = self.settings.get("API", {})
        self.google_connection = GoogleConnection(
            creds_file=api.get("google_cred_file"),
            token_file=api.get("google_token_file"))
        self.whatsapp_connection = WhatsAppConnection(
            token_file=api.get("whatsapp_token_file"),
            phone_number_key=api.get("whatsapp_phone_key", "iliad"))

        # Try to restore cached sessions on startup (no browser/UI)
        self.google_connection.login()
        self.whatsapp_connection.login()

        self.create_widgets()
        self.update_ui()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _on_close(self):
        self._save_setting("App", "window_geometry", self.geometry())
        self.destroy()

    def _open_folder(self, path: str):
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _get_whatsapp_keys(self) -> list:
        """Load available phone number keys from the WhatsApp secrets file."""
        token_file = self.settings.get("API", {}).get(
            "whatsapp_token_file", "whatsapp_secrets.json")
        try:
            with open(token_file) as f:
                return list(json.load(f).get("phone_number_id", {}).keys())
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return ["test", "iliad"]

    def _show_info_popup(self, title: str, message: str):
        win = tk.Toplevel(self)
        win.title(title)
        win.resizable(False, False)
        tk.Label(win, text=message, font=("", 9), justify="left",
                 wraplength=420).pack(padx=20, pady=16)
        tk.Button(win, text="OK", width=8, command=win.destroy).pack(pady=(0, 12))
        win.grab_set()
        win.focus_set()

    def _loading_window(self, message: str) -> tk.Toplevel:
        win = tk.Toplevel(self)
        win.title("Please wait")
        tk.Label(win, text=message).pack(padx=20, pady=20)
        win.update()
        return win

    def _refresh_action_buttons(self):
        """Enable/disable action buttons based on connection state and data."""
        google_ok = self.google_connection.get_state()
        wa_ok = self.whatsapp_connection.get_state()
        day_ok = bool(self.day_combobox.get()) if hasattr(self, "day_combobox") else False

        if hasattr(self, "get_data_button"):
            self.get_data_button.config(
                state="normal" if google_ok and day_ok else "disabled")
        if hasattr(self, "button_map"):
            self.button_map.config(
                state="normal" if google_ok and self._has_data else "disabled")
            self.button_label.config(
                state="normal" if google_ok and self._has_data else "disabled")
            self.button_send.config(
                state="normal" if wa_ok and self._has_data else "disabled")

    def _save_setting(self, section: str, key: str, value: str):
        """Persist a single key to settings.ini without touching other sections."""
        config = configparser.ConfigParser()
        config.read("settings.ini")
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, value)
        with open("settings.ini", "w") as f:
            config.write(f)

    # ── Widget creation ───────────────────────────────────────────────────────

    def create_widgets(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1, minsize=200)

        # ── Connections frame (full width) ────────────────────────────────────
        connections_frame = tk.LabelFrame(self, text="Connections")
        connections_frame.grid(
            row=0, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        connections_frame.grid_columnconfigure(0, weight=0)
        connections_frame.grid_columnconfigure(1, weight=0)
        connections_frame.grid_columnconfigure(2, weight=1)
        connections_frame.grid_columnconfigure(3, weight=0)

        # Google API row
        tk.Label(connections_frame, text="Google API", anchor="w", width=13).grid(
            row=0, column=0, padx=(5, 0), pady=5, sticky="w")
        self.google_status = tk.Label(connections_frame, text="●", foreground="gray", width=2)
        self.google_status.grid(row=0, column=1, padx=0, pady=5, sticky="w")
        self.google_info = tk.Label(
            connections_frame, text="", foreground="black", anchor="w")
        self.google_info.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        g_ctrl = tk.Frame(connections_frame)
        g_ctrl.grid(row=0, column=3, padx=5, pady=5, sticky="e")
        tk.Button(g_ctrl, text="?", width=2,
                  command=self.show_google_auth_info).pack(side="left", padx=(0, 4))
        tk.Button(g_ctrl, text="Connect",
                  command=self.google_connect).pack(side="left")

        # WhatsApp API row
        tk.Label(connections_frame, text="WhatsApp API", anchor="w", width=13).grid(
            row=1, column=0, padx=(5, 0), pady=5, sticky="w")
        self.whatsapp_status = tk.Label(connections_frame, text="●", foreground="gray", width=2)
        self.whatsapp_status.grid(row=1, column=1, padx=0, pady=5, sticky="w")
        self.whatsapp_info = tk.Label(
            connections_frame, text="", foreground="black", anchor="w")
        self.whatsapp_info.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
        wa_ctrl = tk.Frame(connections_frame)
        wa_ctrl.grid(row=1, column=3, padx=5, pady=5, sticky="e")
        wa_keys = self._get_whatsapp_keys()
        active_key = self.settings.get("API", {}).get("whatsapp_phone_key", "iliad")
        tk.Label(wa_ctrl, text="Account:").pack(side="left", padx=(0, 4))
        self.phone_key_combobox = ttk.Combobox(
            wa_ctrl, values=wa_keys, state="readonly", width=6)
        self.phone_key_combobox.set(
            active_key if active_key in wa_keys else (wa_keys[0] if wa_keys else ""))
        self.phone_key_combobox.pack(side="left", padx=(0, 4))
        self.phone_key_combobox.bind("<<ComboboxSelected>>", self.on_phone_key_changed)
        tk.Button(wa_ctrl, text="?", width=2,
                  command=self.show_whatsapp_auth_info).pack(side="left", padx=(0, 4))
        tk.Button(wa_ctrl, text="Connect",
                  command=self.whatsapp_connect).pack(side="left")

        ttk.Separator(self, orient="horizontal").grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=5)

        # ── Toolbar row: day selector + Get Data + Settings ───────────────────
        toolbar = tk.Frame(self)
        toolbar.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        tk.Label(toolbar, text="Select Day:").pack(side="left", padx=(0, 6), pady=5)
        self.day_combobox = ttk.Combobox(toolbar, values=[], state="readonly", height=5)
        self.day_combobox.pack(side="left", pady=5)
        self.day_combobox.bind("<<ComboboxSelected>>", self.on_combobox_selected)
        self.get_data_button = tk.Button(
            toolbar, text="Get Data", command=self.get_data, state="disabled")
        self.get_data_button.pack(side="left", padx=(8, 0), pady=5)
        tk.Button(
            toolbar, text="⚙ Settings",
            command=self.open_settings_window).pack(side="right", pady=5)

        # ── Data table ────────────────────────────────────────────────────────
        self.table_frame = tk.Frame(self, relief="solid", bd=1)
        self.table_frame.grid(
            row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.df_table = pdt.Table(
            self.table_frame, dataframe=pd.DataFrame(), editable=False)
        self.df_table.show()

        # ── Action buttons ────────────────────────────────────────────────────
        action_frame = tk.Frame(self)
        action_frame.grid(
            row=4, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.button_send = tk.Button(
            action_frame, text="Send WhatsApp", width=15, state="disabled",
            command=self.send_whatsapp)
        self.button_send.pack(side="right", padx=(10, 0), pady=5)
        self.button_map = tk.Button(
            action_frame, text="Gen Map PDF", width=15, state="disabled",
            command=self.generate_map)
        self.button_map.pack(side="right", padx=(10, 0), pady=5)
        self.button_label = tk.Button(
            action_frame, text="Gen Labels PDF", width=15, state="disabled",
            command=self.generate_labels)
        self.button_label.pack(side="right", padx=(10, 0), pady=5)

        utils.bind_tooltip(self, self.button_send,
                           "Requires WhatsApp connection and data loaded")
        utils.bind_tooltip(self, self.button_map,
                           "Requires Google connection and data loaded")
        utils.bind_tooltip(self, self.button_label,
                           "Requires Google connection and data loaded")

    # ── Event handlers ────────────────────────────────────────────────────────

    def on_combobox_selected(self, event):
        self._has_data = False
        self.my_clear_table(self.df_table)
        self._refresh_action_buttons()

    def google_connect(self):
        api = self.settings.get("API", {})
        self.google_connection.connect(
            api.get("google_cred_file"),
            api.get("google_token_file"))
        self.update_status_widgets()

    def whatsapp_connect(self):
        selected_key = self.phone_key_combobox.get()
        self.whatsapp_connection.connect(
            self.settings.get("API", {}).get("whatsapp_token_file"),
            selected_key)
        self.settings.setdefault("API", {})["whatsapp_phone_key"] = selected_key
        self._save_setting("API", "whatsapp_phone_key", selected_key)
        self.update_status_widgets()

    def on_phone_key_changed(self, event):
        """Switching the phone key invalidates the current WhatsApp session."""
        self.whatsapp_connection.disconnect()
        self.update_status_widgets()

    def show_google_auth_info(self):
        api = self.settings.get("API", {})
        token_file = api.get("google_token_file", "—")
        self._show_info_popup(
            "Google Authentication",
            f"The app uses OAuth2 to connect to Google.\n\n"
            f"Saved token: {token_file}\n\n"
            f"To re-authenticate (e.g. switch account), delete the token file "
            f"and click Connect.")

    def show_whatsapp_auth_info(self):
        api = self.settings.get("API", {})
        token_file = api.get("whatsapp_token_file", "—")
        phone_key = self.phone_key_combobox.get() or api.get("whatsapp_phone_key", "—")
        phone_id = self.whatsapp_connection.phone_number_id or "—"
        self._show_info_popup(
            "WhatsApp Connection",
            f"The app uses the Meta Graph API to send WhatsApp messages.\n\n"
            f"Secrets file: {token_file}\n"
            f"Active account key: {phone_key}\n"
            f"Phone number ID: {phone_id}\n\n"
            f"To update credentials, edit the secrets file and click Connect.\n"
            f"To add a new phone account, add a key under \"phone_number_id\" "
            f"in the secrets file.")

    # ── Data actions ──────────────────────────────────────────────────────────

    def get_data(self):
        day = self.day_combobox.get()
        if not day:
            messagebox.showwarning("No Day Selected", "Please select a day.")
            return

        loading = self._loading_window("Loading data, please wait...")
        try:
            file_id = self.settings.get("sheets", {}).get("file_id")
            day_settings = self.settings.get("day-" + day)
            if not day_settings:
                messagebox.showwarning("Day Not Configured", "Day not configured.")
                return

            df, error = utils.google_download_worksheet(
                self.google_connection.get_credentials(),
                file_id, day_settings.get("sheet_name"))

            if df is None:
                messagebox.showerror("Error", "Failed to get data: " + error)
                return
            if df.empty:
                messagebox.showinfo(
                    "No Data",
                    f"No rows with a table number found for {day}.\n"
                    "Check that the sheet name is correct and reservations exist.")
                return

            logger.debug(df)
            self.df_table.model.df = df
            self.df_table.redraw()
            self.df_table.autoResizeColumns()
            self._has_data = True
        finally:
            self.update_idletasks()
            loading.destroy()
        self._refresh_action_buttons()

    def generate_labels(self):
        df = self.df_table.model.df
        day = self.day_combobox.get()
        if df.empty or not day:
            messagebox.showwarning(
                "Missing data",
                "Failed to generate labels because no data or day selected.")
            return
        output_dir = self.settings.get("App", {}).get("output_dir", "out")
        loading = self._loading_window("Generating Labels PDF, please wait...")
        try:
            path = utils.generate_table_labels_pdf(df, day, output_dir)
        except Exception as e:
            loading.destroy()
            messagebox.showerror("Error", f"Failed to generate labels PDF:\n{e}")
            return
        loading.destroy()
        if messagebox.askyesno("Completato",
                               f"Labels PDF generated:\n{path}\n\nOpen output folder?"):
            self._open_folder(os.path.abspath(output_dir))

    def generate_map(self):
        day = self.day_combobox.get()
        if not day:
            messagebox.showwarning(
                "Missing Data", "Failed to generate map because no day selected.")
            return
        output_dir = self.settings.get("App", {}).get("output_dir", "out")
        map_range = self.settings.get("sheets", {}).get("map_range", "t1:y50")
        loading = self._loading_window("Generating Map PDF, please wait...")
        try:
            pdf_file_path = utils.google_generate_pdf_map(
                self.google_connection.get_credentials(),
                self.settings.get("sheets", {}).get("file_id"),
                self.settings.get("day-" + day, {}).get("sheet_id"),
                output_dir, day + "-map", map_range)
        except Exception as e:
            loading.destroy()
            messagebox.showerror("Error", f"Failed to generate map PDF:\n{e}")
            return
        loading.destroy()
        if pdf_file_path is None:
            messagebox.showerror("Error", "Failed to generate map PDF.")
            return
        if messagebox.askyesno("Completato",
                               f"Map PDF generated:\n{pdf_file_path}\n\nOpen output folder?"):
            self._open_folder(os.path.abspath(output_dir))

    def send_whatsapp(self):
        df = self.df_table.model.df
        day = self.day_combobox.get()
        if df.empty or not day:
            messagebox.showwarning(
                "Missing data",
                "Failed to send WhatsApp because no data or day selected.")
            return
        if not self.whatsapp_connection.get_state():
            messagebox.showwarning(
                "WhatsApp Not Connected", "Please connect to WhatsApp first.")
            return

        day_string = self.settings.get("day-" + day, {}).get("day_string", day)

        # Filter and format phone numbers
        df = df[df["Tavolo/i"].notna() & df["Telefono"].notna()].copy()
        df["Telefono"] = df["Telefono"].astype(str).apply(
            lambda x: "+39" + x.split(".")[0])

        # Preview — user must explicitly confirm or cancel
        send_confirmed = tk.BooleanVar(value=False)
        preview = tk.Toplevel(self)
        preview.title("Preview — confirm before sending")
        preview.geometry("800x400")
        tk.Label(preview, text="Rows that will receive a message:").pack(pady=5)
        tbl_frame = tk.Frame(preview)
        tbl_frame.pack(fill="both", expand=True, padx=10, pady=10)
        pdt.Table(tbl_frame, dataframe=df, editable=False).show()
        btn_row = tk.Frame(preview)
        btn_row.pack(pady=10)
        tk.Button(btn_row, text="Cancel", width=10,
                  command=preview.destroy).pack(side="left", padx=8)
        tk.Button(btn_row, text="Confirm & Send", width=14,
                  command=lambda: [send_confirmed.set(True), preview.destroy()]).pack(
                      side="left", padx=8)
        self.wait_window(preview)

        if not send_confirmed.get():
            return

        logger.info(f"Sending WhatsApp messages for day: {day} ({day_string})")
        api = self.settings.get("API", {})
        success = utils.send_whatsapp_messages(
            self.whatsapp_connection, df, day_string, True,
            template_name=api.get("whatsapp_template_name", "image_2025"),
            api_version=api.get("whatsapp_api_version", "v25.0"),
            log_file=api.get("wp_log_file", "wp_api.log"),
            media_log_file=api.get("wp_media_log_file", "wp_media_uploads.log"),
        )
        if success:
            messagebox.showinfo("WhatsApp", "All messages sent successfully.")
        else:
            messagebox.showwarning(
                "WhatsApp", "Some messages failed to send. Check the logs.")

    # ── UI helpers ────────────────────────────────────────────────────────────

    def my_clear_table(self, table: pdt.Table):
        if not table.model.df.empty:
            table.clearTable()

    def update_status_widgets(self):
        for conn, status_lbl, info_lbl in [
                (self.google_connection,   self.google_status,   self.google_info),
                (self.whatsapp_connection, self.whatsapp_status, self.whatsapp_info)]:
            state   = conn.get_state()
            message = conn.get_message()
            status_lbl.config(text="●", foreground="green" if state else "red")
            if len(message) > 50:
                info_lbl.config(text=message[:50] + "...")
                utils.bind_tooltip(self, info_lbl, message)
            else:
                info_lbl.config(text=message)
        self._refresh_action_buttons()

    def update_ui(self):
        self.settings = self.load_settings()
        self.update_status_widgets()
        days = [d.strip() for d in
                self.settings.get("sheets", {}).get("days", "").split(",") if d.strip()]
        self.day_combobox.config(values=days)
        if days and not self.day_combobox.get():
            self.day_combobox.set(days[0])
            self._refresh_action_buttons()

    def load_settings(self) -> dict:
        if not os.path.exists("settings.ini"):
            self._create_default_settings()
        config = configparser.ConfigParser()
        config.read("settings.ini")
        return {sect: dict(config.items(sect)) for sect in config.sections()}

    def _create_default_settings(self):
        config = configparser.ConfigParser()
        config["API"] = {
            "google_cred_file":       "google_secrets_cred.json",
            "google_token_file":      "sheets.googleapis.com-python.json",
            "whatsapp_token_file":    "whatsapp_secrets.json",
            "whatsapp_phone_key":     "",
            "whatsapp_api_version":   "v25.0",
            "whatsapp_template_name": "image_2025",
            "wp_log_file":            "wp_api.log",
            "wp_media_log_file":      "wp_media_uploads.log",
        }
        config["App"] = {"output_dir": "out"}
        config["sheets"] = {"file_id": "", "days": "", "map_range": "t1:y50"}
        with open("settings.ini", "w") as f:
            config.write(f)

    # ── Settings window ───────────────────────────────────────────────────────

    def open_settings_window(self):
        win = tk.Toplevel(self)
        win.title("Settings")
        win.geometry("640x560")
        win.resizable(True, True)

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ── API tab ──────────────────────────────────────────────────────────
        api_tab = tk.Frame(notebook)
        notebook.add(api_tab, text="API")
        api_tab.columnconfigure(1, weight=1)

        api_fields = [
            ("google_cred_file",       "Google credentials file",
             "Path to the Google OAuth client secrets JSON\n"
             "(download from Google Cloud Console → APIs & Services → Credentials)"),
            ("whatsapp_token_file",    "WhatsApp secrets file",
             'JSON with keys: "access_token" and "phone_number_id": {"key": "id", ...}'),
            ("whatsapp_api_version",   "WhatsApp API version",
             'Meta Graph API version, e.g. "v25.0"'),
            ("whatsapp_template_name", "WhatsApp template name",
             'Name of the approved WhatsApp message template, e.g. "image_2025"'),
            ("wp_log_file",            "WA API log file",
             "Path for the WhatsApp API call log file"),
            ("wp_media_log_file",      "WA media upload log file",
             "Path for the WhatsApp media upload log file"),
        ]
        api_entries = {}
        for i, (key, label, tip) in enumerate(api_fields):
            tk.Label(api_tab, text=label + ":", anchor="w").grid(
                row=i * 2, column=0, padx=10, pady=(10, 0), sticky="w")
            tk.Label(api_tab, text=tip, anchor="w", foreground="grey", font=("", 8)).grid(
                row=i * 2 + 1, column=0, padx=12, pady=(0, 6), sticky="w")
            entry = tk.Entry(api_tab, width=38)
            entry.insert(0, self.settings.get("API", {}).get(key, ""))
            entry.grid(row=i * 2, column=1, padx=10, pady=(10, 0),
                       sticky="ew", rowspan=2)
            api_entries[key] = entry

        # ── Sheets & Days tab ────────────────────────────────────────────────
        sheets_tab = tk.Frame(notebook)
        notebook.add(sheets_tab, text="Sheets & Days")
        sheets_tab.columnconfigure(1, weight=1)
        sheets_tab.rowconfigure(3, weight=1)

        tk.Label(sheets_tab, text="Google Sheet file ID:", anchor="w").grid(
            row=0, column=0, padx=10, pady=(10, 4), sticky="w")
        file_id_entry = tk.Entry(sheets_tab, width=45)
        file_id_entry.insert(
            0, self.settings.get("sheets", {}).get("file_id", ""))
        file_id_entry.grid(row=0, column=1, padx=10, pady=(10, 4), sticky="ew")

        tk.Label(sheets_tab, text="Map cell range:", anchor="w").grid(
            row=1, column=0, padx=10, pady=4, sticky="w")
        map_range_entry = tk.Entry(sheets_tab, width=45)
        map_range_entry.insert(
            0, self.settings.get("sheets", {}).get("map_range", "t1:y50"))
        map_range_entry.grid(row=1, column=1, padx=10, pady=4, sticky="ew")

        tk.Label(sheets_tab, text="Output directory:", anchor="w").grid(
            row=2, column=0, padx=10, pady=(4, 8), sticky="w")
        output_dir_entry = tk.Entry(sheets_tab, width=45)
        output_dir_entry.insert(
            0, self.settings.get("App", {}).get("output_dir", "out"))
        output_dir_entry.grid(row=2, column=1, padx=10, pady=(4, 8), sticky="ew")

        # ── Days LabelFrame (list + editor side by side) ─────────────────────
        current_days = []
        raw_days = self.settings.get("sheets", {}).get("days", "")
        for day_key in [s.strip() for s in raw_days.split(",") if s.strip()]:
            day_section = self.settings.get(f"day-{day_key}", {})
            current_days.append({
                "key":        day_key,
                "sheet_name": day_section.get("sheet_name", ""),
                "sheet_id":   day_section.get("sheet_id", ""),
                "day_string": day_section.get("day_string", ""),
            })

        days_frame = tk.LabelFrame(sheets_tab, text="Days")
        days_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=4,
                        sticky="nsew")
        days_frame.columnconfigure(0, weight=1)
        days_frame.columnconfigure(2, weight=2)
        days_frame.rowconfigure(0, weight=1)

        # Left: listbox + list action buttons
        days_listbox_frame = tk.Frame(days_frame)
        days_listbox_frame.grid(
            row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        days_listbox_frame.columnconfigure(0, weight=1)
        days_listbox_frame.rowconfigure(0, weight=1)
        days_listbox = tk.Listbox(
            days_listbox_frame, height=6, exportselection=False)
        days_listbox.grid(row=0, column=0, sticky="nsew")
        days_scrollbar = tk.Scrollbar(
            days_listbox_frame, orient="vertical", command=days_listbox.yview)
        days_scrollbar.grid(row=0, column=1, sticky="ns")
        days_listbox.config(yscrollcommand=days_scrollbar.set)

        list_btn_frame = tk.Frame(days_listbox_frame)
        list_btn_frame.grid(row=1, column=0, columnspan=2, pady=(4, 0), sticky="w")
        tk.Button(list_btn_frame, text="+ Add",
                  command=lambda: add_day()).pack(side="left", padx=(0, 6))
        tk.Button(list_btn_frame, text="↑", width=2,
                  command=lambda: move_up()).pack(side="left", padx=(0, 2))
        tk.Button(list_btn_frame, text="↓", width=2,
                  command=lambda: move_down()).pack(side="left", padx=(0, 6))
        tk.Button(list_btn_frame, text="Remove",
                  command=lambda: remove_day()).pack(side="left")

        ttk.Separator(days_frame, orient="vertical").grid(
            row=0, column=1, sticky="ns", padx=6)

        # Right: form + update button
        day_form_frame = tk.Frame(days_frame)
        day_form_frame.grid(
            row=0, column=2, sticky="nsew", padx=(0, 8), pady=8)
        day_form_frame.columnconfigure(1, weight=1)

        day_key_var  = tk.StringVar()
        day_name_var = tk.StringVar()
        day_id_var   = tk.StringVar()
        day_str_var  = tk.StringVar()

        for i, (label_text, string_var) in enumerate([
            ("Key (e.g. gio)",              day_key_var),
            ("Sheet name (e.g. Gio 03)",    day_name_var),
            ("Sheet GID (numeric)",         day_id_var),
            ("Day label (e.g. Giovedì 03)", day_str_var),
        ]):
            tk.Label(day_form_frame, text=label_text + ":", anchor="w").grid(
                row=i, column=0, padx=(0, 6), pady=3, sticky="w")
            tk.Entry(day_form_frame, textvariable=string_var).grid(
                row=i, column=1, pady=3, sticky="ew")

        day_btn_frame = tk.Frame(day_form_frame)
        day_btn_frame.grid(
            row=4, column=0, columnspan=2, pady=(10, 0), sticky="w")
        tk.Button(day_btn_frame, text="Update",
                  command=lambda: update_day()).pack(side="left")

        def refresh_listbox():
            days_listbox.delete(0, tk.END)
            for day in current_days:
                days_listbox.insert(
                    tk.END,
                    f"{day['key']}  —  {day['day_string']}"
                    f"  ({day['sheet_name']})")

        refresh_listbox()

        def on_day_select(event):
            sel = days_listbox.curselection()
            if not sel:
                return
            day = current_days[sel[0]]
            day_key_var.set(day["key"])
            day_name_var.set(day["sheet_name"])
            day_id_var.set(day["sheet_id"])
            day_str_var.set(day["day_string"])

        days_listbox.bind("<<ListboxSelect>>", on_day_select)

        def add_day():
            base, existing = "new", {d["key"] for d in current_days}
            key, n = base, 1
            while key in existing:
                key = f"{base}_{n}"
                n += 1
            current_days.append(
                {"key": key, "sheet_name": "", "sheet_id": "", "day_string": ""})
            refresh_listbox()
            idx = len(current_days) - 1
            days_listbox.selection_clear(0, tk.END)
            days_listbox.selection_set(idx)
            days_listbox.see(idx)
            day_key_var.set(key)
            day_name_var.set("")
            day_id_var.set("")
            day_str_var.set("")

        def update_day():
            sel = days_listbox.curselection()
            if not sel:
                messagebox.showwarning(
                    "No selection", "Select a day from the list first.", parent=win)
                return
            day_key = day_key_var.get().strip()
            if not day_key:
                messagebox.showwarning(
                    "Missing", "Day key is required.", parent=win)
                return
            current_days[sel[0]] = {
                "key":        day_key,
                "sheet_name": day_name_var.get().strip(),
                "sheet_id":   day_id_var.get().strip(),
                "day_string": day_str_var.get().strip(),
            }
            refresh_listbox()
            days_listbox.selection_set(sel[0])

        def move_up():
            sel = days_listbox.curselection()
            if not sel or sel[0] == 0:
                return
            i = sel[0]
            current_days[i - 1], current_days[i] = current_days[i], current_days[i - 1]
            refresh_listbox()
            days_listbox.selection_set(i - 1)
            days_listbox.see(i - 1)

        def move_down():
            sel = days_listbox.curselection()
            if not sel or sel[0] >= len(current_days) - 1:
                return
            i = sel[0]
            current_days[i], current_days[i + 1] = current_days[i + 1], current_days[i]
            refresh_listbox()
            days_listbox.selection_set(i + 1)
            days_listbox.see(i + 1)

        def remove_day():
            sel = days_listbox.curselection()
            if not sel:
                return
            current_days.pop(sel[0])
            refresh_listbox()
            for var in (day_key_var, day_name_var, day_id_var, day_str_var):
                var.set("")

        # ── Save ─────────────────────────────────────────────────────────────
        def do_save():
            config = configparser.ConfigParser()
            new_settings = {}

            config.add_section("API")
            new_settings["API"] = {}
            for key, entry in api_entries.items():
                val = entry.get().strip()
                config.set("API", key, val)
                new_settings["API"][key] = val
            # Preserve fields not shown in the settings UI
            for hidden_key in ("google_token_file", "whatsapp_phone_key"):
                val = self.settings.get("API", {}).get(hidden_key, "")
                config.set("API", hidden_key, val)
                new_settings["API"][hidden_key] = val

            config.add_section("App")
            output_dir = output_dir_entry.get().strip() or "out"
            config.set("App", "output_dir", output_dir)
            new_settings["App"] = {"output_dir": output_dir}

            config.add_section("sheets")
            days_str  = ", ".join(d["key"] for d in current_days)
            file_id   = file_id_entry.get().strip()
            map_range = map_range_entry.get().strip() or "t1:y50"
            config.set("sheets", "file_id",    file_id)
            config.set("sheets", "days",       days_str)
            config.set("sheets", "map_range",  map_range)
            new_settings["sheets"] = {
                "file_id": file_id, "days": days_str, "map_range": map_range}

            for d in current_days:
                sect = f"day-{d['key']}"
                config.add_section(sect)
                new_settings[sect] = {}
                for k in ("sheet_name", "sheet_id", "day_string"):
                    config.set(sect, k, d.get(k, ""))
                    new_settings[sect][k] = d.get(k, "")

            with open("settings.ini", "w") as f:
                config.write(f)

            self.settings = new_settings
            new_key = new_settings.get("API", {}).get("whatsapp_phone_key", "")
            wa_keys = self._get_whatsapp_keys()
            self.phone_key_combobox.config(values=wa_keys)
            if new_key in wa_keys:
                self.phone_key_combobox.set(new_key)

            win.destroy()
            self.update_ui()

        tk.Button(win, text="Save", command=do_save, width=12).pack(pady=8)


if __name__ == "__main__":
    app = App()
    app.mainloop()
