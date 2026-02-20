# ForgeKeeper Language Module: Swift
ARG SWIFT_VERSION=5.10.1-RELEASE
ARG SWIFT_PLATFORM=ubuntu24.04

RUN curl -fsSL https://download.swift.org/swift-${SWIFT_VERSION}/${SWIFT_PLATFORM}/swift-${SWIFT_VERSION}-${SWIFT_PLATFORM}.tar.gz -o /tmp/swift.tar.gz \
    && tar -xzf /tmp/swift.tar.gz -C /opt \
    && mv /opt/swift-${SWIFT_VERSION}-${SWIFT_PLATFORM} /opt/swift \
    && ln -s /opt/swift/usr/bin/swift /usr/local/bin/swift \
    && rm /tmp/swift.tar.gz
