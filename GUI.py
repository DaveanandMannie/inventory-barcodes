import customtkinter
from tkinter import filedialog


def _select_receiving_pdf():
    file_path: str = filedialog.askopenfilename()
    if file_path:
        print(file_path)
    else:
        print('not working')


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title('Receiving Barcode Generator')
        self.geometry("1080x720")
        self.button = customtkinter.CTkButton(self, text="file?", command=_select_receiving_pdf)
        self.button.grid(row=0, column=0)


app = App()
app.mainloop()
