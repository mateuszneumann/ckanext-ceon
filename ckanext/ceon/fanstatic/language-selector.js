$(function() {
    $(".language").on("click", function(e){
        e.preventDefault()
        var lang = '/'+$(this).attr('id')+'/'
        $( "#field-lang-select option:selected" ).prop("selected", false)
        if (lang == '/en_AU/') {
            var link = $('#field-lang-select option[value^="'+lang+'"]').prop("value").replace(lang, "/")
            $('#field-lang-select option[value^="'+lang+'"]').prop("selected", true).prop("value", link)
        } else {
            $('#field-lang-select option[value^="'+lang+'"]').prop("selected", true)
        }
        $('#language_form').submit()
    })
})
		
