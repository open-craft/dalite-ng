(function($) {
    function updateAddLink(input) {
        console.log(input.value);
        $('#add_id_questions').get(0).search = '?_to_field=title&_popup=1&title=' + input.value;
    }
    $(function() {
        var $input = $('#id_identifier');
        $input.change(function(e) { updateAddLink(e.target); } );
        updateAddLink($input.get(0));
    });
})(django.jQuery);
