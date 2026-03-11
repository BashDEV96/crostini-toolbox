<?php
/**
 * Plugin Name: Localhost Application Passwords Enabler
 * Description: Forces the Application Passwords feature to be available, bypassing the HTTPS check.
 * Author: Gemini AI
 * Version: 1.0
 */

// Only enable on localhost or development environments for security
$site_url = get_site_url();
if ( strpos( $site_url, 'localhost' ) !== false || strpos( $site_url, '127.0.0.1' ) !== false || defined( 'WP_DEBUG' ) && WP_DEBUG ) {
    add_filter( 'wp_is_application_passwords_available', '__return_true' );
}