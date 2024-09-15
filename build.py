# pyright: reportAny=false
import argparse
import os
import shutil

import PyInstaller.__main__


def build(target_dir: str):
    # make this from cli args? maybe
    app_name: str = 'Receiving_Barcode_Generator'
    PyInstaller.__main__.run([
        f'--name={app_name}',
        '--onedir',
        '--windowed',
        '--add-data=./resources;resources',
        '--add-data=./documents/product_code_case.csv;./',
        '--add-data=./logs;logs',
        '--add-data=./.env;.',
        '--add-data=./.venv/Lib/site-packages/customtkinter;customtkinter',
        '--add-data=./.venv/Lib/site-packages;site-packages',
        '--add-data=./.venv/Lib/site-packages/PyMuPDF;PyMuPDF/',
        '--add-data=./.venv/Lib/site-packages/selenium;selenium/',
        '--add-data=./.venv/Lib/site-packages/barcode;barcode/',  # this is where the font lives  # noqa: E501
        '--icon=./resources/icon.ico',
        f'--distpath={target_dir}',
        '-y',
        '--clean',
        'GUI.py',
    ])

    build_dir: str = f'{target_dir}/{app_name}'
    os.makedirs(build_dir, exist_ok=True)

    source_logs_dir = os.path.join(build_dir, '_internal', 'logs')
    shutil.move(source_logs_dir, build_dir)

    source_resources_dir = os.path.join(build_dir, '_internal', 'resources')
    shutil.move(source_resources_dir, build_dir)

    source_product_csv = os.path.join(
        build_dir, '_internal', 'product_code_case.csv'
    )
    shutil.move(source_product_csv, build_dir)

    source_env = os.path.join(build_dir, '_internal', '.env')
    shutil.move(source_env, build_dir)
    os.makedirs(f'{build_dir}/history', exist_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Build the Receiving Barcode Generator'
    )
    _ = parser.add_argument(
        'build_dir', help='Target directory for building the application'
    )
    args = parser.parse_args()
    build(args.build_dir)
