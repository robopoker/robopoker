COMBINATION = [
    'high',
    'pair',
    'two',
    'set',
    'str',
    'flush',
    'full',
    'quad',
    'sflush'
]

RANK_NAME = {
    'A': 'Ace',
    'K': 'King',
    'Q': 'Queen',
    'J': 'Jack',
    'T': 'Ten',
    '9': 'Nine',
    '8': 'Eight',
    '7': 'Seven',
    '6': 'Six',
    '5': 'Five',
    '4': 'Four',
    '3': 'Trey',
    '2': 'Deuce'
}

SUIT_NAME = {
    'S': 'Spades',
    'H': 'Hearts',
    'D': 'Diamonds',
    'C': 'Clubs'
}

COMBINATION_NAME = {
    'high':   'Garbage',
    'pair':   'Pair',
    'two':    'Two Pair',
    'set':    'Three of a Kind',
    'str':    'Straight',
    'flush':  'Flush',
    'full':   'Full House',
    'quad':   'Four of a Kind',
    'sflush': 'Straight Flush'
}


def describe_combination(cardset, base, kickers):
    # TODO: return something like "Straight, Ace High"
    return COMBINATION_NAME[COMBINATION[base]]
