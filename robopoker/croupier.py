from __future__ import absolute_import

import sys
import re
from math import floor
from operator import attrgetter

from .entities import CardSet
from . import dictionary
from . import transport
from .handstate.representation import dump as dump_handstate

class Croupier(object):

    def __init__(self, state, log):
        self.state = state
        self.log_file = log
        self.pots = [0]
        self.structure = (
            ('preflop', 0, 20),
            ('flop',    3, 20),
            ('turn',    1, 40),
            ('river',   1, 40),
        )
        self.posts = (
            ('small_blind', 0.5),
            ('big_blind',   1)
        )

    def conduct(self):
        self.deal_pockets()
        for i, (round, draw, bet) in enumerate(self.structure):
            self._log('%-10s  ' % str(round).upper(), False)
            if draw:
                self.deal_community(draw)
            self._log()
            posts = ()
            if not i and self.posts:
                posts = self.posts
            pots = self.betting_round(round, min_bet=bet, posts=posts)
            self.pots = self.pots[:-1] + [self.pots[-1] + pots[0]] + pots[1:]
            self._log(('POTS', self.pots))
        self._log('SHOWDOWN')
        # Folded players forfeit all pots
        contenders = [p for p in self.state.table.players() if not p.folded]
        # Clean last opened pot if it is empty
        if not self.pots[-1]:
            del self.pots[-1]
        self.showdown(contenders)
        for player in contenders:
            if player.win or player.hand:
                self.state.add_showdown(
                    player, player.hand and player.pocket or None)
            if player.win:
                player.stack += player.win
        self.log_winners()

    def deal_pockets(self):
        self._log('DEAL')
        players = self.state.table.players()
        for card in range(0, 2):
            for p in players:
                p.pocket.add(self.state.deck.draw())
        for p in players:
            self._log('  %-10s %s' % (p.name, p.pocket))

    def deal_community(self, count=1):
        self.state.deck.draw()
        for deal in range(0, count):
            draw = self.state.deck.draw()
            self.state.community.append(draw)
            self._log(draw, False)

    def parse_response(self, r):
        r = str(r).strip()
        if not re.match('fold|check|call|bet|raise|allin', r):
            return None
        return r

    def betting_round(self, round, min_bet, posts):
        """
        Plays one full betting round.
        Optional process live blind posts.
        Returns pot.
        """
        full_loops = 0
        cur_bet = 0
        players = self.state.table.players()
        while True:
            # We must reiterate over the players
            # while round is opened
            for position, player in enumerate(players):
                # At the first iteration
                # we have to collect posts
                if not full_loops and posts:
                    # But maybe all posts for this game
                    # are already collected
                    if len(posts) > position:
                        post, factor = posts[position]
                        amount = blind_amount = int(factor * min_bet)
                        if amount >= player.stack:
                            amount = player.stack
                            player.allin = True
                            player.bet = amount
                        else:
                            # Post does not go directly to the bet stack.
                            # Player must be allowed to check or raise his post
                            # later at his turn, even if all other players call it
                            player.blind = amount
                        player.stack -= amount
                        # But it is "live" bet for other players
                        cur_bet = blind_amount
                        self.log_act(player, post)
                        self.state.add_post(player, amount, post)
                        continue
                # After the first iteration
                # we have to check that round not closed
                if self.round_closed(players, cur_bet):
                    return self.collect_pots(players)
                # Folded or all-in player not really in game.
                # Just skip him
                if player.folded or player.allin:
                    continue
                # Ok. Now player must act.
                # Lets check out what kinds of action are possible...
                # TODO: determine possible amounts for each act
                possible = self.possible_actions(player, players, cur_bet, min_bet)
                error = None
                try:
                    response = player.message(possible.keys(), dump_handstate(self.state))
                except transport.Error as e:
                    error = (str(e), 'transport')
                    self._log('ERROR: transport error ' + str(e))
                    response = 'fold'
                act = self.parse_response(response)
                # Now, act is just a keyword like "call" or "fold".
                if act is None:
                    error = (response, 'impl')
                    self._log('ERROR: impl error ' + response)
                    act = 'fold'
                elif act not in possible:
                    # Not allowed actions immediately treats as fold.
                    # TODO: check for bet amount
                    error = (act, 'logic')
                    self._log('ERROR: %s is not allowed' % act)
                    act = 'fold'
                # Fold action works just like any other
                # with the exception, that player forfeit the game and pot
                if act == 'fold':
                    player.folded = True
                # Currently action amount is just one that possible
                # TODO: not-so-limit game, where player may determine amount of his bet
                amount = possible[act]
                extra = amount - (player.bet or 0) - player.blind
                assert extra >= 0
                # Maybe it is all-in
                if extra >= player.stack:
                    self._log('WARNING: unexpected allin')
                    extra = player.stack
                    amount = player.blind + (player.bet or 0) + extra
                    player.allin = True
                    act = 'allin'
                player.stack -= extra
                player.bet = amount
                if amount > cur_bet:
                    cur_bet = amount
                # Ok, player check or bet his blind post.
                # Now it is bet
                player.blind = 0
                self.log_act(player, act)
                self.state.add_action(round, player, act, amount, error)
            # Loop is done
            # Reiterating...
            full_loops += 1

    def round_closed(self, players, cur_bet):
        # Collect active players
        pot_contenders = [pl for pl in players if not pl.folded]
        active = [pl for pl in pot_contenders if not pl.allin]
        count = len(active)
        check_bets_equal = count > 1
        if count == 1:
            # Only one player remains.
            # But if all others are allin, he must be able
            # to call bet of the richest allin or fold
            allins = [pl for pl in pot_contenders if pl.allin]
            last = active[0]
            if len(pot_contenders) - len(allins) == 1 and cur_bet:
                if last.blind >= cur_bet:
                    last.bet = last.blind
                    last.blind = 0
                    return True
                check_bets_equal = True
        if check_bets_equal:
            # We have some active players
            for player in active:
                # Player.bet is nullable!
                # At the end of round all bets must be real and equal
                if player.bet != cur_bet:
                    return False
        return True

    def possible_actions(self, player, players, cur_bet, min_bet):
        if player.blind and player.blind == cur_bet:
            # We are here if all players
            # just call the Blind post or fold.
            # Blind player has an option
            # to check his post or raise it
            r = {'check': player.blind, 'raise': player.blind + min_bet}
        elif cur_bet:
            r = {'call': cur_bet}
            if len([pl for pl in players if not pl.allin and not pl.folded]) > 1:
                if cur_bet + min_bet <= min_bet * 4:
                    r['raise'] = cur_bet + min_bet
        else:
            r = {'check': 0, 'bet': min_bet}
        # Player may fold any time.
        # Action amount equals to chips
        # that already on the table
        r['fold'] = player.blind + (player.bet or 0)
        return r

    def collect_pots(self, players):
        cur_pot = 0  # Current active main or side pot
        pots = []    # When we open the side pot, main goes here
        # We sort players by bet to simplify all-in processing
        players.sort(lambda a, b: cmp(a.bet, b.bet))
        for i, pl in enumerate(players):
            # When player goes allin
            # we must fill main pot from rich players
            # and create the side pot
            if pl.allin and pl.bet:
                # All-in player may not win
                # more money that he invest
                max = pl.bet
                for depositor in players[i:]:
                    # Part of depositor's bet
                    # goes to main pot
                    cur_pot += max
                    depositor.bet -= max
                # Main pot filled.
                # Detach it and open new
                pots.append(cur_pot)
                cur_pot = 0
            # Any way players bet goes
            # to the active pot
            cur_pot += pl.bet or 0
            # Null the bet to prepare
            # for the next betting round
            pl.bet = None
        return pots + [cur_pot]

    def showdown(self, contenders):
        # TODO: Use more sets ;)
        # TODO: Contenders must be sorted by initial stack size and than
        #       by aggressiveness
        contenders.sort(key=attrgetter('initial_stack'))
        # If players has equal initial stack
        # than they are fight for the same pot (AM I RIGHT?)
        by_stack = [[contenders[0]]]
        for player in contenders[1:]:
            last_group = by_stack[-1]
            rich = player.initial_stack > last_group[0].initial_stack
            if (player.allin and rich or
                    not player.allin and last_group[0].allin):
                # start new group
                by_stack.append([player])
            else:
                last_group.append(player)
        # Regroup by pot
        by_pot = {}
        pots = self.pots[:]
        last_pot = None
        while True:
            if not pots:
                break
            last_pot = pots.pop()
            by_pot[last_pot] = by_stack.pop()
        for group in by_stack:
            # Richest players goes to the last group
            by_pot[last_pot].extend(group)

        for pot in reversed(self.pots):
            by_pot[pot] = self.determine_winners(by_pot[pot])

        absolute_winners = self.determine_winners(contenders)

        senior_winners = set()  # absolute winners of the senior pot
        pots_closing_index = None  # reversed index of last side pot with known winner
        for i, pot in enumerate(reversed(self.pots)):
            pot_winners = by_pot[pot]
            absolute_pot_winners = ((set(pot_winners) & set(absolute_winners)) |
                                                                senior_winners)
            if absolute_pot_winners:
                if pots_closing_index is None:
                    pots_closing_index = i
                senior_winners |= absolute_pot_winners
                amount = int(floor(pot / len(absolute_pot_winners)))
                for winner in absolute_pot_winners:
                    winner.win += amount
        # Now we have to drop already processed pots
        del self.pots[:len(self.pots) - pots_closing_index]
        if self.pots:
            # We are here, if the winner of some side pots
            # not found. Cleanup contenders and retry (yes, recursively)
            contenders = [p for p in contenders if p not in absolute_winners]
            self.showdown(contenders)

    def determine_winners(self, contenders):
        if len(contenders) == 1:
            return contenders
        aggressor = contenders[0]
        aggressor.hand = self.player_hand(aggressor)
        winners = [aggressor]
        winner_hand = aggressor.hand
        for player in contenders[1:]:
            player.hand = self.player_hand(player)
            if winner_hand < player.hand:
                winners, winner_hand = [player], player.hand
            elif winner_hand == player.hand:
                winners.append(player)
        return winners

    def player_hand(self, player):
        hand = CardSet(self.state.community + player.pocket.cards)
        hand.rate()
        return hand

    def log_act(self, player, act):
        name_stack = '%s[%d]' % (player.name, player.stack)
        self._log('  %-10s %s[%d]' %
                (name_stack, act, (player.bet or 0) + player.blind))
        sys.stdout.flush()

    def log_winners(self):
        winners = [p for p in self.state.table.players() if p.win]
        assert winners
        for winner in winners:
            inf = [winner.name, 'wins', winner.win]
            if winner.hand:
                combination = dictionary.describe_combination(
                    winner.hand.cards, winner.hand.base, winner.hand.kickers)
                inf.extend(['with', combination, winner.hand.cards])
            self._log(inf)

    def _log(self, s='', nl=True):
        if getattr(s, '__iter__', False):
            s = ' '.join([str(f) for f in s])
        if nl:
            s += '\n'
        self.log_file.write(str(s))
