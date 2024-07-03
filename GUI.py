import customtkinter
from customtkinter import CTkButton, filedialog, CTkLabel, StringVar


# TODO: Create a global font object
class PDFFrame(customtkinter.CTkFrame):
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

        self.select_pdf_button = CTkButton(
            self, text='Select Odoo PDF', command=self.select_receiving_pdf
        )
        self.select_pdf_button.grid(row=0, column=3, padx=50, pady=20, ipadx=5, ipady=5, sticky='e')

    def select_receiving_pdf(self):
        file_path: str = filedialog.askopenfilename()
        if file_path:
            self.selected_file.set(file_path)
        return

    def reset_pdf(self):
        self.selected_file.set(self.default_pdf)


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title('Receiving Barcode Generator')
        self.geometry("1080x720")
        self.PDFFrame = PDFFrame(self)
        self.PDFFrame.grid(row=0, column=0, padx=20, pady=20, sticky="ew", columnspan=2)
        self.grid_columnconfigure(index=1, weight=1)
        self._set_appearance_mode('dark')


app = App()
app.mainloop()
