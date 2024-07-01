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
#   logging
#   proper flow of temp files and i/o dirs
def _sanitize_filename(filename: str) -> str:
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, '-')
    return filename


def _generate_text(label_data: dict) -> str:
    text: str
    if label_data['partial']:
        text = f'{label_data['product']}\nPartial: {label_data['in_qty']} Units\n{label_data['in_ref']}\n'
    elif not label_data['known_box_qty']:
        text = f'{label_data['product']}\nUnknown box Qty: {label_data['in_qty']}\nWH/IN00123\nLet Dave know\n'
    else:
        text = f'{label_data['product']}\n{label_data['box_qty']} Units\n{label_data['in_ref']}\n'

    if not label_data['has_barcode']:
        text += 'Need to create a barcode; Manual transfer and let Dave know'
    text = text.replace('(', '\n(')
    return text


def _place_barcode(page_in_pdf: Page, barcode_str: str, options: dict):
    barcode_obj: Code128 = Code128(barcode_str, writer=ImageWriter())
    barcode_svg_buffer: BytesIO = io.BytesIO()
    barcode_obj.write(barcode_svg_buffer, options=options)
    barcode_svg_buffer.seek(0)

    img_rect_width = page_in_pdf.rect.width * 0.5
    img_rect_height = page_in_pdf.rect.height * 0.5
    page_width = page_in_pdf.rect.width
    x_left = (page_width - img_rect_width) / 2
    y_center = 0.7
    rect = pymupdf.Rect(x_left, y_center, x_left + img_rect_width, y_center + img_rect_height)
    page_in_pdf.insert_image(rect, stream=barcode_svg_buffer)
    barcode_svg_buffer.close()
    return


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


def generate_label_data(line_data: list, receiving_doc: str) -> dict:
    # label data csv headers: Product:str ,Quantity str, Barcode str or int ,box: int
    # TODO: include the operation id
    # this feels like a refactor. Sorry future me :(
    inventory_reference: str = receiving_doc.split('-')[-1].rstrip('.pdf').strip()
    in_qty: int = int(float(line_data[1].split()[0]))
    num_boxes: Optional[int]
    box_qty: Optional[int]
    known_box_qty: bool
    partial: bool
    code: Optional[str]
    has_barcode: bool
    # TODO: remove redundancy if any
    if line_data[3] == '':
        box_qty = None
        known_box_qty = False
    else:
        box_qty = int(float(line_data[3]))
        known_box_qty = True

    if line_data[2] == '':
        code = None
        has_barcode = False
    else:
        code = str(line_data[2])
        has_barcode = True

    if known_box_qty:
        partial = in_qty % box_qty != 0
    else:
        partial = True

    if box_qty is not None:
        num_boxes = in_qty // box_qty
    else:
        num_boxes = None

    label_data: dict = {
        'product': line_data[0],
        'partial': partial,
        'barcode': code,
        'in_qty': in_qty,
        'box_qty': box_qty,
        'num_boxes': num_boxes,
        'has_barcode': has_barcode,
        'known_box_qty': known_box_qty,
        'in_ref': inventory_reference
    }
    return label_data


def generate_label(output_dir: str, label_data: dict):
    # label data keys: product, partial, barcode, in_qty, box_qty, num boxes
    # TODO: use config file for options: create func(environ? ) -> dict
    text: str = _generate_text(label_data)
    writer_options: dict = {
        'margin_bottom': 1,
        'margin_top': 1,
        'quiet_zone': 0,
        'module_width': 0.4,
        'module_height': 10.0,
        'font_size': 5,
        'text_distance': 2,
    }
    label: Document = pymupdf.open()
    label.insert_page(pno=-1, width=432, height=288)
    page: Page = label[0]

    if label_data['has_barcode']:
        _place_barcode(page_in_pdf=page, barcode_str=label_data['barcode'], options=writer_options)

    text_rect = pymupdf.Rect(0, 100, 432, 288)
    page.insert_textbox(text_rect, text, fontsize=20, align=pymupdf.TEXT_ALIGN_CENTER)

    page.set_rotation(90)
    filename: str = _sanitize_filename(label_data['product'])

    if label_data['num_boxes'] is not None and not label_data['partial']:
        for i in range(0, label_data['num_boxes']):
            label.save(f'{output_dir}/{filename}{i + 1}a.pdf')
    else:
        label.save(f'{output_dir}/{filename}-1.pdf')
    label.close()
    # TODO: force gc here ?
    return


# quick and dirty test suite
# receiving_file: str = 'documents/example.pdf'
receiving_file: str = 'documents/Picking Operations - S&S Canada - WH_IN_00129.pdf'
product_csv: str = './documents/product_code_case.csv'
output_csv: str = './test/temp_test.csv'
output_label_pdf: str = './test'
data = parse_odoo_pdf(receiving_file)
left_join(data, product_csv, output_csv)
# label data csv headers: Product,Quantity,Barcode,Case
test = 'Picking Operations - S&S Canada - WH_IN_00129.pdf'
# test_line: list = ["BC_8413_Womens-Triblend-Tee_RM (2XL, Charcoal-Black-Triblend)", '144.00 Units', 884913238824, 72.0]
# test_line: list = ["BC_6400_Womens-Relaxed-Tee_RM (S, White)",'96.00 Units', 884913108509, 48.0]
# test_line: list = ["BC_3200_Baseball-Tee-3/4_RM (M, White/True-Royal)", '8.00 Units', '', '']
# generate_label(output_dir=output_label_pdf, label_data=generate_label_data(test_line, test))
with open(output_csv) as file:
    reader = csv.reader(file)
    next(reader)  # skipping headers
    for line in reader:
        generate_label(output_label_pdf, generate_label_data(line, test))
