<?php
/**
 * Plugin Name: Localhost Application Passwords Enabler
 * Description: Forces the Application Passwords feature to be available, bypassing the HTTPS check.
 * Author: Gemini AI
 */

add_filter( 'wp_is_application_passwords_available', '__return_true' );