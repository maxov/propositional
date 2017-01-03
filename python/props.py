import string

class Prop:
    def __or__(self, that):
        return Or(self, that)
    def __and__(self, that):
        return And(self, that)
    def __invert__(self):
        return Not(self)

class Variable(Prop):
    chars = {'EVERY': '∀', 'EXISTS': '∃', 'EQUIVALENT': '≡', 'AND': '∧', 'OR': '∨',}

    def __init__(this, proposition, variable, quantifier = 'EVERY'):
        this.proposition = proposition
        this.variable = variable
        this.quantifier = quantifier

    def __repr__(this):
        return '{}{}{}({})'.format(this.chars[this.quantifier], this.variable, this.proposition, this.variable)

    @property
    def variables(self):
        return frozenset(self.variable)

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

class Or(BinaryOp):
    symbol = '|'

class And(BinaryOp):
    symbol = '&'

class Not(UnaryOp):
    symbol = '!'

    def __invert__(self):
        return self.arg

def variables(n):
    return [Variable(c, x) for c in string.ascii_uppercase[:n]]

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
    return ~(x)
