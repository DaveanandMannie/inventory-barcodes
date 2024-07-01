import pymupdf
from pymupdf import Document, Page
import pandas as pd
from pandas import DataFrame
from barcode import Code128
from barcode.writer import ImageWriter
import io
from io import BytesIO
import csv
from typing import Optional


# this assumes the given pdf is generated from picking operations on odoo 16
# TODO: create ops;  partial disk writes, full memory buffers; current partial
def parse_odoo_pdf(receiving_doc: str) -> list[list]:
    doc: Document = pymupdf.open(receiving_doc)
    num_of_pages: int = doc.__len__()
    table_list: list = []
    for number in range(num_of_pages):
        page = doc[number]
        table_data_obj = page.find_tables(strategy='lines_strict')
        table_data = table_data_obj[0].extract()
        table_list.extend(table_data)
    cleaned_data: list = [table_list[0][:-2]]
    for sublist in table_list[1:]:
        if 'Product' in sublist:
            continue
        cleaned_data.extend([sublist[:-2]])
    return cleaned_data


def left_join(cleaned_data: list, product_export: str, output_file_path: str):
    cleaned_df: DataFrame = pd.DataFrame(cleaned_data[1:], columns=cleaned_data[0])
    product_list: DataFrame = pd.read_csv(product_export)
    product_list = product_list.rename(columns={product_list.columns[0]: 'Product'})
    joined: DataFrame = pd.merge(cleaned_df, product_list, on='Product', how='left')
    joined.to_csv(output_file_path, index=False)
    return


def generate_label_data(line_data: list) -> dict:
    # label data csv headers: Product:str ,Quantity str, Barcode str or int ,box: int
    # TODO: include the operation id
    # TODO: do exists checks
    # this feels like a refactor. Sorry future me :(
    in_qty: int = int(float(line_data[1].split()[0]))
    if line_data[3] == '':
        box_qty: Optional[int] = None
        known_box_qty: bool = False
    else:
        box_qty: Optional[int] = int(float(line_data[3]))
        known_box_qty: bool = True
    if known_box_qty:
        partial: bool = in_qty % box_qty != 0
    else:
        partial: bool = False
    num_boxes: int = 1
    if line_data[2] == '':
        code: str = '1234'
        has_barcode: bool = False
    else:
        code: str = str(line_data[2])
        has_barcode: bool = True
    if not partial:
        num_boxes: int = in_qty // box_qty
    label_data: dict = {
        'product': line_data[0],
        'partial': partial,
        'barcode': code,
        'in_qty': in_qty,
        'box_qty': box_qty,
        'num_boxes': num_boxes,
        'has_barcode': has_barcode,
        'known_box_qty': known_box_qty
    }
    return label_data


def generate_label(output_dir: str, label_data: dict):
    # label data keys: product, partial, barcode, in_qty, box_qty, num boxes
    # TODO: use config file for options: create func(environ? ) -> dict
    if label_data['partial']:
        text = f'''{label_data['product']}\nPartial: {label_data['in_qty']}\nWH/IN00123\n'''
    else:
        text = f'''{label_data['product']}\n{label_data['box_qty']} Units\nWH/out00123\n'''
    writer_options: dict = {
        'margin_bottom': 1,
        'margin_top': 1,
        'quiet_zone': 5,
        'module_width': 0.4,
        'module_height': 10.0,
        'font_size': 5,
        'text_distance': 2,
    }
    barcode_obj: Code128 = Code128(label_data['barcode'], writer=ImageWriter())
    barcode_svg_buffer: BytesIO = io.BytesIO()
    barcode_obj.write(barcode_svg_buffer, options=writer_options)
    barcode_svg_buffer.seek(0)

    # TODO: func this out
    another_pdf: Document = pymupdf.open()
    another_pdf.insert_page(pno=-1, width=432, height=288)
    page: Page = another_pdf[0]

    rect_width = page.rect.width * 0.5
    rect_height = page.rect.height * 0.5

    page_width = page.rect.width
    x_left = (page_width - rect_width) / 2
    y_center = 0.7
    rect = pymupdf.Rect(x_left, y_center, x_left + rect_width, y_center + rect_height)
    # TODO: func this out
    text_rect = pymupdf.Rect(0, 144, 432, 288)

    page.insert_textbox(text_rect, text, fontsize=18, align=pymupdf.TEXT_ALIGN_CENTER)

    page.insert_image(rect, stream=barcode_svg_buffer)
    page.set_rotation(90)

    for i in range(0, label_data['num_boxes']):
        another_pdf.save(f'{output_dir}/{label_data['product']}-{i + 1}.pdf')
    another_pdf.close()
    barcode_svg_buffer.close()
    # TODO: force gc here ?
    return


# TODO: create logic to handle products without code128; log file -> set to keep track

# quick and dirty test suite
receiving_file: str = 'documents/example.pdf'
product_csv: str = './documents/product_code_case.csv'
output_csv: str = 'temp_test.csv'
output_label_pdf: str = './test'
data = parse_odoo_pdf(receiving_file)
left_join(data, product_csv, output_csv)

# label data csv headers: Product,Quantity,Barcode,Case
# test_line: list = ["Womens-Triblend-Tee(XL, White-Fleck-Triblend)", '24.00 Units', 884913238824, 72.0]
# test_line: list = ["BC_6400_Womens-Relaxed-Tee_RM (S, White)",'96.00 Units', 884913108509, 48.0]
# generate_label(output_dir=output_label_pdf, label_data=generate_label_data(test_line))
with open('temp_test.csv') as file:
    reader = csv.reader(file)
    next(reader)  # skipping headers
    next(reader)  # skipping headers
    next(reader)  # skipping headers
    next(reader)  # skipping headers
    next(reader)  # skipping headers
    next(reader)  # skipping headers
    next(reader)  # skipping headers
    next(reader)  # skipping headers
    next(reader)  # skipping headers
    next(reader)  # skipping headers
    for line in reader:
        generate_label(output_label_pdf, generate_label_data(line))
