$(function() {
	jQuery(".language").on("click", function(){
		jQuery('#language').val('/'+jQuery(this).attr('id')+'/'); 
		jQuery('#language_form').submit()
	})
})
		
