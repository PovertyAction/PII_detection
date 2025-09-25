# HOOK FILE FOR PRESIDIO AND RELATED DEPENDENCIES
# Required for PyInstaller to properly bundle Presidio components

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# ----------------------------- PRESIDIO-ANALYZER -----------------------------
data = collect_all("presidio_analyzer")
datas = data[0]
binaries = data[1]
hiddenimports = data[2]

# Collect recognizer modules
hiddenimports += collect_submodules("presidio_analyzer.predefined_recognizers")

# ----------------------------- PRESIDIO-ANONYMIZER -----------------------------
data = collect_all("presidio_anonymizer")
datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# Collect anonymizer operators
hiddenimports += collect_submodules("presidio_anonymizer.operators")

# ----------------------------- SPACY MODELS -----------------------------
# Include spaCy models that Presidio uses
# Note: This assumes en_core_web_sm model - adjust based on your needs
try:
    import en_core_web_sm  # noqa: F401

    datas += collect_data_files("en_core_web_sm")
except ImportError:
    pass

# ----------------------------- TRANSFORMERS (if using) -----------------------------
# Presidio can use Transformers models for enhanced NER
try:
    data = collect_all("transformers")
    datas += data[0]
    binaries += data[1]
    hiddenimports += data[2]
except ImportError:
    pass

# ----------------------------- ADDITIONAL DEPENDENCIES -----------------------------
# Other dependencies that Presidio might need
for module in ["regex", "phonenumbers", "python_dateutil"]:
    try:
        data = collect_all(module)
        datas += data[0]
        binaries += data[1]
        hiddenimports += data[2]
    except ImportError:
        pass
