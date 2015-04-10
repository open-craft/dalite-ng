// Modify the "add question" link in the assignment edit page to prepopulate the question title
// based on the title of the assignment.

(function($) {
    function updateAddLink(input) {
        var question_number = 0, title_regex, nodes, node, matches, title;
        if (!input.value) {
            // If this assignment doesn't have a title yet, there's not point in prepopulating the
            // question title.
            return;
        }
        title_regex = new RegExp('^' + input.value + 'Q(\\d+)$');
        // Extract all existing question titles from the two select boxes.
        nodes = SelectBox.cache['id_questions_from'].concat(SelectBox.cache['id_questions_to']);
        for (var i = 0; (node = nodes[i]); i++) {
            matches = node.text.match(title_regex);
            if (matches !== null) {
                question_number = Math.max(question_number, +matches[1]);
            }
        }
        // The next question number is one more than the highest number found.
        question_number += 1;
        title = input.value + 'Q' + question_number;
        $('#add_id_questions').get(0).search = '?_to_field=id&_popup=1&title=' + title;
    }
    $(function() {
        var $input = $('#id_identifier');
        $input.change(function(e) { updateAddLink(e.target); } );
        // We have to wait for the cache of the selectboxes to be populated.  This is kind of a
        // hack, since the delay is arbitrary.  It seems to work, though.
        setTimeout(function() { updateAddLink($input.get(0)); }, 250);
    });
})(django.jQuery);
