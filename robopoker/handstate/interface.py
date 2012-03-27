class HandState(object):

    def __init__(self, table, deck):
        self.table = table
        self.deck = deck
        self.community = []
        self.posts = []
        self.betting = {'preflop': [], 'flop': [], 'turn': [], 'river': []}
        self.showdown = []

    def add_post(self, player, amount, type):
        self.posts.append({
            'player': player.name,
            'amount': amount,
            'type': type
        })

    def add_action(self, round, player, type, amount=0, error=None):
        data = {
            'player': player.name,
            'type': type,
            'amount': amount,
            'error': error
        }
        self.betting[round].append(data)

    def add_showdown(self, player, hand):
        self.showdown.append({
            'player': player.name,
            'win': player.win,
            'hand': hand
        })
