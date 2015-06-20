$(function(){
	$('.carousel').carousel()

	$(".section-link").click(function(){
		var target = $(this).attr('href')
		console.log(target, !($(target).is(":visible")))
		if($(target).hasClass("hidden")) {
			$(".sheet").addClass("hidden")
			$(target).removeClass("hidden")
			$(".section-link").removeClass("active")
			$(this).addClass("active")
		}
	})

	$(".paragraph-title").click(function(){
		$(this).next(".paragraph").slideToggle()
	})

	$('a[href=""]').click(function(e){
		e.preventDefault()
	})

	if(window.location.hash) {
		$('a[href="'+window.location.hash+'"]').click()
	}
	else {
		$('a[href="#sheet_1"]').click()
	}
})
