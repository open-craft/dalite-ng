$(function() {
    var all_rationale_inputs = $('.rationale-text-container input[type=radio]')
    // Clear the rationale selection if the user changes answers
    $('input[type=radio][name=second_answer_choice]').click(function () {
        var radio = $(this);
        var rationale_id = radio.parents('.rationale').attr('id');
        all_rationale_inputs.each(function () {
            var sub_radio = $(this);
            if (! (sub_radio.parents('.rationale').attr('id') == rationale_id)) {
                sub_radio.attr('checked', false);
            }
        })
    });
    // Select the right parent option if the user selects a rationale directly.
    all_rationale_inputs.click(function() {
        var radio = $(this);
        $('input[type=radio]').not('input[name="' + radio.prop('name') + '"]').attr('checked', false);
        radio.parents('.rationale').find('input[type=radio][name=second_answer_choice]').click();
    });
});
