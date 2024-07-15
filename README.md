# Receiving Barcode Generator
A small app that creates barcode labels for each box on a given PO

## Usage
To use simply download the ```Picking Operations from A PO ``` and click ```Generate``` it will send all labels
associated with the PO to our hotfolder to print the labels

On the left of the application, you can reprint individual labels and correct any mistakes, either from on the PO side
or on my end. It is pre-populated with label data.
The label output is 4x6

![demo](https://github.com/DaveanandMannie/inventory-barcodes/blob/master/readme_resources/demo.gif)
![output](https://github.com/DaveanandMannie/inventory-barcodes/blob/master/readme_resources/output.png)

## Installation
### From the Source
1. ```git clone https://github.com/DaveanandMannie/inventory-barcodes.git```
2. Install dependencies with ```pip install -r requirements.txt```
3. Run the build script with your target path ```python build.py <target path>```
    1. Note On Windows there might be an issue if there are spaces in the path. If encountered wrap path with ```""```
4. Edit ```.env``` with the defaults; ```HOTFOLDER_DIR```, and ```DEFAULT_PDF_DIR```. Downloads
5. Optionally You could create a shortcut of ```Receiving_Barcode_Generator.exe``` to place on your desktop
### From the Release
1. Download and extract the ```.zip```
2. Edit ```.env``` with the defaults; ```HOTFOLDER_DIR```, and ```DEFAULT_PDF_DIR```. Downloads
3. Optionally You could create a shortcut of ```Receiving_Barcode_Generator.exe``` to place on your desktop


## Logging
Very simple logging to a text file in the root dir
