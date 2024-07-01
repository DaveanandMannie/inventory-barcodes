from first_iter import parse_odoo_pdf, left_join, generate_label, generate_label_data
import functools
import csv
import tracemalloc

odoo_pdf: str = 'test_targets/Picking Operations - S&S Canada - WH_IN_00129.pdf'
product_csv: str = 'documents/product_code_case.csv'
csv_output: str = 'test_targets/csv_history'
label_output: str = 'test_targets/hotfolder'


def print_memory_usage(test_func):
    @functools.wraps(test_func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        result = test_func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        std_out: str = (
            f'Memory Usage : {str(test_func)}\n'
            f'=====================================================================\n'
            f'Current:\n    {current / 10 ** 6}MB\n'
            f'Peak:\n    {peak / 10 ** 6}MB'
        )
        print(std_out)
        return result

    return wrapper


@print_memory_usage
def full_test(receiving_file: str, product_var_csv: str, label_output_dir: str, csv_output_dir: str):
    data: list = parse_odoo_pdf(receiving_file)
    receiving_data: str = left_join(data, product_var_csv, csv_output_dir, receiving_file)
    with open(receiving_data) as file:
        reader: csv.reader = csv.reader(file)
        next(reader)  # skipping headers
        for line in reader:
            label_data: dict = generate_label_data(line, receiving_file)
            generate_label(label_output_dir, label_data)
    return


@print_memory_usage
def store_label_data(receiving_file:str):
    pass


full_test(odoo_pdf, product_csv, label_output, csv_output)
