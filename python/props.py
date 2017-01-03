import string
import random
chars = {'ALL': '∀', 'EXISTS': '∃', 'EQUIVALENT': '≡', 'AND': '∧', 'OR': '∨', 'NOT': '¬'}

class Prop:
    def __or__(self, that):
        return Or(self, that)
    def __and__(self, that):
        return And(self, that)
    def __invert__(self):
        return Not(self)

class PropositionalVariable(Prop):
     def __init__(self, name):
         self.name = name

     def __repr__(self):
         return self.name

     @property
     def variables(self):
         return frozenset(self.name)

class UnaryOp(Prop):
    def __init__(self, arg):
        self.arg = arg
    def __repr__(self):
        return '{}{}'.format(self.symbol, self.arg)
    @property
    def variables(self):
        return self.arg.variables

class BinaryOp(Prop):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return '({} {} {})'.format(self.left, self.symbol, self.right)
    @property
    def variables(self):
        return self.left.variables | self.right.variables

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

class And(BinaryOp):
    symbol = chars['AND']

class Not(UnaryOp):
    symbol = chars['NOT']

    def __invert__(self):
        return self.arg

def variables(n):
    return [PropositionalVariable(c) for c in string.ascii_uppercase[:n]]

TRANSFORMS = []

def T(obj):
    return True

def transform(condition=T):
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
    if depth<(5-random.random()*2) and random.random() > 1/10:
        x = random.random()
        if x < 1/3:
            return ~rgen(n, depth+1)
        elif x < 2/3:
            return rgen(n, depth+1) & rgen(n, depth+1)
        else:
            return rgen(n, depth+1) | rgen(n, depth+1)
    else:
        return random.choice(vs)
