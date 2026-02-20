#!/usr/bin/env bash
# ForgeKeeper Runtime Manager
# Usage: install-lang.sh <install|remove|list> [language]
# Can be called from CLI or the portal /forgekeeper/runtime endpoint
set -euo pipefail

LANG_STATE_DIR="/etc/forgekeeper/langs"
MODULES_DIR="/opt/forgekeeper/dockerfiles"
LOG="/var/log/forgekeeper/runtime.log"
USERNAME="${SUDO_USER:-${USER:-vscode}}"

SUPPORTED_LANGS=(python node go rust java dotnet ruby php swift dart)

log() { mkdir -p "$(dirname "$LOG")"; echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }
die() { echo "ERROR: $*" >&2; exit 1; }

usage() {
  echo "Usage: forgekeeper-runtime <install|remove|list> [language]"
  echo "Languages: ${SUPPORTED_LANGS[*]}"
  exit 0
}

is_installed() {
  [[ -f "${LANG_STATE_DIR}/$1.installed" ]]
}

mark_installed() {
  mkdir -p "$LANG_STATE_DIR"
  touch "${LANG_STATE_DIR}/$1.installed"
}

mark_removed() {
  rm -f "${LANG_STATE_DIR}/$1.installed"
}

cmd_list() {
  echo "ForgeKeeper Language Runtimes"
  echo "─────────────────────────────"
  for lang in "${SUPPORTED_LANGS[@]}"; do
    if is_installed "$lang"; then
      echo "  ✓ $lang  (installed)"
    else
      echo "  ○ $lang  (not installed)"
    fi
  done
}

cmd_install() {
  local lang="${1:-}"
  [[ -z "$lang" ]] && die "Specify a language. Run 'forgekeeper-runtime list' to see options."

  # Validate
  local valid=false
  for l in "${SUPPORTED_LANGS[@]}"; do [[ "$l" == "$lang" ]] && valid=true; done
  [[ "$valid" == false ]] && die "Unknown language: $lang. Supported: ${SUPPORTED_LANGS[*]}"

  if is_installed "$lang"; then
    echo "$lang is already installed."
    exit 0
  fi

  log "Installing language module: $lang"

  case "$lang" in
    python)
      pip3 install --no-cache-dir \
        jupyterlab notebook voila ipykernel \
        black ruff flake8 mypy pytest pytest-cov \
        ipywidgets jupyterlab-code-formatter jupyterlab-git \
        pandas numpy scipy matplotlib seaborn plotly \
        scikit-learn polars mlflow tensorboard
      python3 -m ipykernel install --name forgekeeper --display-name "ForgeKeeper Python"
      ;;
    node)
      curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
      apt-get install -y --no-install-recommends nodejs
      npm install -g npm@latest typescript ts-node eslint prettier vite turbo
      corepack enable
      # Install Bun and Deno as the dev user
      su - "$USERNAME" -c "curl -fsSL https://bun.sh/install | bash" || true
      su - "$USERNAME" -c "curl -fsSL https://deno.land/install.sh | sh" || true
      ;;
    go)
      local GO_VERSION="1.22.3"
      curl -fsSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -o /tmp/go.tar.gz
      rm -rf /usr/local/go
      tar -C /usr/local -xzf /tmp/go.tar.gz
      rm /tmp/go.tar.gz
      export PATH="/usr/local/go/bin:$PATH"
      for pkg in \
          golang.org/x/tools/gopls@latest \
          github.com/go-delve/delve/cmd/dlv@latest \
          github.com/air-verse/air@latest \
          github.com/golangci/golangci-lint/cmd/golangci-lint@latest; do
        GOBIN=/usr/local/bin /usr/local/go/bin/go install "$pkg"
      done
      ;;
    rust)
      su - "$USERNAME" -c "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y"
      su - "$USERNAME" -c "~/.cargo/bin/rustup component add rustfmt clippy"
      su - "$USERNAME" -c "~/.cargo/bin/rustup target add wasm32-unknown-unknown"
      su - "$USERNAME" -c "~/.cargo/bin/cargo install --locked cargo-watch cargo-nextest@0.9.125"
      ;;
    java)
      apt-get update
      apt-get install -y --no-install-recommends openjdk-21-jdk maven gradle
      local KOTLIN_VERSION="1.9.24"
      curl -fsSL "https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip" -o /tmp/kotlin.zip
      mkdir -p /opt/kotlin
      unzip /tmp/kotlin.zip -d /opt/kotlin
      ln -sf /opt/kotlin/kotlinc/bin/kotlinc /usr/local/bin/kotlinc
      ln -sf /opt/kotlin/kotlinc/bin/kotlin /usr/local/bin/kotlin
      rm /tmp/kotlin.zip
      apt-get clean && rm -rf /var/lib/apt/lists/*
      ;;
    dotnet)
      wget https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb -O /tmp/ms-prod.deb
      dpkg -i /tmp/ms-prod.deb
      rm /tmp/ms-prod.deb
      apt-get update
      apt-get install -y dotnet-sdk-8.0 aspnetcore-runtime-8.0
      apt-get clean && rm -rf /var/lib/apt/lists/*
      ;;
    ruby)
      apt-get update
      apt-get install -y --no-install-recommends ruby-full
      gem install --no-document bundler jekyll
      apt-get clean && rm -rf /var/lib/apt/lists/*
      ;;
    php)
      apt-get update
      apt-get install -y --no-install-recommends php-cli php-xml php-curl php-mbstring php-zip
      curl -fsSL https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
      apt-get clean && rm -rf /var/lib/apt/lists/*
      ;;
    swift)
      local SWIFT_VERSION="5.10.1-RELEASE"
      local SWIFT_PLATFORM="ubuntu24.04"
      curl -fsSL "https://download.swift.org/swift-${SWIFT_VERSION}/${SWIFT_PLATFORM}/swift-${SWIFT_VERSION}-${SWIFT_PLATFORM}.tar.gz" -o /tmp/swift.tar.gz
      tar -xzf /tmp/swift.tar.gz -C /opt
      mv "/opt/swift-${SWIFT_VERSION}-${SWIFT_PLATFORM}" /opt/swift
      ln -sf /opt/swift/usr/bin/swift /usr/local/bin/swift
      rm /tmp/swift.tar.gz
      ;;
    dart)
      wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/dart.gpg
      echo "deb [signed-by=/usr/share/keyrings/dart.gpg] https://storage.googleapis.com/download.dartlang.org/linux/debian stable main" > /etc/apt/sources.list.d/dart.list
      apt-get update
      apt-get install -y dart
      apt-get clean && rm -rf /var/lib/apt/lists/*
      ;;
  esac

  mark_installed "$lang"
  log "Successfully installed: $lang"
  echo "✓ $lang installed successfully."
}

cmd_remove() {
  local lang="${1:-}"
  [[ -z "$lang" ]] && die "Specify a language to remove."

  if ! is_installed "$lang"; then
    echo "$lang is not installed."
    exit 0
  fi

  log "Removing language module: $lang"

  case "$lang" in
    python)
      pip3 uninstall -y jupyterlab notebook pandas numpy scipy torch tensorflow mlflow || true
      ;;
    node)
      npm uninstall -g typescript ts-node eslint prettier vite turbo || true
      apt-get remove -y nodejs || true
      ;;
    go)
      rm -rf /usr/local/go
      rm -f /usr/local/bin/gopls /usr/local/bin/dlv /usr/local/bin/air /usr/local/bin/golangci-lint
      ;;
    rust)
      su - "$USERNAME" -c "~/.cargo/bin/rustup self uninstall -y" || true
      ;;
    java)
      apt-get remove -y openjdk-21-jdk maven gradle || true
      rm -rf /opt/kotlin
      rm -f /usr/local/bin/kotlinc /usr/local/bin/kotlin
      apt-get autoremove -y
      ;;
    dotnet)
      apt-get remove -y dotnet-sdk-8.0 aspnetcore-runtime-8.0 || true
      apt-get autoremove -y
      ;;
    ruby)
      apt-get remove -y ruby-full || true
      apt-get autoremove -y
      ;;
    php)
      apt-get remove -y php-cli php-xml php-curl php-mbstring || true
      rm -f /usr/local/bin/composer
      apt-get autoremove -y
      ;;
    swift)
      rm -rf /opt/swift
      rm -f /usr/local/bin/swift
      ;;
    dart)
      apt-get remove -y dart || true
      rm -f /etc/apt/sources.list.d/dart.list /usr/share/keyrings/dart.gpg
      apt-get autoremove -y
      ;;
  esac

  mark_removed "$lang"
  log "Removed: $lang"
  echo "✓ $lang removed."
}

# ── Entrypoint ────────────────────────────────────────────────────────────────
ACTION="${1:-list}"
LANG_ARG="${2:-}"

case "$ACTION" in
  install) cmd_install "$LANG_ARG" ;;
  remove)  cmd_remove  "$LANG_ARG" ;;
  list)    cmd_list ;;
  *)       usage ;;
esac
