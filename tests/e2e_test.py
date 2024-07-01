import first_iter
import csv

odoo_pdf: str = 'Picking Operations - S&S Canada - WH_IN_00129.pdf'
product_csv: str = '../documents/product_code_case.csv'
csv_output: str = './csv_history'
label_output: str = './hotfolder'


def generic_test(receiving_file: str, product_csv: str, label_output_dir: str, csv_output_dir: str):
    data: list = first_iter.parse_odoo_pdf(receiving_file)
    receiving_data: str = first_iter.left_join(data, product_csv, csv_output_dir, receiving_file)
    with open(receiving_data) as file:
        reader: csv.reader = csv.reader(file)
        next(reader)  # skipping headers
        for line in reader:
            label_data: dict = first_iter.generate_label_data(line, receiving_file)
            first_iter.generate_label(label_output_dir, label_data)
    return


generic_test(odoo_pdf, product_csv, label_output, csv_output)
