import api

name, cards, actions, state = api.request()
api.response(
    api.first_possible(
        ('check', 'call', 'allin'),
        actions
    )
)
