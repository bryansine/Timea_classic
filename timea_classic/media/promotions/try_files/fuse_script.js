jQuery(document).ready(function($) {
     $(".fuse_social_icons_links").click(function(){
        // This does the ajax request
        $.post({
            url: fuse_social.ajax_url, // or example_ajax_obj.ajaxurl if using on frontend
            data: {
                'action': 'fuse_social_update_analytics',
                'connect' : $(this).attr('data-title'),
                'nonce' : $(this).attr('data-nonce')
            },
            success:function(data) {
                // This outputs the result of the ajax request
                console.log(data);
            },
            error: function(errorThrown){
                console.log(errorThrown);
            }
        });  

    });
});