import string
import random
chars = {'ALL': '∀', 'EXISTS': '∃', 'EQUIVALENT': '≡', 'AND': '∧', 'OR': '∨', 'NOT': '¬'}

def opts(n):
    if n == 0:
        yield []
    else:
        for v in opts(n-1):
            yield [True] + v
        for v in opts(n-1):
            yield [False] + v

def char(i):
    return chr(ord('A') + i)

def print_header(o, e):
    print(' '.join(char(i) for i in range(o)) + ' ' + str(e))

def single_letter(b):
    if b:
        return 'T'
    else:
        return 'F'

def print_row(truth, result):
    print(' '.join(single_letter(truth[i]) for i in range(len(truth))) + ' ' + single_letter(result))

class Prop:
    def __or__(self, that):
        return Or(self, that)
    def __and__(self, that):
        return And(self, that)
    def __invert__(self):
        return Not(self)
    def __eq__(self, that):
        o = max(self.ord, that.ord) + 1
        for truth in opts(o):
            if self(truth) != that(truth):
                return False
        return True
    def table(self):
        o = self.ord + 1
        print_header(o, self)
        for truth in opts(o):
            print_row(truth, self(truth))

#Are also functions
class PropositionalVariable(Prop):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    @property
    def ord(self):
        return ord(self.name) - ord('A')

    def __call__(self, values):
        return values[self.ord]

class UnaryOp(Prop):
    def __init__(self, arg):
        self.arg = arg
    def __repr__(self):
        return '{}{}'.format(self.symbol, self.arg)

    @property
    def ord(self):
        return self.arg.ord

class BinaryOp(Prop):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return '({} {} {})'.format(self.left, self.symbol, self.right)

    @property
    def ord(self):
        return max(self.left.ord, self.right.ord)

class Quantifier(Prop):
    char = ""

    def __init__(self, qvar, prop):
        self.qvar = qvar
        self.prop = prop

    def __repr__(self):
        return '({}{}{})'.format(self.char, self.qvar, self.prop)

class All(BinaryOp):
    char = chars['ALL']

class Exists(BinaryOp):
    char = chars['EXISTS']

class Or(BinaryOp):
    symbol = chars['OR']

    def __call__(self, values):
        return self.left(values) or self.right(values)

class And(BinaryOp):
    symbol = chars['AND']

    def __call__(self, values):
        return self.left(values) and self.right(values)

class Not(UnaryOp):
    symbol = chars['NOT']

    def __invert__(self):
        return self.arg

    def __call__(self, values):
        return not self.arg(values)

def variables(n):
    return [PropositionalVariable(c) for c in string.ascii_uppercase[:n]]

#basically only these variables are true
def onlyMakeTheseTrue(*variables):
    vs = [False] * 26
    for v in variables:
        vs[v.ord] = True
    return vs

VS = variables(26)

TRANSFORMS = []

def always_T(obj):
    return True

def transform(condition=always_T):
    def inner(fn):
        TRANSFORMS.append((condition, fn))
        return fn
    return inner

def isa(tpe):
    def inner(obj):
        return isinstance(obj, tpe)
    return inner

@transform(isa(Or))
def de_morgan_or(x):
    l, r = x.left, x.right
    return ~(~l & ~r)

@transform(isa(And))
def de_morgan_and(x):
    l, r = x.left, x.right
    return ~(~l | ~r)

def rgen(n=3, depth=0):
    vs = variables(n)
    if depth<3 and random.random() > 1/5:
        x = random.random()
        if x < 1/3:
            return ~rgen(n, depth+1)
        elif x < 2/3:
            return rgen(n, depth+1) & rgen(n, depth+1)
        else:
            return rgen(n, depth+1) | rgen(n, depth+1)
    else:
        return random.choice(VS[:n])

A, B, C, D, E = VS[:5]

T = A | ~A
F = A & ~A

def implies(a, b):
    return ~a | b
