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
        self.select_callbacks: list = []
        self.reset_callbacks: list = []

        self.file_frame_label = CTkLabel(self, text='"Picking Operations" PDF:', font=('consolas', 19, 'bold'))
        self.file_frame_label.grid(row=0, column=0, sticky='nsew', padx=20)

        self.selected_pdf_label = CTkLabel(self, textvariable=self.selected_file, wraplength=350)
        self.selected_pdf_label.grid(row=0, column=1, sticky='nsew', padx=20)

        self.reset_button = CTkButton(
            self, text='Reset', fg_color='red', hover_color='darkred', command=self._execute_reset_callbacks
        )
        self.reset_button.grid(row=0, column=2)

        self.select_pdf_button = CTkButton(self, text='Select Odoo PDF', command=self._select_receiving_pdf)
        self.select_pdf_button.grid(row=0, column=3, padx=20, pady=20, ipadx=5, ipady=5, sticky='e')

    def _select_receiving_pdf(self):
        file_path: str = filedialog.askopenfilename(initialdir=self.master.default_pdf_dir.get())
        if file_path:
            self.selected_file.set(file_path)
            self._execute_select_callbacks(file_path)
        return

    def register_select_callback(self, callback: Callable):
        """Register call back to be executed when a file is selected"""
        self.select_callbacks.append(callback)
        return

    def register_reset_callback(self, callback: Callable):
        self.reset_callbacks.append(callback)
        return

    def _execute_select_callbacks(self, file_path: str):
        """Execute all registered select call backs"""
        for callback in self.select_callbacks:
            callback(file_path)
        return

    # TODO: Callback? :(
    def _execute_reset_callbacks(self):
        self.selected_file.set(self.default_pdf)
        for callback in self.reset_callbacks:
            callback()
        return


# TODO: create a config pop up with a password
class OperationFrame(CTkFrame):
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
        self.generate_button = CTkButton(self, text='Generate Labels', fg_color='grey', hover=False)
        self.generate_button.grid(row=2, columnspan=2, padx=20, pady=20, ipadx=20, ipady=20, sticky='ew')

        self.config_button = CTkButton(self, text='Edit Config')
        self.config_button.grid(row=3, column=0, padx=20, pady=20, ipadx=5, ipady=5, sticky='w')
        # TODO: decide what to show in the config tile subspace

        self.csv_dir_label = CTkLabel(self, text='CSV History:')
        self.csv_dir_label.grid(row=4, column=0, padx=20, pady=10)
        self.effective_csv_dir = CTkLabel(self, textvariable=master.joined_csv_dir, wraplength=200)
        self.effective_csv_dir.grid(row=4, column=1, padx=20, pady=20, ipadx=5, ipady=5, sticky='e')

    def active_gen_button(self, *args):
        _ = args
        self.generate_button.configure(fg_color='green', hover=True, hover_color='darkgreen')
        return

    def default_gen_button(self, *args):
        _ = args
        self.generate_button.configure(fg_color='grey', hover=False)
        return


@print_memory_usage
class App(CTk):
    def __init__(self, config_file: dict):
        super().__init__()
        self._set_appearance_mode('dark')
        self.title('Receiving Barcode Generator')
        self.geometry("1080x720")
        self.config: dict = config_file
        self.label_data: list[dict] = []
        self.hotfolder_dir: StringVar = StringVar(value=self.config['hotfolder_dir'])
        self.default_pdf_dir: StringVar = StringVar(value=self.config['default_pdf_dir'])
        self.joined_csv_dir: StringVar = StringVar(value=self.config['csv_history_dir'])
        self.product_var_csv: StringVar = StringVar(value=self.config['product_var_csv'])
        self.odoo_ref: StringVar = StringVar(value='No file selected')

        self.grid_columnconfigure(index=0, weight=1)
        self.grid_columnconfigure(index=1, weight=1)
        self.grid_columnconfigure(index=2, weight=1)

        self.PDFFrame = PDFFrame(self)
        self.PDFFrame.grid(row=0, column=0, padx=20, pady=20, sticky="ew", columnspan=3)
        self.PDFFrame.register_select_callback(self.store_label_data)
        self.PDFFrame.register_reset_callback(self.reset_odoo_ref)

        self.config_frame = OperationFrame(self)
        self.config_frame.grid(row=1, column=2, padx=20, sticky='e')

        self.PDFFrame.register_select_callback(self.config_frame.active_gen_button)
        self.PDFFrame.register_reset_callback(self.config_frame.default_gen_button)

    def _select_hotfolder(self):
        hotfolder_dir: str = filedialog.askdirectory(initialdir=self.hotfolder_dir.get())
        if hotfolder_dir:
            self.hotfolder_dir.set(hotfolder_dir)
        return

    def store_label_data(self, file_path):
        data: list = parse_odoo_pdf(file_path)

        joined_csv: str = left_join(
            cleaned_data=data,
            product_var_export=self.product_var_csv.get(),
            output_file_path=self.joined_csv_dir.get(),
            receiving_pdf=file_path
        )
        self.label_data = generate_all_label_data(joined_csv, file_path)
        self.odoo_ref.set(self.label_data[0]['in_ref'])
        return

    def reset_odoo_ref(self):
        self.odoo_ref.set('No file selected')
        return

if __name__ == "__main__":
    app = App(config)
    app.mainloop()
