import re
import os
from glob import iglob
import tempfile
from StringIO import StringIO
from robopoker.croupier import Croupier
from robopoker.handstate.interface import HandState

def fixtures():
    for initial in iglob(os.path.abspath(os.path.dirname(__file__)) + '/fixture/*.in.xml'):
        if os.path.basename(initial).startswith('_'): continue
        expected = re.sub(r'(\..*){2}$', '.out.xml', initial)
        yield initial, expected

def diff(state, expected):
    tmp = file(tempfile.mkstemp()[1], 'w')
    tmp.write(state.dump(False))
    tmp.close()
    code = os.system('diff -b %s %s' % (expected, tmp.name))
    return not code

if __name__ == '__main__':
    for initial, expected in fixtures():
        success = False
        print '%-40s' % os.path.basename(initial),
        state = HandState.load(file(initial))
        croupier = Croupier(state, StringIO())
        croupier.conduct()
        success = diff(state, expected)
        if not success:
            print 'F'
            exit(1)
        print '.'


