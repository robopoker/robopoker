import xml.etree.ElementTree as ET
import api

name, cards, actions, state = api.request()
state = ET.parse(state)

fear = False
for act in state.getroot().findall('./betting/round/action'):
    if act.get('type') in ('raise',):
        fear = True
        break

if fear:
    api.response('fold')
else:
    api.response(
        api.first_possible(
            ('check', 'call', 'allin'),
            actions
        )
    )
