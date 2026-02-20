# ForgeKeeper Language Module: Node.js / TypeScript / Front-end
# Installs Node.js 20 LTS, Bun, Deno, and common JS tooling
ARG USERNAME=vscode
ARG GO_VERSION=1.22.3

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g npm@latest \
    && corepack enable \
    && corepack prepare pnpm@latest --activate \
    && corepack prepare yarn@stable --activate \
    && npm install -g typescript ts-node eslint prettier webpack vite turbo nx \
        @angular/cli @vue/cli react-native-cli create-react-app \
        vercel netlify-cli serve http-server @devcontainers/cli \
    && npm cache clean --force \
    && rm -rf /var/lib/apt/lists/*

RUN su - ${USERNAME} -c "curl -fsSL https://bun.sh/install | bash" \
    && su - ${USERNAME} -c "curl -fsSL https://deno.land/install.sh | sh"
