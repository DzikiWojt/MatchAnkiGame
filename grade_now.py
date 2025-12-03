from typing import Sequence

from anki.cards import CardId
from anki.scheduler.v3 import CardAnswer
from aqt.operations import CollectionOp
from aqt.qt import QWidget
from aqt.utils import tooltip, tr


def grade_now(
    *,
    parent: QWidget,
    card_ids: Sequence[CardId],
    ease: int,
) -> CollectionOp:
    if ease == 1:
        rating = CardAnswer.AGAIN
    elif ease == 2:
        rating = CardAnswer.HARD
    elif ease == 3:
        rating = CardAnswer.GOOD
    else:
        rating = CardAnswer.EASY
    return CollectionOp(
        parent,
        lambda col: col._backend.grade_now(
            card_ids=card_ids,
            rating=rating,
        ),
    ).success(
        lambda _: tooltip(
            tr.scheduling_graded_cards_done(cards=len(card_ids)), parent=parent
        )
    )
