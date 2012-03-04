import sys

def request():
    def rl():
        line = sys.stdin.readline()
        return line.strip()
    name = rl()
    cards = rl()
    rl()
    actions = []
    while True:
        act = rl()
        if not act: break
        actions.append(act)
    return name, cards, actions, sys.stdin

def response(s):
    print s
    sys.stdout.flush()

def first_possible(actions, allowed):
    for v in actions:
        if v in allowed:
            return v
    raise Exception('%s not in %s' % (actions, allowed))
