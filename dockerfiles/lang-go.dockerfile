# ForgeKeeper Language Module: Go
ARG GO_VERSION=1.22.3

RUN curl -fsSL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz -o /tmp/go.tar.gz \
    && rm -rf /usr/local/go \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz

RUN for pkg in \
        golang.org/x/tools/gopls@latest \
        golang.org/x/lint/golint@latest \
        github.com/go-delve/delve/cmd/dlv@latest \
        github.com/air-verse/air@latest \
        github.com/golangci/golangci-lint/cmd/golangci-lint@latest \
        github.com/golang/mock/mockgen@latest; do \
        GOBIN=/usr/local/bin /usr/local/go/bin/go install "$pkg"; \
    done
