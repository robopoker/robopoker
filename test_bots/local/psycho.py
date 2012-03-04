import random
import api

name, cards, actions, state = api.request()
api.response(random.choice(actions))
