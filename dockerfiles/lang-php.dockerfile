# ForgeKeeper Language Module: PHP + Composer
# php-cli and extensions are in the base apt block; this adds Composer
RUN curl -fsSL https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
