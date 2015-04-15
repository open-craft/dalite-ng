// This snippet makes sure that only rationales corresponding to the selected answer can be
// selected during question review.

$(function() {
    function setRadioButtonStatus(name, disabled) {
        // Disable or enable or radio buttons for the given name.
        $('input[type=radio][name=' + name + ']').each(function() {
            this.disabled = disabled;
            if (disabled) this.checked = false;
        });
    }

    // Disable all radio buttons until the user has chosen an answer.
    setRadioButtonStatus('rationale_choice_0', true);
    setRadioButtonStatus('rationale_choice_1', true);

    // Enable the right set of rationales when the user changes the selected answer.
    $('input[type=radio][name=second_answer_choice]').change(function() {
        var n, enable_name, disable_name;
        enable_name = this.id.replace('id_second_answer', 'rationale');
        n = enable_name.length - 1
        disable_name = enable_name.substr(0, n) + (enable_name[n] == '0' ? '1' : '0');
        setRadioButtonStatus(enable_name, false);
        setRadioButtonStatus(disable_name, true);
    });
});
