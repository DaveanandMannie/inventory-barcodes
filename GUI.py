import csv
from customtkinter import CTkButton, filedialog, CTkLabel, StringVar, CTkFrame, CTk
from odoogen import *
from e2e_test import print_memory_usage
import json
from typing import Callable

with open('./documents/test_config.json') as file:
    config: dict = json.load(file)


# TODO: Create a global font object
class PDFFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(index=1, weight=2)
        self.default_pdf: str = 'No file selected'
        self.selected_file = StringVar(value=self.default_pdf)
        self.callbacks: list = []  # depending on how I control data flow I might back this a static function

        self.file_frame_label = CTkLabel(self, text='"Picking Operations" PDF:', font=('consolas', 19, 'bold'))
        self.file_frame_label.grid(row=0, column=0, sticky='nsew', padx=20)

        self.selected_pdf_label = CTkLabel(self, textvariable=self.selected_file, wraplength=350)
        self.selected_pdf_label.grid(row=0, column=1, sticky='nsew', padx=20)

        self.reset_button = CTkButton(self, text='Reset', fg_color='red', command=self.reset_pdf)
        self.reset_button.grid(row=0, column=2)

        self.select_pdf_button = CTkButton(self, text='Select Odoo PDF', command=self._select_receiving_pdf)
        self.select_pdf_button.grid(row=0, column=3, padx=20, pady=20, ipadx=5, ipady=5, sticky='e')

    def _select_receiving_pdf(self):
        file_path: str = filedialog.askopenfilename(initialdir=self.master.default_pdf_dir.get())
        if file_path:
            self.selected_file.set(file_path)
            self._execute_callbacks(file_path)
        return

    def register_callback(self, callback: Callable):
        """Register call back to be executed when a file is selected"""
        self.callbacks.append(callback)
        return

    def _execute_callbacks(self, file_path: str):
        """Execute all registered call backs"""
        for callback in self.callbacks:
            callback(file_path)
        return

    # TODO: Callback? :(
    def reset_pdf(self):
        self.selected_file.set(self.default_pdf)
        self.master.odoo_ref.set(self.default_pdf)
        return


# TODO: create a config pop up with a password
class ConfigFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.hotfolder_label = CTkLabel(self, text='Current Hotfolder:')
        self.hotfolder_label.grid(row=0, column=0, padx=20, pady=10)
        self.effective_hotfolder_label = CTkLabel(self, textvariable=master.hotfolder_dir, wraplength=200)
        self.effective_hotfolder_label.grid(row=0, column=1, padx=20, pady=10)

        self.odoo_ref_label = CTkLabel(self, text='Odoo Reference:')
        self.odoo_ref_label.grid(row=1, column=0, padx=20, pady=10)
        self.effective_hotfolder_label = CTkLabel(self, textvariable=master.odoo_ref, wraplength=200)
        self.effective_hotfolder_label.grid(row=1, column=1, padx=20, pady=10)
        # TODO: commands -> odoo-gen
        self.generate_button = CTkButton(self, text='Generate Labels', fg_color='grey', hover_color='green')
        self.generate_button.grid(row=2, columnspan=2, padx=20, pady=20, ipadx=20, ipady=20, sticky='ew')

        self.config_button = CTkButton(self, text='Edit Config')
        self.config_button.grid(row=3, column=0, padx=20, pady=20, ipadx=5, ipady=5, sticky='w')
        # TODO: decide what to show in the config tile subspace

        self.csv_dir_label = CTkLabel(self, text='CSV History:')
        self.csv_dir_label.grid(row=4, column=0, padx=20, pady=10)
        self.effective_csv_dir = CTkLabel(self, textvariable=master.joined_csv_dir, wraplength=200)
        self.effective_csv_dir.grid(row=4, column=1, padx=20, pady=20, ipadx=5, ipady=5, sticky='e')


@print_memory_usage
class App(CTk):
    def __init__(self, config_file: dict):
        super().__init__()
        self._set_appearance_mode('dark')
        self.title('Receiving Barcode Generator')
        self.geometry("1080x720")
        self.config: dict = config_file
        self.label_data: list[dict] = []

        self.grid_columnconfigure(index=0, weight=1)
        self.grid_columnconfigure(index=1, weight=1)
        self.grid_columnconfigure(index=2, weight=1)

        self.PDFFrame = PDFFrame(self)
        self.PDFFrame.grid(row=0, column=0, padx=20, pady=20, sticky="ew", columnspan=3)
        self.PDFFrame.register_callback(self.store_label_data)

        self.hotfolder_dir: StringVar = StringVar(value=self.config['hotfolder_dir'])
        self.default_pdf_dir: StringVar = StringVar(value=self.config['default_pdf_dir'])
        self.joined_csv_dir: StringVar = StringVar(value=self.config['csv_history_dir'])
        self.product_var_csv: StringVar = StringVar(value=self.config['product_var_csv'])

        # TODO: get from odoo-gen
        self.odoo_ref: StringVar = StringVar(value='No file selected')

        self.config_frame = ConfigFrame(self)
        self.config_frame.grid(row=1, column=2, padx=20, sticky='e')

    def _select_hotfolder(self):
        hotfolder_dir: str = filedialog.askdirectory(initialdir=self.hotfolder_dir.get())
        if hotfolder_dir:
            self.hotfolder_dir.set(hotfolder_dir)
        return

    def store_label_data(self, file_path):
        data: list = parse_odoo_pdf(file_path)

        receiving_data: str = left_join(
            cleaned_data=data,
            product_var_export=self.product_var_csv.get(),
            output_file_path=self.joined_csv_dir.get(),
            receiving_pdf=file_path
        )
        # TODO  decide weather to add this functionality to odoo-gen -> probably
        with open(receiving_data) as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            for line in reader:
                label_dict: dict = generate_label_data(line, file_path)
                self.label_data.append(label_dict)
            self.odoo_ref.set(self.label_data[0]['in_ref'])
        return


if __name__ == "__main__":
    app = App(config)
    app.mainloop()