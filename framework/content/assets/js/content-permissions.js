YUI().use("node-menunav", function(Y) {

	Y.all('.content-permissions').each(function(i) {

	    Y.on('contentready', function () {

	        this.plug(Y.Plugin.NodeMenuNav, { autoSubmenuDisplay: false, mouseOutHideDelay: 0 });

	    	this.all('.yui3-menu').setStyle('visibility','visible');

	    }, "#" + i.get('id'));

	}).setStyle('visibility','visible');

});