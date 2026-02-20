# ForgeKeeper Language Module: JVM (Java, Kotlin, Scala)
ARG KOTLIN_VERSION=1.9.24

# Java + Maven + Gradle already in base apt block.
# This module adds Kotlin compiler.
RUN curl -fsSL https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip -o /tmp/kotlin.zip \
    && mkdir -p /opt/kotlin \
    && unzip /tmp/kotlin.zip -d /opt/kotlin \
    && ln -sf /opt/kotlin/kotlinc/bin/kotlinc /usr/local/bin/kotlinc \
    && ln -sf /opt/kotlin/kotlinc/bin/kotlin /usr/local/bin/kotlin \
    && rm /tmp/kotlin.zip
