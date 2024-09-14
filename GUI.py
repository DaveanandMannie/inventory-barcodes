# WARN: threading is implicit. I want to rewrite with explicit multithreading
import os
from datetime import datetime
from typing import Any, Callable, cast

from CTkMessagebox import CTkMessagebox
from customtkinter import (
    BooleanVar,
    CTk,
    CTkButton,
    CTkCheckBox,
    CTkEntry,
    CTkFrame,
    CTkInputDialog,
    CTkLabel,
    CTkProgressBar,
    CTkScrollableFrame,
    IntVar,
    StringVar,
    filedialog,
)
from dotenv import load_dotenv

from odoogen import (
    LabelData,
    ReceiptData,
    generate_all_label_data,
    generate_label,
    get_receipt_products,
    left_join,
)

_ = load_dotenv()

config: dict[str, str] = {
    'csv_history_dir': cast(str, os.getenv('CSV_HISTORY_DIR')),
    'hotfolder_dir': cast(str, os.getenv('HOTFOLDER_DIR')),
    'default_pdf_dir': cast(str, os.getenv('DEFAULT_PDF_DIR')),
    'product_var_csv': cast(str, os.getenv('PRODUCT_VAR_CSV')),
    'email': cast(str, os.getenv('EMAIL')),
    'pass': cast(str, os.getenv('PASSWORD'))
}

TITLE_FONT: tuple[str, int, str] = ('Arial', 19, 'bold')
FONT: tuple[str, int] = ('Arial', 14)


class NoLinkError(Exception):
    pass


class LinkError(Exception):
    pass


class LinkFrame(CTkFrame):
    """Top Frame where the link is inputed"""
    def __init__(self, master: 'App'):
        super().__init__(master)
        self._set_appearance_mode('dark')
        _ = self.grid_columnconfigure(index=1, weight=2)

        self.default_link: str = 'No link set'
        self.receipt_link = StringVar(value=self.default_link)

        self.select_callbacks: list[Callable[[str], None]] = []
        self.reset_callbacks: list[Callable[[], None]] = []

        self.link_label = CTkLabel(
            self,
            text='Picking Operations Ref:',
            font=TITLE_FONT
        )
        self.link_label.grid(row=0, column=0, sticky='nsew', padx=20)

        self.selected_link_label = CTkLabel(
            self,
            textvariable=self.master.odoo_ref,  # pyright: ignore [reportAttributeAccessIssue, reportUnknownArgumentType] # noqa
            wraplength=350,
            font=TITLE_FONT
        )
        self.selected_link_label.grid(row=0, column=1, sticky='nsew', padx=20)

        self.reset_button: CTkButton = CTkButton(
            self,
            text='Reset',
            fg_color='red',
            hover_color='darkred',
            command=self._execute_reset_callbacks,
            font=FONT
        )
        self.reset_button.grid(row=0, column=2)

        self.set_link_button: CTkButton = CTkButton(
            self,
            text='Set Receipt link',
            command=self._set_receipt_link,
            font=FONT
        )
        self.set_link_button.grid(
            row=0, column=3, padx=20, pady=20, ipadx=5, ipady=5, sticky='e'
        )

    # HACK: avoiding threading for next refact/rewrite
    def _prog(self):
        """Change some global labels for user feedback"""
        self.master.odoo_ref.set('Working please wait...')  # pyright: ignore [reportAttributeAccessIssue]  # noqa: E501
        self.master.progress_label_text.set('Grabbing reciept info...')  # pyright: ignore [reportAttributeAccessIssue]  # noqa: E501

    def _clean_link(self, link: str | None) -> str:
        prefix: str = 'https://'
        odoo: str = 'odoo.printgeek.ca'
        if link is None or not link:
            raise NoLinkError
        elif odoo not in link:
            raise LinkError
        elif not link.startswith(prefix):
            c_link = prefix + link
        else:
            c_link = link
        return c_link

    def _help_get(self):
        """Func to get link and execute  callbacks"""
        dialog: CTkInputDialog = CTkInputDialog(
            text='Paste receipt link:',
            title='Receipt Link',
            button_hover_color='green'
        )
        link: str | None = dialog.get_input()
        try:
            c_link: str = self._clean_link(link)
            self.receipt_link.set(c_link)
            self._execute_select_callbacks(c_link)
            self.master.progress_bar.set(1)  # pyright: ignore [reportAttributeAccessIssue]  # noqa: E501
        except NoLinkError:
            self._no_link()
            self._execute_reset_callbacks()
        except LinkError:
            self._err_link()
            self._execute_reset_callbacks()

    def _set_receipt_link(self):
        """Sets receipt link based on user input"""
        self._prog()
        _ = self.after(200, self._help_get)

    @staticmethod
    def _no_link():
        """No link pop up"""
        _ = CTkMessagebox(
            title='No link provided',
            message='No link provider',
            justify='center',
            icon='cancel',
            font=FONT
        )

    @staticmethod
    def _err_link():
        """Invalid link pop up"""
        _ = CTkMessagebox(
            title='Invalid link',
            message='Invalid link please provide a proper odoo receipt link',
            justify='center',
            icon='cancel',
            font=FONT
        )

    def reg_select_callback(self, callback: Callable[[str], None]):
        """Register callback to be executed when a link is provided"""
        self.select_callbacks.append(callback)

    def reg_reset_callback(self, callback: Callable[[], None]):
        """Register callback to be executed reset is clicked"""
        self.reset_callbacks.append(callback)

    def _execute_select_callbacks(self, link: str):
        """Execute all registered select callbacks"""
        for callback in self.select_callbacks:
            callback(link)

    def _execute_reset_callbacks(self):
        """Reverts to initial state an executes reset callbacks"""
        self.receipt_link.set(self.default_link)
        for callback in self.reset_callbacks:
            callback()


class SingleLabelFrame(CTkFrame):
    """
    Contains individual label data that will populate the
    scrollable frame
    """
    def __init__(self, master: 'AllLabelFrame', label_data: LabelData):
        super().__init__(master, width=500, height=100)
        self._set_appearance_mode('dark')

        self.label_data: LabelData = label_data
        self.product = StringVar(value=label_data['product'].replace(' ', '\n', 1).replace('_RM', ''))  # noqa: E501
        self.single_gen_button = CTkButton(
            self,
            text='Print',
            command=self._print_single_label,
            font=FONT
        )

        self.in_qty = StringVar(value=str(label_data['in_qty']))
        self.partial = BooleanVar(value=label_data['partial'])
        self.box_qty = IntVar(value=label_data['box_qty'])

        self.partial = CTkCheckBox(
            self,
            text='Label as Partial',
            variable=self.partial,
            command=self._change_partial
        )

        self.product_label = CTkLabel(
            self,
            textvariable=self.product,
            width=225,
            font=FONT
        )
        self.box_qty_label = CTkLabel(self, text='Box Quantity:', font=FONT)
        self.box_qty_entry = CTkEntry(
            self,
            textvariable=self.box_qty,
            width=60,
            justify='center',
            font=FONT
        )
        self.box_qty_label.bind('<Return>', self._change_box_qty)
        self.in_qty_label = CTkLabel(self, textvariable=self.in_qty, font=FONT)

        self.product_label.grid(
            row=0, column=0, padx=(10, 20), pady=20, sticky='w'
        )
        self.box_qty_label.grid(row=0, column=1, pady=20)
        self.box_qty_entry.grid(row=0, column=2, padx=(5, 10), pady=20)
        self.partial.grid(row=0, column=3, padx=10, pady=20)
        self.in_qty_label.grid(row=0, column=4, padx=10, pady=20)
        self.single_gen_button.grid(
            row=0, column=5, padx=10, pady=20, sticky='e'
        )
        _ = self.columnconfigure(index=0, weight=1)

    def _print_single_label(self):
        """Generates a single label"""
        generate_label(
            hotfolder=config['hotfolder_dir'],
            label_data=self.label_data
        )
        _ = CTkMessagebox(
                title='Task Finished',
                message='Task Finished',
                icon='check',
                justify='center'
            )

    def _change_box_qty(self, event: Any):  # noqa: ANN401, E501  # pyright: ignore [reportAny]
        """Changes the box quantity based on user entry"""
        _ = event  # pyright: ignore [reportAny]
        try:
            new_qty = int(self.box_qty_entry.get())
            self.box_qty.set(new_qty)
            self.label_data['box_qty'] = new_qty
            _ = CTkMessagebox(
                    title='Box Quantity Updated',
                    message=f'Box Quantity updated to: {new_qty}',
                    icon='check',
                    justify='center'
                )
        except ValueError:
            _ = CTkMessagebox(
                    title='Error',
                    message='Incorrect Value',
                    icon='cancel',
                    justify='center'
                )

    def _change_partial(self):
        """Changes the partial status based on checkbox"""
        if self.partial.get() == 0:
            self.label_data['partial'] = False
        else:
            self.label_data['partial'] = True


class AllLabelFrame(CTkScrollableFrame):
    """A scrollable frame that has each product in th receipt"""
    def __init__(self, master: 'App', **kwargs):  # pyright: ignore [reportUnknownParameterType, reportMissingParameterType] # noqa
        super().__init__(master, **kwargs)  # pyright: ignore [reportUnknownArgumentType]  # noqa E501
        self._set_appearance_mode('dark')
        _ = self.columnconfigure(index=0, weight=1)
        _ = self.columnconfigure(index=1, weight=0)
        self.frames: list[SingleLabelFrame] = []

        self.Title_label = CTkLabel(
            self, text='Print Individual Labels', font=TITLE_FONT
        )
        self.pseudo_hr = CTkFrame(self, height=4, fg_color='white')
        self.Title_label.grid(
            row=0, column=0, padx=(20, 10), pady=5, sticky='ew'
        )
        self.pseudo_hr.grid(row=1, columnspan=2, sticky='ew')

    def generate_frames(self, all_label_data: list[LabelData]):
        """
        Deletes old frames if any enerate single frames for each line item in
        receipt
        """
        if len(self.frames) > 0:
            for frame in self.frames:
                frame.destroy()
            self.frames.clear()

        frame_num: int = 2

        for label_dict in all_label_data:
            frame = SingleLabelFrame(self, label_dict)
            frame.grid(row=frame_num)
            self.frames.append(frame)
            frame_num += 1

    def delete_frames(self):
        """Delates all old frames"""
        for frame in self.frames:
            frame.destroy()
        self.frames.clear()


class OperationFrame(CTkFrame):
    """
    The frame wher it shows all the working dirs and has the configurable .env
    """
    def __init__(self, master: 'App'):
        super().__init__(master)
        self._set_appearance_mode('dark')
        self.hotfolder_label = CTkLabel(
            self, text='Current Hotfolder:', font=FONT
        )
        self.hotfolder_label.grid(row=0, column=0, padx=20, pady=10)
        self.effective_hotfolder_label = CTkLabel(
            self, textvariable=master.hotfolder_dir, wraplength=200, font=FONT
        )
        self.effective_hotfolder_label.grid(row=0, column=1, padx=20, pady=10)
        self.gen_button_callbacks: list[Callable[[], None]] = []

        self.odoo_ref_label = CTkLabel(self, text='Odoo Reference:', font=FONT)
        self.odoo_ref_label.grid(row=1, column=0, padx=20, pady=10)
        self.effective_hotfolder_label = CTkLabel(
            self, textvariable=master.odoo_ref, wraplength=200, font=FONT
        )
        self.effective_hotfolder_label.grid(row=1, column=1, padx=20, pady=10)

        self.generate_button = CTkButton(
            self, text='Generate Labels',
            fg_color='grey',
            hover=False,
            command=self._execute_gen_button_callbacks,
            font=FONT
        )
        self.generate_button.grid(
            row=2, columnspan=2, padx=20, pady=20, ipadx=20, ipady=20,
            sticky='ew'
        )

        # TODO: create a config pop up with a password
        self.config_button = CTkButton(
            self, text='Edit Config', command=self._not_implemented, font=FONT
        )
        self.config_button.grid(
            row=3, column=0, columnspan=2, padx=20, pady=20, ipadx=5, ipady=5,
            sticky='ew'
        )

        self.csv_dir_label = CTkLabel(self, text='CSV History:', font=FONT)
        self.csv_dir_label.grid(row=4, column=0, padx=20, pady=10)
        self.effective_csv_dir = CTkLabel(
            self, textvariable=master.joined_csv_dir, wraplength=200, font=FONT
        )
        self.effective_csv_dir.grid(
            row=4, column=1, padx=20, pady=20, ipadx=5, ipady=5, sticky='e'
        )

    @staticmethod
    def _not_implemented():
        """Not implemented pop up"""
        _ = CTkMessagebox(
            title='Not implemented yet',
            message='Not implemented yet',
            justify='center',
            icon='warning',
            font=FONT
        )

    def reg_gen_button_callback(self, callback: Callable[[], None]):
        """Register callbacks when for the generate button"""
        self.gen_button_callbacks.append(callback)

    def _execute_gen_button_callbacks(self):
        """Executes all registered callbacks for the generate button"""
        for callback in self.gen_button_callbacks:
            callback()

    def active_gen_button(self, *args):  # pyright: ignore [reportUnknownParameterType, reportMissingParameterType] # noqa
        """Visual feed back for when the generate button is clickable"""
        _ = args  # pyright: ignore [reportUnknownVariableType]
        self.generate_button.configure(
            fg_color='green', hover=True, hover_color='darkgreen'
        )

    def default_gen_button(self, *args):  # pyright: ignore [reportUnknownParameterType, reportMissingParameterType] # noqa
        """Visual configurations when the generate button is not clickable"""
        _ = args  # pyright: ignore [reportUnknownVariableType]
        self.generate_button.configure(fg_color='grey', hover=False)


class App(CTk):
    """Main app window"""
    def __init__(self, config: dict[str, str]):
        super().__init__()
        self.iconbitmap('resources/icon.ico')
        self._set_appearance_mode('dark')
        self.title('Receiving Barcode Generator')
        self.geometry("1366x768")
        self.resizable(False, False)
        self.config: dict[str, str] = config
        self.label_data: list[LabelData] = []
        self.hotfolder_dir = StringVar(value=self.config['hotfolder_dir'])
        self.joined_csv_dir = StringVar(value=self.config['csv_history_dir'])
        self.product_var_csv = StringVar(value=self.config['product_var_csv'])
        self.odoo_ref: StringVar = StringVar(value='No link set')

        _ = self.grid_columnconfigure(index=0, weight=1)
        _ = self.grid_columnconfigure(index=1, weight=1)
        _ = self.grid_columnconfigure(index=2, weight=1)
        _ = self.grid_columnconfigure(index=3, weight=0)
        _ = self.grid_rowconfigure(index=2, weight=1)

        self.LinkFrame = LinkFrame(self)
        self.LinkFrame.grid(
            row=0, column=0, padx=20, pady=20, sticky="ew", columnspan=4
        )

        self.Individual_Label_Frame = AllLabelFrame(self)
        self.Individual_Label_Frame.grid(
            row=1, column=0, columnspan=3, padx=(20, 10), pady=(0, 20),
            rowspan=3, sticky='nsew'
        )

        self.OperationFrame = OperationFrame(self)
        self.OperationFrame.grid(row=1, column=3, padx=(10, 20), sticky='e')

        # call back registry
        # ----------- when a file is selected -----------#
        self.LinkFrame.reg_select_callback(self.OperationFrame.active_gen_button)  # pyright: ignore [reportUnknownArgumentType]  # noqa: E501
        self.LinkFrame.reg_select_callback(self.store_label_data)
        self.LinkFrame.reg_select_callback(self.generate_frames)

        # ----------- when the reset button is pressed -----------#
        self.LinkFrame.reg_reset_callback(self.OperationFrame.default_gen_button)  # pyright: ignore [reportUnknownArgumentType]  # noqa: E501
        self.LinkFrame.reg_reset_callback(self.reset_odoo_ref)
        self.LinkFrame.reg_reset_callback(self.delete_frames)
        self.LinkFrame.reg_reset_callback(self.reset_progress)

        # ----------- when the generate button is pressed -----------#
        self.OperationFrame.reg_gen_button_callback(self.generate_all_labels)

        # --------------Progress bar----------------- #
        self.progress_bar = CTkProgressBar(
            self, width=300, height=15, progress_color='darkgreen'
        )
        self.progress_bar.grid(
            row=2, column=3, columnspan=4, padx=20, pady=(90, 10), sticky='n'
        )
        self.progress_bar.set(0)
        self.progress_label_text = StringVar(value='No task')
        self.progress_label = CTkLabel(
            self, textvariable=self.progress_label_text, font=TITLE_FONT
        )
        self.progress_label.grid(row=2, column=3, padx=20, sticky='ew')

    def generate_frames(self, link: str):
        """Generates the frames for receipt line items"""
        _ = link
        self.Individual_Label_Frame.generate_frames(self.label_data)

    def delete_frames(self):
        """Deletes all active frames"""
        self.Individual_Label_Frame.delete_frames()

    def _select_hotfolder(self):
        """Chosing the hotfolder"""
        hotfolder_dir: str = filedialog.askdirectory(
            initialdir=self.hotfolder_dir.get()
        )
        if hotfolder_dir:
            self.hotfolder_dir.set(hotfolder_dir)

    def store_label_data(self, link: str):
        """Makes receipt data available to the entire app"""
        data: ReceiptData = get_receipt_products(
            url=link,
            email=self.config['email'],
            password=self.config['pass']
        )

        joined_csv: str = left_join(
            receipt_data=data,
            var_export=self.product_var_csv.get(),
            output_dir=self.joined_csv_dir.get()
        )
        self.label_data = generate_all_label_data(joined_csv)
        self.odoo_ref.set(cast(str, data['reference']))

    def reset_odoo_ref(self):
        """Resets the odoo reference string globally"""
        self.odoo_ref.set('No link set')

    def _update_progress(self, progress: float):
        """Updates the float value for the progress bar"""
        self.progress_bar.set(progress)

    def reset_progress(self):
        """Returns progress bar to none/empty state"""
        self.progress_label_text.set('No task')
        self.progress_bar.set(0)

    def generate_all_labels(self):
        """Generates all labels for a the selected Receipt"""
        self.progress_label_text.set('Working')
        total_labels: int = len(self.label_data)
        label_iter = iter(self.label_data)
        process_count: int = 1

        # HACK:  I did this this way to avoiding having to use threading
        def _process():
            try:
                nonlocal process_count
                label_dict: LabelData = next(label_iter)
                generate_label(
                    hotfolder=self.hotfolder_dir.get(),
                    label_data=label_dict
                )
                process_count += 1
                self._update_progress(process_count / (total_labels + 1))
                _ = self.after(100, _process)  # Delay is for aesthetics
            except StopIteration:
                self.progress_label_text.set('Finished')
                _ = CTkMessagebox(
                        title='Task Finished',
                        message='Task Finished',
                        icon='check',
                        justify='center'
                    )
                date: str = datetime.now().strftime('%d-%m-%Y %H:%M')
                print(f'Finished: {self.label_data[0]['in_ref']} -> {date}')
        _process()


if __name__ == "__main__":
    app = App(config)
    app.mainloop()
