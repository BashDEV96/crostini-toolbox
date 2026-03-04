<?php
/**
 * Snippet Name: Visual Term Description Editor (No Plugin)
 * Description: Enables the TinyMCE Visual Editor for Category and Tag descriptions.
 * It removes default WordPress filters that strip HTML and adds support 
 * for shortcodes and paragraphs.
 * Version: 1.0
 */

// 1. SETUP: Remove filters that strip HTML & add filters for formatting
function my_custom_editor_setup() {
    // Remove the "nanny" filters that strip HTML tags upon save/display
    remove_filter( 'pre_term_description', 'wp_filter_kses' );
    remove_filter( 'term_description', 'wp_kses_data' );

    // Add filters to ensure shortcodes work and paragraphs are formatted correctly
    add_filter( 'term_description', 'wptexturize' );
    add_filter( 'term_description', 'convert_smilies' );
    add_filter( 'term_description', 'convert_chars' );
    add_filter( 'term_description', 'wpautop' );
    add_filter( 'term_description', 'do_shortcode', 11 );
}
add_action( 'init', 'my_custom_editor_setup' );

// 2. RENDER: Replace the text box with the Visual Editor
function my_render_term_editor( $term ) {
    ?>
    <tr class="form-field term-description-wrap">
        <th scope="row"><label for="description">Description</label></th>
        <td>
            <?php
            $settings = array(
                'textarea_name' => 'description',
                'textarea_rows' => 10,
                'media_buttons' => true, // Allows adding images
            );
            
            // Decode existing HTML so it displays correctly inside the editor
            wp_editor( htmlspecialchars_decode( $term->description ), 'html-tag-description', $settings );
            ?>
            
            <script>
                // Hide the original plain text textarea so we don't have duplicate fields
                jQuery(document).ready(function($){
                    $('textarea#description').closest('.form-field').hide();
                });
            </script>
            
            <p class="description">Visual Editor Enabled. You can use full HTML and Shortcodes here.</p>
        </td>
    </tr>
    <?php
}

// Hook into the Edit screens for Categories and Tags
add_action( 'category_edit_form_fields', 'my_render_term_editor' );
add_action( 'post_tag_edit_form_fields', 'my_render_term_editor' );