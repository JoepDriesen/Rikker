function update_game(update) {
	location.reload();
}

$(function() {
	$("#picking-form select").change(function() {
		$(this).removeClass('suit-0 suit-1 suit-2 suit-3 suit-4');
		$(this).addClass('suit-' + $(this).val());
	})
})