# HOOK FILE FOR SPACY
# Reference: https://stackoverflow.com/questions/59645155/spacy-2-2-3-filenotfounderror-errno-2-no-such-file-or-directory-thinc-neur
from PyInstaller.utils.hooks import collect_all

# ----------------------------- SPACY -----------------------------
data = collect_all("spacy")

datas = data[0]
binaries = data[1]
hiddenimports = data[2]

# ----------------------------- THINC -----------------------------
data = collect_all("thinc")

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- CYMEM -----------------------------
data = collect_all("cymem")

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- PRESHED -----------------------------
data = collect_all("preshed")

datas += data[0]
binaries += data[1]
hiddenimports += data[2]

# ----------------------------- BLIS -----------------------------

data = collect_all("blis")

datas += data[0]
binaries += data[1]
hiddenimports += data[2]
# This hook file is a bit of a hack - really, all of the libraries should be in separate hook files. (Eg hook-blis.py with the blis part of the hook)

# ----------------------------- SPACY MODELS -----------------------------
# Include spaCy language models if present
try:
    import en_core_web_sm  # noqa: F401
    from PyInstaller.utils.hooks import collect_data_files

    datas += collect_data_files("en_core_web_sm")
except ImportError:
    pass

try:
    import en_core_web_md  # noqa: F401

    datas += collect_data_files("en_core_web_md")
except ImportError:
    pass

try:
    import en_core_web_lg  # noqa: F401

    datas += collect_data_files("en_core_web_lg")
except ImportError:
    pass
