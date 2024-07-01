import first_iter
import functools
import csv
import tracemalloc

odoo_pdf: str = 'Picking Operations - S&S Canada - WH_IN_00129.pdf'
product_csv: str = '../documents/product_code_case.csv'
csv_output: str = './csv_history'
label_output: str = './hotfolder'


def mem_perf(test_func):
    @functools.wraps(test_func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        result = test_func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(
            f'Memory usage (Mb)\n===============\nCurrent:\n    {current / 10 ** 6}\nPeak:\n    {peak / 10 ** 6}'
        )
        return result

    return wrapper


@mem_perf
def generic_test(receiving_file: str, product_var_csv: str, label_output_dir: str, csv_output_dir: str):
    data: list = first_iter.parse_odoo_pdf(receiving_file)
    receiving_data: str = first_iter.left_join(data, product_var_csv, csv_output_dir, receiving_file)
    with open(receiving_data) as file:
        reader: csv.reader = csv.reader(file)
        next(reader)  # skipping headers
        for line in reader:
            label_data: dict = first_iter.generate_label_data(line, receiving_file)
            first_iter.generate_label(label_output_dir, label_data)
    return


generic_test(odoo_pdf, product_csv, label_output, csv_output)
