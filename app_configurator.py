import tkinter as ttk

class AppConfigurator(ttk.Toplevel):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.title("Configuration")
        self.geometry("400x500")

        self.config = config

        self.create_widgets()

    def create_widgets(self):

        self.google_frame = ttk.LabelFrame(self, text='Google Sheet')
        self.google_frame.pack(fill='y', expand=True)

        # Set file id
        self.file_id_label = ttk.Label(self.google_frame, text="File ID:")
        self.file_id_label.pack()
        self.file_id_entry = ttk.Entry(self.google_frame, width=60)
        self.file_id_entry.insert(0, self.config.get('file_id', ''))
        self.file_id_entry.pack()

        for day in self.config.get('days', []):
            self.create_day_widgets(self.google_frame, day)

        self.new_day_button = ttk.Button(self.google_frame, text="Add Day", command=self.add_day)

        # Set days (sheets)

        # Add days (sheets): when the user clicks this button, a new label will appaer with an entry box, one for each property: key, sheet name, day string, sheet id

        # Save button
        self.button = ttk.Button(self, text="Save", command=self.save)
        self.button.pack()

    def save(self):
        self.config['file_id'] = self.file_id_entry.get()
        self.master.save_config(self.config)
        self.withdraw()

    def create_day_widgets(self, parent, day):
        day_config = self.config.get("days", []).get(day, {})
        day_frame = ttk.LabelFrame(parent, text=day)
        day_frame.pack(fill='y', expand=True)
        day_sheet_id_label = ttk.Label(day_frame, text="Sheet ID:")
        day_sheet_id_label.pack()
        day_sheet_id_entry = ttk.Entry(day_frame, width=60)
        day_sheet_id_entry.insert(0, (day_config['sheet_id'], ''))
        day_sheet_id_entry.pack()
        # self.new_day_button.pack()
        # self_new_day_key_label = ttk.Label(self.google_frame, text="Key:")
        # self_new_day_key_label.pack()
        # self.new_day_key = ttk.Entry(self.google_frame, width=20)
        # self.new_day_key.pack()
        # self.new_day_sheet_name_label = ttk.Label(self.google_frame, text="Sheet Name:")
        # self.new_day_sheet_name_label.pack()
        # self.new_day_sheet_name = ttk.Entry(self.google_frame, width=20)
        # self.new_day_sheet_name.pack()
        # self.new_day_day_string_label = ttk.Label(self.google_frame, text="Day String:")
        # self.new_day_day_string_label.pack()
        # self.new_day_day_string = ttk.Entry(self.google_frame, width=20)
        # self.new_day_day_string.pack()
        # self.new_day_sheet_id_label = ttk.Label(self.google_frame, text="Sheet ID:")
        # self.new_day_sheet_id_label.pack()
        # self.new_day_sheet_id = ttk.Entry(self.google_frame, width=20)
        # self.new_day_sheet_id.pack()
        # self.new_day_save_button = ttk.Button(self.google_frame, text="Save", command=self.save_new_day)
        # self.new_day_save_button.pack()
