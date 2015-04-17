// This snippet makes sure that only rationales corresponding to the selected answer can be
// selected during question review.

$(function() {
    function setRadioButtonStatus(index) {
        // Disable or enable the radio buttons for the set of rationales with the given index.
        var disabled = !$('#id_second_answer_choice_' + index).get(0).checked;
        $('input[type=radio][name=rationale_choice_' + index + ']').each(function() {
            this.disabled = disabled;
            if (disabled) this.checked = false;
        });
    }

    // Disable all radio buttons until the user has chosen an answer.
    setRadioButtonStatus(0);
    setRadioButtonStatus(1);

    // Enable the right set of rationales when the user changes the selected answer.
    $('input[type=radio][name=second_answer_choice]').change(function() {
        setRadioButtonStatus(0);
        setRadioButtonStatus(1);
    });
});
