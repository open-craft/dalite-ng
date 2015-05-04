# -*- coding: utf-8 -*-
"""Selection algorithms for rationales shown during question review.

Each algorithm is a callable taking three arguments:

  rand_seed: A hashable object used to seed the random number generator.  Makes sure the same user
      gets consistent choices when reloading the page.

  first_answer_choice: The first choice of the student.

  entered_rationale: The rationale text entered by the student.

  question: The Question instance for the current question.

The callable must return a list of tuples (choice_index, choice_label, rationales), where
rationales is a list of pairs (rationale_id, rationale_text).

The callable must have an attribute 'version' with a version string for the algorithm.
"""
from __future__ import unicode_literals

import random
from django.utils.translation import ugettext_lazy as _
from . import models


def simple(rand_seed, first_answer_choice, entered_rationale, question):
    """Select the rationales to show to the user based on their answer choice.

    The two answer choices presented will include the answer the user chose.  If the user's answer
    wasn't correct, the second choice will be a correct answer.  If the user's answer wasn't
    correct, the second choice presented will be weighted by the number of available rationales,
    i.e. an answer that has only a few rationales available will have a low chance of being shown
    to the user.  Up to four rationales are presented to the user for each choice, if available.
    In addition, the user can choose to stick with their own rationale.
    """
    # Make the choice of rationales deterministic, so people can't see all rationales by
    # repeatedly reloading the page.
    rng = random.Random(rand_seed)
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
        random_rationale = other_rationales[rng.randrange(other_rationales.count())]
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
        rationales = rng.sample(rationales, min(4, rationales.count()))
        rationales = [(r.id, r.rationale) for r in rationales]
        chosen_choices.append((choice, label, rationales))
    # Include the rationale the student entered in the choices.
    chosen_choices[0][2].append((None, _('I stick with my own rationale.')))
    return chosen_choices

simple.version = "v1.1"
