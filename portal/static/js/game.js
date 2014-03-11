function update_game(update) {
	if (update.update) {
		$("#players").html(update.players);
		$("#playfield-container").html(update.playfield);
		$("#extra-info").html(update.extra_info);
		$("#messages").html(update.messages);
	}
}