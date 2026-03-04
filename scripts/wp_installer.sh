#!/bin/bash
# Chromebook Underground - Plain Jane WordPress Installer
# Tested on Debian-based Crostini
set -e

# --- CONFIGURATION ---
# Change this version number (e.g., to 8.4) to update PHP.
# This variable locks the Core and Extensions to the same version to prevent mismatch errors.
PHP_VER="8.3"
DB_NAME="wordpress"
DB_USER="wp_user"
DB_PASS="wp_pass"
ADMIN_USER="admin"
ADMIN_PASS="admin"
ADMIN_EMAIL="admin@example.com"
# ---------------------

echo "Updating and preparing system..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y lsb-release apt-transport-https ca-certificates

echo "Adding Ondrej Sury PHP repository..."
sudo wget -O /etc/apt/trusted.gpg.d/php.gpg https://packages.sury.org/php/apt.gpg
echo "deb https://packages.sury.org/php/ $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/php.list > /dev/null
sudo apt update

echo "Installing dependencies (PHP $PHP_VER)..."
# CHANGED: Explicitly using $PHP_VER to ensure Core and Modules match
sudo apt install -y apache2 mariadb-server \
  php${PHP_VER} \
  libapache2-mod-php${PHP_VER} \
  php${PHP_VER}-mysql \
  php${PHP_VER}-curl \
  php${PHP_VER}-gd \
  php${PHP_VER}-mbstring \
  php${PHP_VER}-xml \
  php${PHP_VER}-zip \
  php${PHP_VER}-intl \
  php${PHP_VER}-imagick \
  curl unzip chromium

echo "Configuring Apache..."
# Enable mod_rewrite
sudo a2enmod rewrite

# Add AllowOverride All to the WordPress directory in the default Apache conf
sudo sed -i '/<VirtualHost \*:80>/a\\n<Directory /var/www/html/wordpress>\n AllowOverride All\n</Directory>\n' /etc/apache2/sites-available/000-default.conf

echo "Starting services..."
sudo systemctl enable apache2 mariadb
sudo systemctl restart apache2 mariadb

echo "Setting up MariaDB..."
sudo mysql -u root -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME};"
sudo mysql -u root -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';"
sudo mysql -u root -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
sudo mysql -u root -e "FLUSH PRIVILEGES;"

echo "Installing WP-CLI..."
# Added a check to remove existing wp-cli if running script multiple times
if [ -f /usr/local/bin/wp ]; then
    sudo rm /usr/local/bin/wp
fi
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
chmod +x wp-cli.phar
sudo mv wp-cli.phar /usr/local/bin/wp

echo "Setting up WordPress..."
sudo mkdir -p /var/www/html/wordpress
cd /var/www/html/wordpress

# Clean directory if it exists to prevent download errors
if [ -f wp-config.php ]; then
    echo "Existing WordPress installation found. Skipping download..."
else
    sudo wp core download --allow-root
    sudo wp config create --dbname=${DB_NAME} --dbuser=${DB_USER} --dbpass=${DB_PASS} --allow-root
    sudo wp core install --url="http://localhost/wordpress" --title="Local WP" --admin_user=${ADMIN_USER} --admin_password=${ADMIN_PASS} --admin_email=${ADMIN_EMAIL} --skip-email --allow-root
fi

echo "Fixing permissions..."
sudo chown -R www-data:www-data /var/www/html/wordpress
sudo chmod -R 755 /var/www/html/wordpress

echo "Restarting Apache..."
sudo systemctl restart apache2

echo "Done! Open Chromium and go to http://localhost/wordpress/wp-admin"
echo "Username: ${ADMIN_USER}"
echo "Password: ${ADMIN_PASS}"