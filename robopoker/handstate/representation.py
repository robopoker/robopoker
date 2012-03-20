import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from StringIO import StringIO
from robopoker.entities import *
import robopoker.transport as transport
import interface

__all__ = ['dump', 'open', 'parse', 'echo', 'to_public']

def dump(state, public=True, pretty=True):
    root = ET.Element('game')
    appendNotEmpty(root, dump_table(state.table))
    appendNotEmpty(root, dump_posts(state.posts))
    appendNotEmpty(root, dump_betting(state.betting))
    appendNotEmpty(root, dump_community(state.community))
    if state.showdown:
        appendNotEmpty(root, dump_showdown(state.showdown))
    if not public:
        appendNotEmpty(root, dump_deck(state.deck))
    if public:
        root = to_public(root)
    return echo(root, pretty)

def echo(root, pretty=True):
    s = StringIO()
    ET.ElementTree(root).write(s)
    if pretty:
        xml = minidom.parseString(s.getvalue())
        return xml.toprettyxml()
    return s.getvalue()

def to_public(root, player=None):
    players = root.findall('table/player')
    for p in players:
        p.remove(p.find('pocket'))
        p.remove(p.find('transport'))
    deck = root.find('deck')
    if deck is not None:
        root.remove(deck)
    acts = root.findall('betting/round/action')
    for a in acts:
        w = a.find('error')
        if w is None:
            continue
        if not player or a.get('player') != player:
            a.remove(w)
    return root

def dump_posts(posts):
    if not posts:
        return
    root = ET.Element('posts')
    for post in posts:
        attrs = {'player': post['player'], 'amount': str(post['amount']), 'type': post['type']}
        ET.SubElement(root, 'post', attrs)
    return root

def dump_betting(betting):
    root = ET.Element('betting')
    for round in ('preflop', 'flop', 'turn', 'river'):
        actions = betting[round]
        sub = ET.SubElement(root, 'round', {'name': round})
        for act in actions:
            attrs = {'player': act['player'], 'type': act['type'], 'amount': str(act['amount'])}
            action = ET.SubElement(sub, 'action', attrs)
            if act['error']:
                err = ET.SubElement(action, 'error', {'rel': act['error'][1]})
                err.text = act['error'][0]
    return root

def dump_community(community):
    root = ET.Element('community')
    for card in community:
        root.append(dump_card(card))
    return root

def dump_table(table):
    root = ET.Element('table', {'button': str(table.button)})
    for k in table.occupied_sits():
        player = table.sits[k]
        attrs = {'name': player.name, 'in_stack': str(player.initial_stack), 'stack': str(player.stack), 'sit': str(k)}
        player_el = ET.SubElement(root, 'player', attrs)
        pocket = ET.SubElement(player_el, 'pocket')
        for card in player.pocket.cards:
            pocket.append(dump_card(card))
        tr = player.transport
        ET.SubElement(player_el, 'transport', {'type': tr.type(), 'service': tr.service})
    return root

def dump_deck(deck):
    if not deck.cards:
        return
    root = ET.Element('deck')
    for card in deck.cards:
        root.append(dump_card(card))
    return root

def dump_showdown(showdown):
    if not showdown:
        return
    root = ET.Element('showdown')
    for show in showdown:
        sub = ET.SubElement(root, 'player', {'name': show['player'], 'win': str(show['win'])})
        if show['hand']:
            hand = ET.SubElement(sub, 'hand')
            for card in show['hand'].cards:
                hand.append(dump_card(card))
    return root

def dump_card(card):
    return ET.Element('card', {'rank': card.rank, 'suit': card.suit})

def open(source):
    return ET.parse(source).getroot()

def parse(source):
    root = open(source)
    table = parse_table(root.find('table'))
    deck = parse_deck(root.find('deck'))
    res = interface.HandState(table, deck)
    return res

def parse_table(el):
    table = Table()
    table.button = int(el.get('button'))
    for p_el in el:
        tr = p_el.find('transport').attrib
        p = Player(p_el.get('name'), transport.create(tr['type'], tr['service']), int(p_el.get('stack')))
        table.sit_in(p, int(p_el.get('sit')))
    return table

def parse_deck(el):
    cards = []
    for card_el in el:
        cards.append(Card(card_el.get('rank'), card_el.get('suit')))
    return Deck(cards)

def appendNotEmpty(parent, child):
    if child is not None:
        parent.append(child)
