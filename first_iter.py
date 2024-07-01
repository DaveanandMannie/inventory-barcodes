import pymupdf
from pymupdf import Document, Page
import pandas as pd
from pandas import DataFrame
from barcode import Code128
from barcode.writer import ImageWriter
import io
from io import BytesIO
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
        text = (
            f'{label_data['product']}\nUnknown box Qty: {label_data['in_qty']}\n{label_data['in_ref']}\nLet Dave know\n'
        )
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


def parse_odoo_pdf(receiving_pdf: str) -> list[list]:
    """

    :param:
        receiving_doc: Path to Odoo's picking operations
    :return list :
        list of list
        - Product : str
        - Incoming Quantity: str
        - Barcode : str | int | None
        - Expected Box Quantity: int | None
    """
    doc: Document = pymupdf.open(receiving_pdf)
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


def left_join(cleaned_data: list, product_var_export: str, output_file_path: str, receiving_pdf: str) -> str:
    """

    :param list cleaned_data: list of list parsed from a Picking Operations PDF
    :param str product_var_export: Path to Odoo's product variant export using Display Name and Barcode
    :param str output_file_path: Path to a folder to keep history of the left joins
    :param str receiving_pdf: Path or name of the Picking Operations PDF
    :return str: the cleaned file name. reference number in Odoo
    """
    in_ref: str = receiving_pdf.split('-')[-1].rstrip('.pdf').strip()
    filename: str = f'{output_file_path}/{in_ref}.csv'
    cleaned_df: DataFrame = pd.DataFrame(cleaned_data[1:], columns=cleaned_data[0])
    product_list: DataFrame = pd.read_csv(product_var_export)
    product_list = product_list.rename(columns={product_list.columns[0]: 'Product'})
    joined: DataFrame = pd.merge(cleaned_df, product_list, on='Product', how='left')
    joined.to_csv(filename, index=False)
    return filename


def generate_label_data(line_data: list, receiving_pdf: str) -> dict:
    """

    :param list line_data: [
        Product: str
        Incoming Quantity: str
        Barcode: int | str | None
        Expected Box Quantity: int | None
        ]
    :param  str receiving_pdf: Path or name of the Picking Operations PDF
    :return dict:
        - 'product' str : Display name in Odoo
        - 'partial' bool : If the full box cannot divide evenly with the in_qty
        - 'barcode' str : Content to make the Code128 barcode
        - 'in_qty' int : amount outlined in Picking Operation
        - 'box_qty' int | None : Number of units a full box
        - 'num_boxes' int |None :
        - 'has_barcode' bool : If Odoo has a barcode for the item
        - 'known_box_qty' Bool: If a box qty exists
        - 'in_ref' str: reference for Odoo Picking Operation
    """
    # this feels like a refactor. Sorry future me :(
    inventory_reference: str = receiving_pdf.split('-')[-1].rstrip('.pdf').strip()
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


def generate_label(hotfolder: str, label_data: dict):
    """

    :param str hotfolder: path to the hotfolder
    :param  dict label_data: Created by generate_label_data(*)
        - 'product' str : Display name in Odoo
        - 'partial' bool : If the full box cannot divide evenly with the in_qty
        - 'barcode' str : Content to make the Code128 barcode
        - 'in_qty' int : amount outlined in Picking Operation
        - 'box_qty' int | None : Number of units a full box
        - 'num_boxes' int |None :
        - 'has_barcode' bool : If Odoo has a barcode for the item
        - 'known_box_qty' Bool: If a box qty exists
        - 'in_ref' str: reference for Odoo Picking Operation
    :return:
    """
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
            label.save(f'{hotfolder}/{filename}{i + 1}a.pdf')
    else:
        label.save(f'{hotfolder}/{filename}-1.pdf')
    label.close()
    # TODO: force gc here ?
    return
