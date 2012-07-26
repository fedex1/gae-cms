YUI().use('tabview', function(Y) {

	Y.all('.text.default.tabs').each(function(i) {

		new Y.TabView({ srcNode: "#" + i.get('id') }).render();

	}).setStyle('visibility','visible');

});