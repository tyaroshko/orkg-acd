conda create --prefix ./env python=3.10
conda activate ./env
conda install poetry
poetry install
pip wheel --no-cache-dir --use-pep517 "pymupdf (==1.20.2)"
pip install fitz
pip install frontend
pip install --upgrade fake-useragent