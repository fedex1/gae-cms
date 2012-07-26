/* Vertical menu needs work, currently not functional */

YUI().use("node-menunav", function(Y) {

	Y.all('.nav-dropdown-v').each(function(i) {

	    Y.on('contentready', function () {

	        this.plug(Y.Plugin.NodeMenuNav);

	        this.get("ownerDocument").get("documentElement").removeClass("yui3-loading");

	    }, "#" + i.get('id'));

	});

});