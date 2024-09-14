import csv
import os
from io import BytesIO
from typing import TypedDict, cast

import pandas as pd
import pymupdf
from barcode import Code128
from barcode.writer import ImageWriter
from pandas import DataFrame
from pymupdf import Document, Page, Rect
from selenium.webdriver.chrome.webdriver import WebDriver

from scraper import scraper

# ============ Type defs ============ #
type ProductData = list[list[str]]
type ReceiptData = dict[str, str | ProductData]


class LabelData(TypedDict):
    product: str
    partial: bool
    barcode: str
    in_qty: int
    box_qty: int
    num_boxes: int
    has_barcode: bool
    known_box_qty: bool
    in_ref: str
# ============ Type defs end ============ #


def _sanitize_filename(filename: str) -> str:
    """Removes invalid characters based on Windows file criterion"""
    invalid_chars = '\\/:*?"<>|'
    for char in invalid_chars:
        filename = filename.replace(char, '-')
    return filename


def _generate_text(label_data: LabelData) -> str:
    """Generates the text below the scannable barcode"""
    text: str
    product: str = label_data['product']
    in_qty: int = label_data['in_qty']
    ref: str = label_data['in_ref']
    box_qty: int = label_data['box_qty']

    if label_data['partial']:
        text = f'{product}\nPartial: {in_qty} Units\n{ref}\n'
    elif not label_data['known_box_qty']:
        text = f'{product}\nUnknown box qty{in_qty}\n{ref}\nlet Dave know\n'
    else:
        text = f'{product}\n{box_qty} Units\n{ref}\n'
    return text


def _place_barcode(page: Page, barcode: str, opts: dict[str, float]):
    """
    Places the scannable barcode img into the center of the page
    """
    barcode_obj: Code128 = Code128(barcode, writer=ImageWriter())
    barcode_svg_buff: BytesIO = BytesIO()
    barcode_obj.write(barcode_svg_buff, options=opts)
    _ = barcode_svg_buff.seek(0)

    # basedpyright cant go this deep I guess.
    img_rect_width = page.rect.width * 0.5  # pyright: ignore[reportAny]
    img_rect_height = page.rect.height * 0.5  # pyright: ignore[reportAny]
    page_width = page.rect.width  # pyright: ignore[reportAny]
    x_left = (page_width - img_rect_width) / 2  # pyright: ignore[reportAny]
    y_center = 0.7

    rect = Rect(
        x_left, y_center, x_left + img_rect_width, y_center + img_rect_height    # pyright: ignore[reportAny]  # noqa: E501
    )
    page.insert_image(rect, stream=barcode_svg_buff)  # pyright: ignore [reportAttributeAccessIssue]  # noqa: E501
    barcode_svg_buff.close()


def get_receipt_products(url: str, email: str, password: str) -> ReceiptData:
    """
    Replaces func parse_odoo_pdf
    Takes Receipt url and login credentials
    returns a dict with receipt reference and receipt data
    :return dict:
    """
    driver: WebDriver = scraper.driver_setup(email=email, password=password)
    product_data: ProductData = scraper.get_label_data(link=url, driver=driver)
    reference: str = scraper.get_reference(driver)
    receipt_data: ReceiptData = {
        'reference': reference,
        'product_data': product_data
    }
    driver.quit()
    return receipt_data


def left_join(receipt_data: ReceiptData,
              var_export: str,
              output_dir: str
              ) -> str:
    """
    Parameters:
        receipt_data: Receipt data dict
        var_export: export from odoo containg proudct, barcodes,
                    and known case number
        output_dir: output dir
    """
    ref = cast(str, receipt_data['reference'])
    file: str = f'{ref}.csv'
    filename: str = os.path.join(output_dir, file)
    product_data = cast(ProductData, receipt_data['product_data'])
    product_df = DataFrame(product_data[1:], columns=product_data[0])  # pyright: ignore[reportArgumentType]  # noqa: E501

    var_list: DataFrame = pd.read_csv(var_export)
    var_list = var_list.rename(columns={var_list.columns[0]: 'Product'})  # pyright: ignore[reportUnhashable]  # noqa: E501

    join: DataFrame = pd.merge(product_df, var_list, on='Product', how='left')
    join.to_csv(filename, index=False)
    return filename


def generate_label_data(line_data: list[str], reference: str) -> LabelData:
    """
    Creates the dict that the barcode lib will use to create the barcode and
    the contains the data needed for the GUI
    """
    ref: str = reference.split('\\')[-1].split('.')[0]  # FIXME: ugly oneliner
    barcode: str = line_data[2]
    in_qty: int = int(float(line_data[1]))
    box_qty: int = 0
    known_box_qty: bool = False
    num_boxes: int = 0
    partial: bool = True

    if line_data[3]:
        box_qty = int(float(line_data[3]))
        known_box_qty = True

    if known_box_qty:
        partial = (in_qty % box_qty != 0)

    if box_qty > 0:
        num_boxes = in_qty // box_qty

    label_data: LabelData = {
        'product': line_data[0],
        'partial': partial,
        'barcode': barcode,
        'in_qty': in_qty,
        'box_qty': box_qty,
        'num_boxes': num_boxes,
        'has_barcode': bool(barcode),
        'known_box_qty': known_box_qty,
        'in_ref': ref
    }
    return label_data


def generate_all_label_data(joined_fp: str) -> list[LabelData]:
    """
    Reads the csv created by the left jion func and retuns a list
    of dicts containing all data need to create the label pdf
    """
    ref: str = joined_fp.split('/')[-1].replace('-', '/')
    data: list[LabelData] = []
    with open(joined_fp) as csv_file:
        reader = csv.reader(csv_file)
        _ = next(reader)
        for line in reader:
            data.append(generate_label_data(line_data=line, reference=ref))
    return data


def generate_label(hotfolder: str, label_data: LabelData):
    """
    Creates labels based on  LabelData dict
    :param:
        Hotfolder: Destination for the file
        label_data: data from generate_label data func
    """
    text: str = _generate_text(label_data)
    writer_options: dict[str, float] = {
        'margin_bottom': 1,
        'margin_top': 1,
        'quiet_zone': 0,
        'module_width': 0.4,
        'module_height': 10.0,
        'font_size': 5,
        'text_distance': 2
    }
    label: Document = pymupdf.open()
    # TODO: try to replace with '.new_page(*kwargs)'
    label.insert_page(pno=-1, width=432, height=288)  # pyright: ignore [reportAttributeAccessIssue]  # noqa: E501
    page: Page = label[0]

    if label_data['has_barcode']:
        _place_barcode(
            page=page, barcode=label_data['barcode'], opts=writer_options
        )

    text_rect = Rect(0, 100, 432, 288)
    page.insert_textbox(  # pyright: ignore [reportAttributeAccessIssue]
        text_rect, text, fontsize=20, align=pymupdf.TEXT_ALIGN_CENTER
    )

    page.set_rotation(90)

    filename: str = _sanitize_filename(label_data['product'])
    target: str = os.path.join(hotfolder, filename)

    if not label_data['partial'] and label_data['num_boxes'] != 0:
        for i in range(label_data['num_boxes']):
            label.save(f'{target}-{i + 1}.pdf')
    else:
        label.save(f'{target}-1.pdf')

    label.close()
