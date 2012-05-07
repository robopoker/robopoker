RANKS = [None, None, '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']


def rate_hand(hand):
    """
    Hand format example:
        ['AS', 'TS', '9D', '2H', 'QC']
    Currently supports 5..7 card hands
    Returns tuple:
     - hand combination id:
         0      No-pair hand
         1      One pair
                Two cards of one rank plus garbage
         2      Two pair
                Two cards of the same rank, plus two cards of another rank, plus garbage
         3      Three of a Kind
                Three cards of the same rank plus garbage
         4      Straight
                Five cards of sequential rank in at least two different suits
         5      Flush
                Five cards of the same suit but not in sequence
         6      Full House
                Three cards of one rank and two cards of another rank
         7      Four of a kind
                Four cards of one rank plus garbage
         8      Straight flush
                Five cards of sequential rank and in the same suit
     - "kickers" array - for arguable situations
         Rating contains rank of "kickers" - cards,
         that solve conflicts with a combination.
         You may use it, when two players has the same
         combination. Kickers are sorted by its priority.
    """
    vals = hand_vals(hand)
    fl = flush(hand)
    if fl:
        str = straight(fl)
        if str:
            return 8, str
        fl.reverse()
        return 5, fl
    str = straight(vals)
    if str:
        return 4, str
    ck = count_kind(vals)
    if len(ck[4]):
        return 7, ck[4] + ck[1][:1]
    pair = ck[2]
    three = ck[3]
    if three and pair:
        return 6, [three[0], pair[0]]
    if three:
        return 3, [three[0]] + ck[1][:2]
    if len(pair) >= 2:
        return 2, pair + ck[1][:1]
    if pair:
        return 1, pair + ck[1][:3]
    return 0, ck[1][:5]


def cmp_rate(rate_x, rate_y):
    for i, kx in enumerate(rate_x):
        ky = rate_y[i]
        kick = cmp(kx, ky)
        if kick:
            return kick
    return 0


def hand_vals(hand):
    """
    Return sorted numeric values of cards in a hand
    """
    values = []
    for card in hand:
        val = RANKS.index(card[0])
        values.append(val)
    values.sort()
    return values


def count_kind(vals):
    """
    A somewhat crufty sorting method for poker.
    Inventor: http://charlesleifer.com/blog/robopoker-hand-evaluation-project-euler-54/
    """
    ck = {1: [], 2: [], 3: [], 4: []}
    for card in vals:
        added = False
        for i in range(3, 0, -1):
            if card in ck[i]:
                card_list = ck[i]
                idx = card_list.index(card)
                del(ck[i][idx])
                ck[i + 1].append(card)
                added = True
                break
        if not added:
            ck[1].append(card)
    for k, v in ck.items():
        v.sort()
        v.reverse()
    # correct for 5-card combinations (i.e., 2x3-of-a-kind or 3x2-of-a-kind)
    if len(ck[3]) > 1:
        ck[2].append(ck[3][-1])
        del(ck[3][-1])
    if len(ck[2]) > 2:
        ck[1].append(ck[2][-1])
        del(ck[2][-1])
    return ck


def flush(hand):
    suits = {'S': [], 'H': [], 'D': [], 'C': []}
    # index cards by suit
    for card in hand:
        suits[card[1]].append(card)
    fl = None
    for (s, cards) in suits.items():
        if (len(cards) >= 5):
            fl = cards
            break
    if not fl:
        return []
    # for >5 cards hands we need to use higher flush only
    vals = hand_vals(fl)
    return vals[-5:]


def straight(vals):
    vals = vals[:] # vals is mutable. copy.
    for x in range(len(vals), 4, -1):
        if vals[x - 1] == 14:
            vals.insert(0, 1) # simulate an ace at the beginning
    seq = 1
    last = len(vals) - 1
    # count sequential vals
    # trying to find longest sequence
    for i, x in enumerate(vals):
        next = None
        if last != i:
            next = vals[i + 1]
        if next == x + 1:
            seq += 1
        elif next != x:
            if seq >= 5:
                return [x]
            if not next:
                return []
            seq = 1


if __name__ == '__main__':
    import dictionary

    def test_rate(silent=False):
        fixture = [
            ['AS 2S 3S 4S 5S',       'sflush', [5]],
            ['2S 3S 4S 5S 6S',       'sflush', [6]],
            ['AS KS QS JS TS',       'sflush', [14]],
            ['AS AC 3S AD AH 2H 4D', 'quad',   [14, 4]],
            ['3D 3C 3S AD AH',       'full',   [3, 14]],
            ['AC 7S 6H AH 8H 2D AD', 'set',    [14, 8, 7]],
            ['AS 2S 3S TS QS',       'flush',  [14, 12, 10, 3,  2]],
            ['AD 2S 3S TS QS 5S',    'flush',  [12, 10, 5,  3,  2]],
            ['AS KS QD JS TS 5S',    'flush',  [14, 13, 11, 10, 5]],
            ['AS KS QD TS 5S 2S JS', 'flush',  [14, 13, 11, 10, 5]],
            ['AD 2S 3C 4S TS 5D',    'str',    [5]],
            ['2S 3S 4S 5S 6D',       'str',    [6]],
            ['2S 3S 4S 5S 6D 7D',    'str',    [7]],
            ['3D 3S 3H AS 4D QH 5H', 'set',    [3, 14, 12]],
            ['3D 3S AH AS 4D 6H',    'two',    [14, 3, 6]],
            ['3D 3S 5H AS 4D',       'pair',   [3, 14, 5, 4]],
            ['TD 2D 6D 8C JH 3H JC', 'pair',   [11, 10, 8, 6]],
            ['TD 2D 6D 8C JH 2S 7H', 'pair',   [2, 11, 10, 8]],
            ['3D QS 5H AS 4D',       'high',   [14, 12, 5, 4, 3]],
        ]
        for (hand, expected, kickers) in fixture:
            expected = dictionary.COMBINATION.index(expected)
            actual = rate_hand(hand.split())
            if not silent:
                print '%-20s %-6s %-6s %s' % (
                       hand, expected, actual[0] == expected and 'ok' or '!!! ' + str(actual[0]),
                       actual[1] != kickers and str(kickers) + ' !!! ' + str(actual[1]) or '')

    def test_cmp(silent=False):
        fixture = [
            [[20, 10, 5,  4],  [10, 12, 5, 4],  1],
            [[20, 10, 5,  4],  [20, 10, 5, 4],  0],
            [[20, 10, 5,  4],  [20, 12, 5, 4], -1],
            [[20, 10, 19, 4],  [20, 12, 5, 4], -1],
        ]
        for rate_x, rate_y, expected in fixture:
            actual = cmp_rate(rate_x, rate_y)
            if not silent:
                print '%-20s %-20s %s' % (
                    rate_x, rate_y,
                    'ok'
                    if expected == actual
                    else str(expected) + '!!!' + str(actual))

    test_rate()
    test_cmp()
