# PII Application

### About
This application identifies likely PII (personally identifiable information) in a dataset. To use, download the .exe installer from the [latest release](https://github.com/PovertyAction/PII_detection/releases/latest) and follow the in-app directions.

This tool is current listed as an alpha release because it is still being tested on IPA PII-containing field datasets.

### How does it work?

There are a series of rules that are applied to a dataset's column to identify if a given column is a PII. Such rules are:

* If column name or label match with any word of the list of restricted words ( ex 'name', 'surname', 'ssn', etc; check restricted_words.py) and has sufficiently sparse string entries.
Ex: ‘What is your name?’ would be flagged, but ‘Do you like your name?’ not.
* If entries in a given column have a specific format (at the moment checking phone number format and date format, we can expand to  gps, national identifiers, etc)
* If all entries in a given column are sufficiently sparse (almost all unique). Ideal to identify open ended questions.

Importantly, this is an arbitrary defined list of conditions, and for sure can be improved. Very open to feedback!

Once the PIIs are identified, users have the opportunity to say what they would like to do with those columns. Options are: drop column, encode column or keep column. According to those instructions, a new de-identified dataset is created. Also, the system outputs a log .txt file and a .csv file that maps the new and encoded values.

### Files included

#### Main files
* app_frontend.py: App GUI script using tkinter.
* PII_data_processor.py: App backend, it reads data files, identifies PIIs and creates new de-identified data files.
* find_piis_in_unstructed_text.py: Script used by PII_data_processor to particularly detect piis in unstructured text

### Other utility files
* restricted_words.py: Script to get restricted words for PII identification
* constant_strings.py: Declares strings used across app.
* query_google_answer_boxes.py: Script to query locations and populations
* dist folder: Contains .exe file for execution
* hook-spacy.py: Dependency file needed when creating .exe

### Setup

`sudo apt install python3.8-tk`



### Help and Support

Please feel free to open an issue for fixes or new feature requests. You can also contact researchsupport@poverty-action.org

### Contributing

We welcome contributions in any form! To contribute please fork the project, make your changes and submit a pull request. We will do our best to work through any issues with you and get your code merged into the main branch.

### Credit

IPA's RT-DEG teams.

J-PAL: stata_PII_scan. 2020. https://github.com/J-PAL/stata_PII_scan

J-PAL: PII-Scan. 2017. https://github.com/J-PAL/PII-Scan

### Licensing

The PII script is [MIT Licensed](https://github.com/PovertyAction/PII_detection/blob/master/LICENSE).

### Distribution

#### To create executable app
`pyinstaller --windowed --icon=app_icon.ico --add-data="app_icon.ico;." --add-data="ipa_logo.jpg;." --add-data="anonymize_script_template_v2.do;." --additional-hooks-dir=. --hiddenimport srsly.msgpack.util --noconfirm app_frontend.py`

#### To create windows application installer
Compile `create_installer.iss` using Inno Setup Compiler
<!-- Reference: https://www.youtube.com/watch?v=RrpvNvklmFA https://www.youtube.com/watch?v=DTQ-atboQiI&t=135s-->
