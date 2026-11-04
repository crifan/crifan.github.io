require(["gitbook", "jQuery"], function(gitbook, $) {
    gitbook.events.bind('start', function (e, config) {

        var conf = config['toolbar-button'];
        var label = conf.label;
        var icon = conf.icon;
        var url = conf.url;

        gitbook.toolbar.createButton({
            icon: 'fa ' + (icon || 'fa fa-edit'),
            text: label,
            onClick: function() {
                window.open(url);
            }
        });
    });

});