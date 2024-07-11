from customtkinter import (
    CTkButton, filedialog, CTkLabel, StringVar, CTkFrame, CTk, CTkScrollableFrame, CTkCheckBox, CTkEntry, IntVar,
    BooleanVar, CTkProgressBar
)
from CTkMessagebox import CTkMessagebox
from odoogen import parse_odoo_pdf, left_join, generate_label, generate_all_label_data
import json
from typing import Callable

with open('./documents/test_config.json') as file:
    config: dict = json.load(file)


# TODO: doc strings ? probably for future me
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

    def _execute_reset_callbacks(self):
        self.selected_file.set(self.default_pdf)
        for callback in self.reset_callbacks:
            callback()
        return


class SingleLabelFrame(CTkFrame):
    def __init__(self, master, label_dict: dict):
        super().__init__(master, width=500, height=100)
        self.label_data = label_dict
        self.product_name = StringVar(value=label_dict['product'].replace(' ', '\n', 1).replace('_RM', ''))
        self.single_gen_button = CTkButton(self, text='Print', command=self._print_single_label)
        self.in_qty = StringVar(value=label_dict['in_qty'])
        self.partial = BooleanVar(value=label_dict['partial'])

        if label_dict['box_qty']:
            self.box_qty = IntVar(value=label_dict['box_qty'])
        else:
            self.box_qty = IntVar(value=0)

        self.partial = CTkCheckBox(self, text='Label as Partial', variable=self.partial, command=self._change_partial)

        self.product_name_label = CTkLabel(self, textvariable=self.product_name, width=225)
        self.box_qty_label = CTkLabel(self, text='Box Quantity:')
        self.box_qty_entry = CTkEntry(self, textvariable=self.box_qty, width=60, justify='center')
        self.box_qty_entry.bind('<Return>', self._change_box_qty)
        self.in_qty_label = CTkLabel(self, textvariable=self.in_qty)

        self.product_name_label.grid(row=0, column=0, padx=(10, 20), pady=20, sticky='w')
        self.box_qty_label.grid(row=0, column=1, pady=20)
        self.box_qty_entry.grid(row=0, column=2, padx=(5, 10), pady=20)
        self.partial.grid(row=0, column=3, padx=10, pady=20)
        self.in_qty_label.grid(row=0, column=4, padx=10, pady=20)
        self.single_gen_button.grid(row=0, column=5, padx=10, pady=20, sticky='e')
        self.columnconfigure(index=0, weight=1)

    def _print_single_label(self):
        generate_label(label_data=self.label_data, hotfolder=config['hotfolder_dir'])
        return


    def _change_box_qty(self, event):
        _ = event
        try:
            new_qty = int(self.box_qty_entry.get())
            self.box_qty.set(new_qty)
            self.label_data['box_qty'] = new_qty
            CTkMessagebox(title='Box Quanitty Updated', message=f'Box Quanitity updated to: {new_qty}', icon='check', justify='center')
        except ValueError:
            CTkMessagebox(title='Error', message='Incorrect Value', icon='cancel', justify='center')

    def _change_partial(self):
        if self.partial.get() == 0:
            self.label_data['partial'] = False
        else:
            self.label_data['partial'] = True
        return


class AllLabelFrame(CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(index=0, weight=1)
        self.columnconfigure(index=1, weight=0)
        self.frames: list = []

        self.Title_label = CTkLabel(self, text='Print Individual Labels', font=('consolas', 19, 'bold'))
        self.pseudo_hr = CTkFrame(self, height=4, fg_color='white')

        self.Title_label.grid(row=0, column=0, padx=(20, 10), pady=5, sticky='ew')
        self.pseudo_hr.grid(row=1, columnspan=2, sticky='ew')

    def generate_frames(self, label_data: list):
        if len(self.frames) > 0:
            for frame in self.frames:
                frame.destroy()
            self.frames.clear()
        frame_num: int = 2
        for label_dict in label_data:
            frame = SingleLabelFrame(self, label_dict)
            frame.grid(row=frame_num)
            self.frames.append(frame)
            frame_num += 1

    def delete_frames(self):
        for frame in self.frames:
            frame.destroy()
        self.frames.clear()


class OperationFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.hotfolder_label = CTkLabel(self, text='Current Hotfolder:')
        self.hotfolder_label.grid(row=0, column=0, padx=20, pady=10)
        self.effective_hotfolder_label = CTkLabel(self, textvariable=master.hotfolder_dir, wraplength=200)
        self.effective_hotfolder_label.grid(row=0, column=1, padx=20, pady=10)
        self.gen_button_callbacks: list = []

        self.odoo_ref_label = CTkLabel(self, text='Odoo Reference:')
        self.odoo_ref_label.grid(row=1, column=0, padx=20, pady=10)
        self.effective_hotfolder_label = CTkLabel(self, textvariable=master.odoo_ref, wraplength=200)
        self.effective_hotfolder_label.grid(row=1, column=1, padx=20, pady=10)

        self.generate_button = CTkButton(
            self, text='Generate Labels', fg_color='grey', hover=False, command=self._execute_gen_button_callbacks
        )
        self.generate_button.grid(row=2, columnspan=2, padx=20, pady=20, ipadx=20, ipady=20, sticky='ew')

        # TODO: create a config pop up with a password
        self.config_button = CTkButton(self, text='Edit Config', command=self._not_implemented)
        self.config_button.grid(row=3, column=0, columnspan=2, padx=20, pady=20, ipadx=5, ipady=5, sticky='ew')
        # TODO: decide what to show in the config tile subspace

        self.csv_dir_label = CTkLabel(self, text='CSV History:')
        self.csv_dir_label.grid(row=4, column=0, padx=20, pady=10)
        self.effective_csv_dir = CTkLabel(self, textvariable=master.joined_csv_dir, wraplength=200)
        self.effective_csv_dir.grid(row=4, column=1, padx=20, pady=20, ipadx=5, ipady=5, sticky='e')

    @staticmethod
    def _not_implemented():
        CTkMessagebox(title='Not implemented yet', message='Not implemented yet', justify='center', icon='warning')
        return

    def register_gen_button_callback(self, callback: Callable):
        """Register call back to be executed when a file is selected"""
        self.gen_button_callbacks.append(callback)
        return

    def _execute_gen_button_callbacks(self):
        for callback in self.gen_button_callbacks:
            callback()
        return

    def active_gen_button(self, *args):
        _ = args
        self.generate_button.configure(fg_color='green', hover=True, hover_color='darkgreen')
        return

    def default_gen_button(self, *args):
        _ = args
        self.generate_button.configure(fg_color='grey', hover=False)
        return


class App(CTk):
    def __init__(self, config_file: dict):
        super().__init__()
        self._set_appearance_mode('dark')
        self.title('Receiving Barcode Generator')
        self.geometry("1366x768")
        self.resizable(False, False)
        self.config: dict = config_file
        self.label_data: list = []
        self.hotfolder_dir: StringVar = StringVar(value=self.config['hotfolder_dir'])
        self.default_pdf_dir: StringVar = StringVar(value=self.config['default_pdf_dir'])
        self.joined_csv_dir: StringVar = StringVar(value=self.config['csv_history_dir'])
        self.product_var_csv: StringVar = StringVar(value=self.config['product_var_csv'])
        self.odoo_ref: StringVar = StringVar(value='No file selected')

        self.grid_columnconfigure(index=0, weight=1)
        self.grid_columnconfigure(index=1, weight=1)
        self.grid_columnconfigure(index=2, weight=1)
        self.grid_columnconfigure(index=3, weight=0)
        self.grid_rowconfigure(index=2, weight=1)

        self.PDFFrame = PDFFrame(self)
        self.PDFFrame.grid(row=0, column=0, padx=20, pady=20, sticky="ew", columnspan=4)
        self.Individual_Label_Frame = AllLabelFrame(self)

        self.Individual_Label_Frame.grid(row=1, column=0, columnspan=3, padx=(20, 10), pady=(0, 20), rowspan=3,
                                         sticky='nsew')

        self.OperationFrame = OperationFrame(self)
        self.OperationFrame.grid(row=1, column=3, padx=(10, 20), sticky='e')

        # call back registry
        # ----------- when a file is selected -----------#
        self.PDFFrame.register_select_callback(self.OperationFrame.active_gen_button)
        self.PDFFrame.register_select_callback(self.store_label_data)
        self.PDFFrame.register_select_callback(self.generate_frames)

        # ----------- when the reset button is pressed -----------#
        self.PDFFrame.register_reset_callback(self.OperationFrame.default_gen_button)
        self.PDFFrame.register_reset_callback(self.reset_odoo_ref)
        self.PDFFrame.register_reset_callback(self.delete_frames)
        self.PDFFrame.register_reset_callback(self.rest_progress)

        # ----------- when the generate button is pressed -----------#
        self.OperationFrame.register_gen_button_callback(self.generate_all_labels)

        # --------------Progress bar----------------- #
        self.progress_bar = CTkProgressBar(self, width=300, height=15, progress_color='darkgreen')
        self.progress_bar.grid(row=2, column=3, columnspan=4, padx=20, pady=(90, 10), sticky='n')
        self.progress_bar.set(0)
        self.progress_label_text = StringVar(value='No task')
        self.progress_label = CTkLabel(self, textvariable=self.progress_label_text, font=('consolas', 19, 'bold'))
        self.progress_label.grid(row=2, column=3, padx=20, sticky='ew')

    def generate_frames(self, filepath):
        _ = filepath
        self.Individual_Label_Frame.generate_frames(self.label_data)
        return

    def delete_frames(self):
        self.Individual_Label_Frame.delete_frames()
        return

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

    def _update_progress(self, progress):
        self.progress_bar.set(progress)
        return

    def rest_progress(self):
        self.progress_label_text.set('No task')
        self.progress_bar.set(0)
        return

    def generate_all_labels(self):
        self.progress_label_text.set('Working')
        total_labels: int = len(self.label_data)
        label_iter = iter(self.label_data)
        process_count: int = 1

        def _process():
            try:
                nonlocal process_count  # I watch one functional video XD
                label_dict = next(label_iter)
                generate_label(hotfolder=self.hotfolder_dir.get(), label_data=label_dict)
                process_count += 1
                self._update_progress(process_count / (total_labels + 1))
                self.after(100, _process)  # The delay is for aesthetics
            except StopIteration:
                self.progress_label_text.set('Finished')
                CTkMessagebox(title='Task Finished', message='Task Finished', icon='check', justify='center')
        _process()
        return


if __name__ == "__main__":
    app = App(config)
    app.mainloop()
