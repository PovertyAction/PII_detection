
# PII Application

### About
This application identifies likely PII (personally identifiable information) in a dataset. To use, download the .exe from the latest release and follow the in-app directions.

This tool is current listed as an alpha release because it is still being tested on IPA PII-containing field datasets.

### Help and Support

Please feel free to open an issue for fixes or new feature requests. You can also contact researchsupport@poverty-action.org

### Contributing

We welcome contributions in any form! To contribute please fork the project make your changes and submit a pull request. We will do our best to work through any issues with you and get your code merged into the main branch.

### Credit

J-PAL: PII-Scan. 2017. https://github.com/J-PAL/PII-Scan

IPA's RT-DEG teams.

### Licensing

The PII script is [MIT Licensed](https://github.com/PovertyAction/PII_detection/blob/master/LICENSE).

### To create .exe from source file
`pyinstaller --onefile --windowed --icon=app.ico --add-data="app.ico;." --add-data="ipa_logo.jpg;." tkinter_script.py`