$(function() {
	$(".language").on("click", function(e){
		e.preventDefault()
		var value = '/'+jQuery(this).attr('id')+'/'
		$('#field-lang-select').val(value); 
		$('#language_form').submit()
	})
})
		
