# ForgeKeeper Language Module: Python & Data Science
# Installs CPython, pip tooling, Jupyter, ML/data stack
ARG USERNAME=vscode

RUN su - ${USERNAME} -c "pipx install pipenv" \
    && su - ${USERNAME} -c "pipx install poetry" \
    && su - ${USERNAME} -c "pipx install rye" \
    && su - ${USERNAME} -c "pipx install pre-commit" \
    && python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python3 -m pip install --no-cache-dir \
        jupyterlab notebook voila ipykernel \
        black ruff flake8 mypy pytest pytest-cov \
        ipywidgets jupyterlab-code-formatter jupyterlab-git \
        pandas numpy scipy matplotlib seaborn plotly \
        scikit-learn polars tensorflow torch torchvision torchaudio \
        mlflow tensorboard pyspark "sqlfluff[lint]" \
    && python3 -m ipykernel install --name forgekeeper --display-name "ForgeKeeper Python"
