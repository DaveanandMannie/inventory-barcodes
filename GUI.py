from customtkinter import CTkButton, filedialog, CTkLabel, StringVar, CTkFrame, CTk
from odoogen import *
from e2e_test import print_memory_usage
# TODO: Create a global font object
class PDFFrame(CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(index=1, weight=2)
        self.default_pdf: str = 'No file selected'
        self.selected_file = StringVar(value=self.default_pdf)

        self.file_frame_label = CTkLabel(self, text='"Picking Operations" PDF:', font=('consolas', 19, 'bold'))
        self.file_frame_label.grid(row=0, column=0, sticky='nsew', padx=20)

        self.selected_pdf_label = CTkLabel(self, textvariable=self.selected_file, wraplength=350)
        self.selected_pdf_label.grid(row=0, column=1, sticky='nsew', padx=20)

        self.reset_button = CTkButton(self, text='Reset', fg_color='red', command=self.reset_pdf)
        self.reset_button.grid(row=0, column=2)

        self.select_pdf_button = CTkButton(self, text='Select Odoo PDF', command=self._select_receiving_pdf)
        self.select_pdf_button.grid(row=0, column=3, padx=20, pady=20, ipadx=5, ipady=5, sticky='e')

    def _select_receiving_pdf(self):
        file_path: str = filedialog.askopenfilename()
        if file_path:
            self.selected_file.set(file_path)
        return

    def reset_pdf(self):
        self.selected_file.set(self.default_pdf)


class Frame(CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.hotfolder_label = CTkLabel(self, text='Current Hotfolder:')
        self.hotfolder_label.grid(row=0, column=0, padx=20, pady=10)
        self.effective_hotfolder_label = CTkLabel(self, textvariable=master.hotfolder_path, wraplength=200)
        self.effective_hotfolder_label.grid(row=0, column=1, padx=20, pady=10)

        self.odoo_ref_label = CTkLabel(self, text='Odoo Reference:')
        self.odoo_ref_label.grid(row=1, column=0, padx=20, pady=10)
        self.effective_hotfolder_label = CTkLabel(self, textvariable=master.odoo_ref, wraplength=200)
        self.effective_hotfolder_label.grid(row=1, column=1, padx=20, pady=10)


# TODO: create a config pop up with a password
@print_memory_usage
class App(CTk):
    def __init__(self):
        super().__init__()
        self._set_appearance_mode('dark')
        self.title('Receiving Barcode Generator')
        self.geometry("1080x720")

        self.grid_columnconfigure(index=0, weight=1)
        self.grid_columnconfigure(index=1, weight=1)
        self.grid_columnconfigure(index=2, weight=1)

        self.PDFFrame = PDFFrame(self)
        self.PDFFrame.grid(row=0, column=0, padx=20, pady=20, sticky="ew", columnspan=3)



        self.generate_button = CTkButton(self, text='Generate Labels')
        self.generate_button.grid(row=1, column=1)



        # TODO: get from config file? json? yaml? txt? fully 256bit encrypted tarball? Jia Tan will get my pay :(
        self.hotfolder_path: StringVar = StringVar(value='E:/PrintGeek/inventory-barcodes/test_targets/hotfolder')
        self._default_pdf_dir: StringVar = StringVar()

        # TODO: get from odoo-gen
        self.odoo_ref: StringVar = StringVar(value='WH/IN/00014')

        self.test_frame = Frame(self)
        self.test_frame.grid(row=1, column=2, padx=20, sticky='e')

    def _select_hotfolder(self):
        hotfolder_path: str = filedialog.askdirectory(initialdir=self.hotfolder_path.get())
        if hotfolder_path:
            self.hotfolder_path.set(hotfolder_path)
        return


app = App()
app.mainloop()