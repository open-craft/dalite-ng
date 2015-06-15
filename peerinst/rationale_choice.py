# -*- coding: utf-8 -*-
"""Selection algorithms for rationales shown during question review.

Each algorithm is a callable taking these arguments:

  rng: The random number generator to use.

  first_answer_choice: The first choice of the student.

  entered_rationale: The rationale text entered by the student.

  question: The Question instance for the current question.

The callable must return a list of tuples (choice_index, choice_label, rationales), where
rationales is a list of pairs (rationale_id, rationale_text).

The callable must have the following attributes:

  version: A version string for the algorithm.

  verbose_name: A human-readable short name for use in the admin interface.

  description: A long description explaining how the algorithm chooses rationales.

To make an algorithm available to users, make sure to add it to the "algorithms" dictionary
at the end of this file.
"""
from __future__ import unicode_literals

from django.db.models import Count, Max
from django.utils.translation import ugettext_lazy as _


class RationaleSelectionError(Exception):
    """Raised when an error occurs during rationale selection.

    The message attached to this exception will be shown to the user.
    """


def _base_selection_algorithm(
        rng, first_answer_choice, unused_entered_rationale, question, selection_callback
    ):
    """Select the rationales at random."""
    from . import models  # Local import to avoid circular dependency
    first_choice = first_answer_choice
    answer_choices = question.answerchoice_set.all()
    # Find all public rationales for this question.
    all_rationales = models.Answer.objects.filter(question=question, show_to_others=True)
    # Select a second answer to offer at random.  If the user's answer wasn't correct, the
    # second answer choice offered must be correct.
    if answer_choices[first_choice - 1].correct:
        # We must make sure that rationales for the second answer exist.  The choice is
        # weighted by the number of rationales available.
        other_rationales = all_rationales.exclude(first_answer_choice=first_choice)
        # We don't use rng.choice() to avoid fetching all rationales from the database.
        try:
            random_rationale = other_rationales[rng.randrange(other_rationales.count())]
        except ValueError:
            raise RationaleSelectionError(
                _("Can't proceed since the course staff did not provide example answers.")
            )
        second_choice = random_rationale.first_answer_choice
    else:
        # Select a random correct answer.  We assume that a correct answer exists.
        second_choice = rng.choice(
            [i for i, choice in enumerate(answer_choices, 1) if choice.correct]
        )
    chosen_choices = []
    for choice in [first_choice, second_choice]:
        label = question.get_choice_label(choice)
        # Get all rationales for the current choice.
        rationales = all_rationales.filter(first_answer_choice=choice)
        # Select up to four rationales for each choice, if available.
        rationales = selection_callback(rng, rationales)
        rationales = [(r.id, r.rationale) for r in rationales]
        chosen_choices.append((choice, label, rationales))
    # Include the rationale the student entered in the choices.
    chosen_choices[0][2].append((None, _('I stick with my own rationale.')))
    return chosen_choices


def simple(rng, first_answer_choice, entered_rationale, question):

    def callback(rng, rationales):
        return rng.sample(rationales, min(4, rationales.count()))

    return _base_selection_algorithm(
        rng, first_answer_choice, entered_rationale, question, callback
    )

simple.version = "v1.1"
simple.verbose_name = _("Simple random rationale selection")
simple.description = _(
    """The two answer choices presented will include the answer the user chose.  If the user's
    answer wasn't correct, the second choice will be a correct answer.  If the user's answer was
    correct, the second choice presented will be weighted by the number of available rationales,
    i.e. an answer that has only a few rationales available will have a low chance of being shown
    to the user.  Up to four rationales are presented to the user for each choice, if available.
    In addition, the user can choose to stick with their own rationale.
    """
)


def prefer_expert_and_highly_voted(rng, first_answer_choice, entered_rationale, question):

    def callback(rng, rationales):
        chosen = []

        # Add an expert rationale if one exists.
        expert_rationales = rationales.filter(expert=True)
        if expert_rationales:
            chosen.append(rng.choice(expert_rationales))
            rationales = rationales.exclude(pk=chosen[-1].pk)

        # Add a highly voted rationale if one exists.
        rationales_with_votes = rationales.annotate(votes=Count('answer'))
        max_votes = rationales_with_votes.aggregate(Max('votes'))['votes__max']
        highly_voted_rationales = rationales_with_votes.filter(votes__gt=max_votes // 2)
        if highly_voted_rationales:
            chosen.append(rng.choice(highly_voted_rationales))
            rationales = rationales.exclude(pk=chosen[-1].pk)

        # Fill up with random other rationales
        chosen.extend(rng.sample(rationales, min(4 - len(chosen), rationales.count())))
        rng.shuffle(chosen)
        return chosen

    return _base_selection_algorithm(
        rng, first_answer_choice, entered_rationale, question, callback
    )

prefer_expert_and_highly_voted.version = "v1.0"
prefer_expert_and_highly_voted.verbose_name = _("Prefer expert and highly votes rationales")
prefer_expert_and_highly_voted.description = _(
    """The two answer choices presented will include the answer the user chose.  If the user's
    answer wasn't correct, the second choice will be a correct answer.  If the user's answer was
    correct, the second choice presented will be weighted by the number of available rationales,
    i.e. an answer that has only a few rationales available will have a low chance of being shown
    to the user.  Up to four rationales are presented to the user for each choice, if available.
    In addition, the user can choose to stick with their own rationale.

    The four rationales will include at least one "expert" rationale, if available, and at least
    one rationale with more than half the maximum number of votes, if available.
    """
)


# The dictionary of all algorithms users can choose from.
algorithms = {
    'simple': simple,
    'prefer_expert_and_highly_voted': prefer_expert_and_highly_voted,
}


def algorithm_choices():
    """Return a list of algorithms to choose from in the user interface.

    The choices are in a format suitable to be used as the "choices" parameter of a model
    field, i.e. pairs of the form (value, human-readable value).
    """
    return [(name, fn.verbose_name) for name, fn in algorithms.viewitems()]
