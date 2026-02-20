# ForgeKeeper Language Module: .NET / C#
RUN wget https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y dotnet-sdk-8.0 dotnet-sdk-7.0 aspnetcore-runtime-8.0 \
    && rm -rf /var/lib/apt/lists/*
