$(function() {
	$(".language").on("click", function(e){
		e.preventDefault()
		var lang = '/'+$(this).attr('id')+'/'
		$( "#field-lang-select option:selected" ).prop("selected", false)
		$('#field-lang-select option[value^="'+lang+'"]').prop("selected", true)
		$('#language_form').submit()
	})
})
		
