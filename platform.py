#!/usr/bin/env python
"""
Create hand mode:
    Usage: <INPUT> | python platform.py create_hand > initial_hand_state.xml

    Creates "initial-hand-state" xml file from scratch.
    File contains minimal state (table+deck) in the internal format.
    Later it may be used as input for play hand mode.
    <INPUT> format:
    # it is a comment
    <sit><b?> <name>   <stack>   <type>   <service>\n for each player

Play hand mode:
    Usage: cat/type initial_hand_state.xml | python platform.py play_hand \
           1> result_hand_state.xml 2> croupier.log

    Perform robopoker play from the initial hand state to the awarding.

Publish state mode:
    Usage cat/type private.xml | python platform.py publish_state > public.xml
"""
import sys
import re

from robopoker.entities import Table, Deck, Player
from robopoker import transport
from robopoker.croupier import Croupier
from robopoker.handstate.interface import HandState
import robopoker.handstate.representation as handstate_repr


class Controller(object):

    def do_create_hand(self):
        def create_players():
            players = []
            button = None
            for line in sys.stdin:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                data = re.split(r'\s+', line, 4)
                sit = str(data[0])
                if sit.endswith('b'):
                    sit = sit[:-1]
                    button = int(sit)
                players.append(
                    (int(sit),
                        Player(data[1],
                            transport.create(data[3], data[4]), data[2])))
            return players, button

        def create_state(players, button):
            table = Table()
            deck = Deck()
            deck.shuffle()
            for (sit, player) in players:
                table.sit_in(player, sit)
            if button is None:
                table.rotate_button()
            else:
                table.button = button
            return HandState(table, deck)

        dest = sys.stdout
        players, button = create_players()
        state = create_state(players, button)
        dest.write(handstate_repr.dump(state, False))

    def do_play_hand(self):
        source = sys.stdin
        dest = sys.stdout
        state = handstate_repr.parse(source)
        croupier = Croupier(state, sys.stderr)
        croupier.conduct()
        dump = handstate_repr.dump(state, False)
        print >> dest, dump,

    def do_publish_state(self):
        player = None
        if len(sys.argv) > 2:
            player = sys.argv[2]
        source = sys.stdin
        dest = sys.stdout
        dest.write(handstate_repr.echo(
            handstate_repr.to_public(handstate_repr.open(source), player)
        ))


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print __doc__
        sys.exit(1)
    mode = 'do_' + sys.argv[1]
    ctrl = Controller()
    if mode not in dir(ctrl):
        sys.exit(1)
    clb = getattr(ctrl, mode)
    sys.exit(clb() if callable(clb) else 1)
