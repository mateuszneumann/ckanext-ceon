function changeSheet(target, section_link) {
	if($(target).hasClass("hidden")) {
		$(".sheet").addClass("hidden")
		$(target).removeClass("hidden")
		$(".section-link").removeClass("active")
		section_link.addClass("active")
	}
}

$(function(){
	$('.carousel').carousel()

	$(".section-link").click(function(){
		var target = $(this).attr('href')
		changeSheet(target, $(this))
	})

	$(".paragraph-title").click(function(){
		$(this).next(".paragraph").slideToggle()
	})

	$('a[href=""]').click(function(e){
		e.preventDefault()
	})

	if(window.location.hash) {
		var target = window.location.hash
		changeSheet(target, $('a[href="'+target+'"]'))
	}
	else {
		changeSheet("#sheet_1", $('a[href="#sheet_1"]'))
	}
})
