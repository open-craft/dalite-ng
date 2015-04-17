(function ($) {
    $(function () {
        $.get('/static/peerinst/templates/media_buttons.handlebars', {}, function (data) {
            var template = Handlebars.compile(data);
            $('#id_text').after(template());
        });
    });
})(django.jQuery);