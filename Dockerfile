# syntax=docker/dockerfile:1.7
ARG BASE_IMAGE=mcr.microsoft.com/devcontainers/base:ubuntu-24.04
FROM ${BASE_IMAGE}

ARG DEBIAN_FRONTEND=noninteractive
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=1000
ARG FORGEKEEPER_USER_EMAIL=dev@example.com
ARG FORGEKEEPER_HANDLE=forgekeeper
ARG FORGEKEEPER_WORKSPACE=playground
ARG GO_VERSION=1.22.3
ARG DART_VERSION_CHANNEL=stable
ARG OPENVSCODE_VERSION=1.89.1
ARG LAZYDOCKER_VERSION=0.23.3
ARG HELIX_VERSION=23.10
ARG ZELLIJ_VERSION=0.37.2
ARG SWIFT_VERSION=5.10.1-RELEASE
ARG SWIFT_PLATFORM=ubuntu24.04
ARG KOTLIN_VERSION=1.9.24
ARG HELM_VERSION=3.15.0
ARG KUSTOMIZE_VERSION=5.4.2
ARG TERRAFORM_VERSION=1.7.5
ARG GUM_VERSION=0.13.0
ARG DOCKER_COMPOSE_VERSION=2.27.0

ENV FORGEKEEPER_USER_EMAIL=${FORGEKEEPER_USER_EMAIL} \
    FORGEKEEPER_HANDLE=${FORGEKEEPER_HANDLE} \
    FORGEKEEPER_WORKSPACE=${FORGEKEEPER_WORKSPACE} \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    TZ=Etc/UTC \
    SHELL=/usr/bin/zsh \
    PIPX_HOME=/home/${USERNAME}/.local/pipx \
    PIPX_BIN_DIR=/home/${USERNAME}/.local/bin \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PATH=/home/${USERNAME}/.local/bin:/home/${USERNAME}/.cargo/bin:/home/${USERNAME}/.bun/bin:/home/${USERNAME}/.deno/bin:/usr/local/go/bin:/opt/swift/usr/bin:/opt/kotlin/kotlinc/bin:/usr/local/bin:$PATH

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Locale + base packages
RUN locale-gen en_US.UTF-8 \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        apt-transport-https \
        ca-certificates \
        software-properties-common \
        locales \
        tzdata \
        sudo \
        git \
        curl \
        wget \
        gnupg \
        unzip \
        zip \
        tar \
        xz-utils \
        rsync \
        lsb-release \
        build-essential \
        clang \
        clangd \
        cmake \
        ninja-build \
        pkg-config \
        gdb \
        lldb \
        valgrind \
        strace \
        lsof \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        pipx \
        openjdk-21-jdk \
        maven \
        gradle \
        ruby-full \
        php-cli \
        php-xml \
        php-curl \
        php-mbstring \
        sqlite3 \
        postgresql-client \
        mysql-client \
        redis-tools \
        tmux \
        screen \
        zsh \
        fish \
        direnv \
        fzf \
        ripgrep \
        fd-find \
        bat \
        git-delta \
        just \
        neovim \
        fonts-firacode \
        fonts-jetbrains-mono \
        fontconfig \
        netcat-openbsd \
        iperf3 \
        httpie \
        dnsutils \
        traceroute \
        jq \
        yq \
        htop \
        btop \
        glances \
        iotop \
        iftop \
        nvtop \
        sysstat \
        ufw \
        supervisor \
        ca-certificates \
        shellcheck \
        tree \
        graphviz \
        libssl-dev \
        libbz2-dev \
        libreadline-dev \
        libffi-dev \
        liblzma-dev \
        libsqlite3-dev \
        zlib1g-dev \
        autoconf \
        automake \
        libtool \
        pkg-config \
        imagemagick \
        docker.io \
        containerd \
        ansible \
        cowsay \
        figlet \
        toilet \
        neofetch \
        chafa \
        moreutils \
        pandoc \
        markdown \
        yamllint \
        tidy \
        lynx \
        sshpass \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip \
    && unzip /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/aws /tmp/awscliv2.zip

RUN gem install --no-document lolcat

RUN ln -sf /usr/bin/fdfind /usr/local/bin/fd || true

# Charm gum for interactive banners/scripts
RUN curl -fsSL https://github.com/charmbracelet/gum/releases/download/v${GUM_VERSION}/gum_${GUM_VERSION}_Linux_x86_64.tar.gz -o /tmp/gum.tgz \
    && tar -xzf /tmp/gum.tgz -C /tmp gum \
    && install /tmp/gum /usr/local/bin/gum \
    && rm -f /tmp/gum /tmp/gum.tgz

# Create dev user
RUN if ! id -u ${USERNAME} >/dev/null 2>&1; then \
        if ! getent group ${USER_GID} >/dev/null; then groupadd --gid ${USER_GID} ${USERNAME}; fi; \
        useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} -s /usr/bin/zsh; \
    fi \
    && usermod -aG sudo,docker ${USERNAME} \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/90-${USERNAME} \
    && chmod 0440 /etc/sudoers.d/90-${USERNAME}

# Node.js 20.x, PNPM/Yarn, JavaScript tooling
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g npm@latest \
    && corepack enable \
    && corepack prepare pnpm@latest --activate \
    && corepack prepare yarn@stable --activate \
    && npm install -g typescript ts-node eslint prettier webpack vite turbo nx @angular/cli @vue/cli react-native-cli create-react-app vercel netlify-cli serve http-server @devcontainers/cli \
    && npm cache clean --force \
    && rm -rf /var/lib/apt/lists/*

# Bun & Deno
RUN su - ${USERNAME} -c "curl -fsSL https://bun.sh/install | bash" \
    && su - ${USERNAME} -c "curl -fsSL https://deno.land/install.sh | sh"

# Go toolchain
RUN curl -fsSL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz -o /tmp/go.tar.gz \
    && rm -rf /usr/local/go \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz

RUN for pkg in \
        golang.org/x/tools/gopls@latest \
        golang.org/x/lint/golint@latest \
        github.com/go-delve/delve/cmd/dlv@latest \
        github.com/air-verse/air@latest \
        github.com/derailed/k9s@latest \
        github.com/golangci/golangci-lint/cmd/golangci-lint@latest \
        github.com/golang/mock/mockgen@latest; do \
        GOBIN=/usr/local/bin /usr/local/go/bin/go install "$pkg"; \
    done

RUN curl -fsSL https://github.com/zellij-org/zellij/releases/download/v${ZELLIJ_VERSION}/zellij-x86_64-unknown-linux-musl.tar.gz -o /tmp/zellij.tgz \
    && tar -xzf /tmp/zellij.tgz -C /usr/local/bin zellij \
    && chmod +x /usr/local/bin/zellij \
    && rm /tmp/zellij.tgz

# Rust toolchain + CLI helpers
RUN su - ${USERNAME} -c "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y" \
    && su - ${USERNAME} -c "~/.cargo/bin/rustup component add rustfmt clippy" \
    && su - ${USERNAME} -c "~/.cargo/bin/rustup target add wasm32-unknown-unknown" \
    && su - ${USERNAME} -c "~/.cargo/bin/cargo install --locked wasm-pack cargo-watch trunk tauri-cli procs cargo-nextest@0.9.125" \
    && su - ${USERNAME} -c "~/.cargo/bin/cargo install --locked zellij@${ZELLIJ_VERSION}"

# Python tooling + Jupyter stack
RUN su - ${USERNAME} -c "pipx install pipenv" \
    && su - ${USERNAME} -c "pipx install poetry" \
    && su - ${USERNAME} -c "pipx install rye" \
    && su - ${USERNAME} -c "pipx install pre-commit" \
    && python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel \
    && python3 -m pip install --no-cache-dir jupyterlab notebook voila ipykernel black ruff flake8 mypy pytest pytest-cov ipywidgets jupyterlab-code-formatter jupyterlab-git pandas numpy scipy matplotlib seaborn plotly scikit-learn polars tensorflow torch torchvision torchaudio mlflow tensorboard pyspark sqlfluff[lint] \
    && python3 -m ipykernel install --name forgekeeper --display-name "ForgeKeeper Python"

# .NET SDKs
RUN wget https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y dotnet-sdk-8.0 dotnet-sdk-7.0 aspnetcore-runtime-8.0 \
    && rm -rf /var/lib/apt/lists/*

# Dart SDK
RUN wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/dart.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/dart.gpg] https://storage.googleapis.com/download.dartlang.org/linux/debian ${DART_VERSION_CHANNEL} main" > /etc/apt/sources.list.d/dart.list \
    && apt-get update \
    && apt-get install -y dart \
    && rm -rf /var/lib/apt/lists/*

# Kotlin compiler
RUN curl -fsSL https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip -o /tmp/kotlin.zip \
    && mkdir -p /opt/kotlin \
    && unzip /tmp/kotlin.zip -d /opt/kotlin \
    && ln -sf /opt/kotlin/kotlinc/bin/kotlinc /usr/local/bin/kotlinc \
    && ln -sf /opt/kotlin/kotlinc/bin/kotlin /usr/local/bin/kotlin \
    && rm /tmp/kotlin.zip

# Swift toolchain
RUN curl -fsSL https://download.swift.org/swift-${SWIFT_VERSION}/${SWIFT_PLATFORM}/swift-${SWIFT_VERSION}-${SWIFT_PLATFORM}.tar.gz -o /tmp/swift.tar.gz \
    && tar -xzf /tmp/swift.tar.gz -C /opt \
    && mv /opt/swift-${SWIFT_VERSION}-${SWIFT_PLATFORM} /opt/swift \
    && ln -s /opt/swift/usr/bin/swift /usr/local/bin/swift \
    && rm /tmp/swift.tar.gz

# VS Code in browser & openvscode
RUN curl -fsSL https://code-server.dev/install.sh | sh \
    && curl -fsSL https://github.com/gitpod-io/openvscode-server/releases/download/openvscode-server-v${OPENVSCODE_VERSION}/openvscode-server-v${OPENVSCODE_VERSION}-linux-x64.tar.gz -o /tmp/openvscode.tar.gz \
    && mkdir -p /opt/openvscode \
    && tar -xzf /tmp/openvscode.tar.gz -C /opt/openvscode --strip-components=1 \
    && ln -s /opt/openvscode/bin/openvscode-server /usr/local/bin/openvscode-server \
    && rm /tmp/openvscode.tar.gz

# Browser terminals & dashboards
RUN npm install -g wetty \
    && curl -fsSL https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 -o /usr/local/bin/ttyd \
    && chmod +x /usr/local/bin/ttyd \
    && curl -fsSL https://github.com/jesseduffield/lazydocker/releases/download/v${LAZYDOCKER_VERSION}/lazydocker_${LAZYDOCKER_VERSION}_Linux_x86_64.tar.gz -o /tmp/lazydocker.tgz \
    && tar -xzf /tmp/lazydocker.tgz -C /tmp lazydocker \
    && mv /tmp/lazydocker /usr/local/bin/lazydocker \
    && rm /tmp/lazydocker.tgz

# Kubernetes & IaC CLIs
RUN curl -fsSLo /usr/local/bin/kubectl https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl \
    && chmod +x /usr/local/bin/kubectl \
    && curl -fsSL https://get.helm.sh/helm-v${HELM_VERSION}-linux-amd64.tar.gz -o /tmp/helm.tar.gz \
    && tar -xzf /tmp/helm.tar.gz -C /tmp linux-amd64/helm \
    && mv /tmp/linux-amd64/helm /usr/local/bin/helm \
    && rm -rf /tmp/helm.tar.gz /tmp/linux-amd64 \
    && curl -fsSL https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv${KUSTOMIZE_VERSION}/kustomize_v${KUSTOMIZE_VERSION}_linux_amd64.tar.gz -o /tmp/kustomize.tgz \
    && tar -xzf /tmp/kustomize.tgz -C /usr/local/bin kustomize \
    && rm /tmp/kustomize.tgz \
    && curl -fsSL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip -o /tmp/terraform.zip \
    && unzip /tmp/terraform.zip -d /usr/local/bin \
    && rm /tmp/terraform.zip

# Helix editor
RUN curl -fsSL https://github.com/helix-editor/helix/releases/download/${HELIX_VERSION}/helix-${HELIX_VERSION}-x86_64-linux.tar.xz -o /tmp/helix.tar.xz \
    && tar -xf /tmp/helix.tar.xz -C /opt \
    && ln -s /opt/helix-${HELIX_VERSION}/hx /usr/local/bin/hx \
    && rm /tmp/helix.tar.xz

# Starship prompt
RUN curl -fsSL https://starship.rs/install.sh | sh -s -- -y -b /usr/local/bin

# VS Code CLI extensions and fonts placeholder (extensions installed later via scripts)

# Oh My Zsh + starship config + banner
RUN su - ${USERNAME} -c "git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git ~/.oh-my-zsh" \
    && su - ${USERNAME} -c "cp ~/.oh-my-zsh/templates/zshrc.zsh-template ~/.zshrc"

RUN cat <<EOS >> /home/${USERNAME}/.zshrc
# ForgeKeeper defaults
export FORGEKEEPER_USER_EMAIL="${FORGEKEEPER_USER_EMAIL}"
export FORGEKEEPER_HANDLE="${FORGEKEEPER_HANDLE}"
export FORGEKEEPER_WORKSPACE="${FORGEKEEPER_WORKSPACE}"
if command -v starship >/dev/null 2>&1; then
  eval "\$(starship init zsh)"
fi
if command -v direnv >/dev/null 2>&1; then
  eval "\$(direnv hook zsh)"
fi
alias kk=kubectl
EOS
RUN chown ${USERNAME}:${USERNAME} /home/${USERNAME}/.zshrc

RUN mkdir -p /usr/local/share/forgekeeper /etc/profile.d /var/log/forgekeeper /opt/forgekeeper

COPY logo/ /usr/local/share/forgekeeper/logo/
COPY portal/ /opt/forgekeeper/portal/
COPY logo/ /opt/forgekeeper/portal/logo/
COPY scripts/forgekeeper-control.sh /usr/local/bin/forgekeeper-control.sh

RUN chmod +x /usr/local/bin/forgekeeper-control.sh \
    && cp /usr/local/share/forgekeeper/logo/Forge.png /opt/forgekeeper/portal/logo/Forge.png >/dev/null 2>&1 || true \
    && sed -i "s|__FORGEKEEPER_HANDLE__|${FORGEKEEPER_HANDLE}|g" /opt/forgekeeper/portal/config.js \
    && sed -i "s|__FORGEKEEPER_USER_EMAIL__|${FORGEKEEPER_USER_EMAIL}|g" /opt/forgekeeper/portal/config.js \
    && sed -i "s|__FORGEKEEPER_WORKSPACE__|${FORGEKEEPER_WORKSPACE}|g" /opt/forgekeeper/portal/config.js \
    && chown -R ${USERNAME}:${USERNAME} /opt/forgekeeper/portal /var/log/forgekeeper

RUN cat <<'EOBANNER' > /usr/local/bin/forgekeeper-banner.sh
#!/usr/bin/env bash
set -euo pipefail
LOGO_PATH="/usr/local/share/forgekeeper/logo/Forge.png"
if command -v chafa >/dev/null 2>&1 && [ -f "$LOGO_PATH" ]; then
  chafa --fill=block --symbols=block --size=64x20 "$LOGO_PATH"
else
cat <<'ASCII'
 ______                     _                 
|  ____|                   | |                
| |__   _ __   ___   ___   | | ___   ___  ___ 
|  __| | '_ \ / _ \ / _ \  | |/ _ \ / _ \/ __|
| |____| | | |  __/| (_) | | | (_) |  __/\__ \
|______|_| |_|\___| \___/  |_|\___/ \___||___/
ASCII
fi
printf "User: %s\nEmail: %s\nWorkspace: %s\n" "${FORGEKEEPER_HANDLE:-unknown}" "${FORGEKEEPER_USER_EMAIL:-unknown}" "${FORGEKEEPER_WORKSPACE:-unknown}" | cowsay -f tux || true
EOBANNER
RUN chmod +x /usr/local/bin/forgekeeper-banner.sh \
    && echo '/usr/local/bin/forgekeeper-banner.sh' > /etc/profile.d/00-forgekeeper-banner.sh

# Supervisor definitions for hosted apps
RUN mkdir -p /etc/supervisor/conf.d \
    && cat <<EOSUP > /etc/supervisor/conf.d/code-server.conf
[program:code-server]
command=/usr/bin/code-server --bind-addr 0.0.0.0:8080 --auth none --disable-telemetry
user=${USERNAME}
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
EOSUP

RUN cat <<EOSUP > /etc/supervisor/conf.d/openvscode.conf
[program:openvscode]
command=/usr/local/bin/openvscode-server --host 0.0.0.0 --port 3000
user=${USERNAME}
autostart=false
autorestart=true
EOSUP

RUN cat <<EOSUP > /etc/supervisor/conf.d/jupyter.conf
[program:jupyter]
command=/usr/bin/env bash -lc "jupyter lab --ip=0.0.0.0 --no-browser --NotebookApp.token='' --NotebookApp.password=''"
autostart=false
autorestart=true
user=${USERNAME}
EOSUP

RUN cat <<EOSUP > /etc/supervisor/conf.d/ttyd.conf
[program:ttyd]
command=/usr/local/bin/ttyd -p 7681 zsh
user=${USERNAME}
autostart=true
autorestart=true
EOSUP

RUN cat <<'EOSUP' > /etc/supervisor/conf.d/portal.conf
[program:forgekeeper-portal]
directory=/opt/forgekeeper/portal
environment=FORGEKEEPER_PORTAL_PORT=7000
command=/usr/bin/env python3 /opt/forgekeeper/portal/server.py
user=${USERNAME}
autostart=true
autorestart=true
stdout_logfile=/var/log/forgekeeper/portal.log
stderr_logfile=/var/log/forgekeeper/portal.err.log
EOSUP

# Entrypoint printing banner then executing command
RUN cat <<'EOENTRY' > /usr/local/bin/forgekeeper-entrypoint.sh
#!/usr/bin/env bash
set -e
/usr/local/bin/forgekeeper-banner.sh || true
if ! pgrep -x supervisord >/dev/null 2>&1; then
  /usr/bin/supervisord -c /etc/supervisor/supervisord.conf >/var/log/forgekeeper/supervisord.log 2>&1 &
fi
exec "$@"
EOENTRY

RUN chmod +x /usr/local/bin/forgekeeper-entrypoint.sh

EXPOSE 8080 3000 3001 3002 7000 7681 8001 8081 8082 8083 8084 8888 5000 5050 6006 9000 9090 16686 19999

USER ${USERNAME}
WORKDIR /workspaces

ENTRYPOINT ["/usr/local/bin/forgekeeper-entrypoint.sh"]
CMD ["sleep", "infinity"]
