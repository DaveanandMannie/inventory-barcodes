import pymupdf
from pymupdf import Document
import pandas as pd
from pandas import DataFrame
from barcode import Code128
import io
from io import BytesIO


# this assumes the given pdf is generated from picking operations on odoo 16
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


def generate_label(output_dir: str, label_data: list, index: int):
    # label data csv headers: Product,Quantity,Barcode,Case
    # TODO: use config file for options
    code: str = label_data[2]
    writer_options: dict = {
        'margin_bottom': 45,
        'margin_top': 25,
        'quiet_zone': 50,
        'module_width': 0.7,
        'module_height': 15.0,
        'font_size': 25,
        'text_distance': 10,
        'human': ''
    }
    barcode_obj: Code128 = Code128(code)
    barcode_svg_buffer: BytesIO = io.BytesIO()
    barcode_svg_buffer.write(barcode_obj.render(writer_options))
    barcode_svg_buffer.seek(0)

    svg_buffer_data: Document = pymupdf.open(stream=barcode_svg_buffer.read())
    converted_svg: bytes = svg_buffer_data.convert_to_pdf()
    label: Document = pymupdf.open("pdf", converted_svg)
    label[0].set_rotation(90)
    label.save(f'{output_dir}/{index}')
    label.close()
    barcode_svg_buffer.close()
    # TODO: force gc here ?
    return



receiving_file = './documents/whin.pdf'
product_csv = './documents/product_code_case.csv'
output_csv = 'temp_test.csv'
output_label_pdf = 'label_output.pdf'
sample_code = '9254567890'

data = parse_odoo_pdf(receiving_file)
left_join(data, product_csv, output_csv)
generate_label(sample_code, output_label_pdf)
