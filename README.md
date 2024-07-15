# Receiving Barcode Generator
A small app that creates barcode labels for each box on a given PO
[main_app.png](readme_resources%2Fmain_app.png)
Simple logging
## Table of Contents
- [Usage](#usage)
- [Installation](#installation)
## Usage
To use simply download the ```Picking Operations from A PO ``` and click ```Generate``` it will send all labels
associated with the PO to our hotfolder to print the labels
[demo.mp4](readme_resources%2FGIFbase.mp4)

On the left of the application, you can reprint individual labels and correct any mistakes, either from on the PO side
or on my end. It is pre-populated with label data.

## Installation
### From the Source
1. ```git clone https://github.com/DaveanandMannie/inventory-barcodes.git```
2. Install dependencies with ```pip install -r requirements.txt```
3. Run the build script with your target path ```python build.py <target path>```
    1. Note On windows there might be an issue if there are spaces in the path. If encountered wrap path with ```""```
4. Edit ```.env``` with the defaults; ```HOTFOLDER_DIR```, and ```DEFAULT_PDF_DIR```. Downlaods
5. Optionally You could create a shortcut of ```Receiving_Barcode_Generator.exe``` to place on your desktop
### From the Release
1. Download and extract the ```.zip```
2. Edit ```.env``` with the defaults; ```HOTFOLDER_DIR```, and ```DEFAULT_PDF_DIR```. Downlaods
3. Optionally You could create a shortcut of ```Receiving_Barcode_Generator.exe``` to place on your desktop
[demo.mp4](readme_resources%2FGIFbase.mp4)