$(function() {
    // Select the right parent option if the user selects a rationale directly.
    $('input[type=radio][name=rationale_choice_0], input[type=radio][name=rationale_choice_1]').click(function() {
        var radio = $(this);
        if (radio.is(':checked')) {
            $('input[type=radio]').not('input[name="' + radio.prop('name') + '"]').attr('checked', false);
            radio.parents('.rationale').find('input[type=radio][name=second_answer_choice]').click();
        }
    });
});
