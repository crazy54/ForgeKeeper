# ForgeKeeper Language Module: Dart
ARG DART_VERSION_CHANNEL=stable

RUN wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/dart.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/dart.gpg] https://storage.googleapis.com/download.dartlang.org/linux/debian ${DART_VERSION_CHANNEL} main" > /etc/apt/sources.list.d/dart.list \
    && apt-get update \
    && apt-get install -y dart \
    && rm -rf /var/lib/apt/lists/*
