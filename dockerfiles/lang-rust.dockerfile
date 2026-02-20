# ForgeKeeper Language Module: Rust
ARG USERNAME=vscode
ARG ZELLIJ_VERSION=0.37.2

RUN su - ${USERNAME} -c "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y" \
    && su - ${USERNAME} -c "~/.cargo/bin/rustup component add rustfmt clippy" \
    && su - ${USERNAME} -c "~/.cargo/bin/rustup target add wasm32-unknown-unknown" \
    && su - ${USERNAME} -c "~/.cargo/bin/cargo install --locked wasm-pack cargo-watch trunk tauri-cli procs cargo-nextest@0.9.125"
