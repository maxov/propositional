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

        def print_header():
            print('\n\033[1mPropositional Statement:\033[0m ' + str(self) + "\n")
            print('╔══' + '══╦══'.join('═' for i in range(o)) + '══╦══' + '═'*len(str(self)) + "══╗")
            print('║  ' + '  ║  '.join(char(i) for i in range(o)) + '  ║  ' + str(self)+ '  ║')
            print('╠══' + '══╬══'.join('═' for i in range(o)) + '══╬══' + '═'*len(str(self)) + "══╣")

        def print_row(truth, result):
            print('║  ' + '  ║  '.join(single_letter(truth[i]) for i in range(len(truth))) + \
                '  ║  ' + ' ' * (len(str(self))//2) + single_letter(result) + \
                ' ' * (len(str(self))//2 - (1-len(str(self))%2)) + '  ║')

        def print_footer():
            print('╚══' + '══╩══'.join('═' for i in range(o)) + '══╩══' + '═'*len(str(self)) + "══╝")

        def single_letter(b):
            return '\033[94mT\033[0m' if b else '\033[91mF\033[0m'

        print_header()
        for truth in opts(o):
            print_row(truth, self(truth))
        print_footer()


class Const(Prop):
    def __init__(self, value):
        self.value = value

    @property
    def ord(self):
        return -1

    def __repr__(self):
        return single_letter(self.value)

    def __call__(self, values):
        return self.value

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
        self.qvar, self.prop = qvar, prop

    def __repr__(self):
        return '({}{}{})'.format(self.char, self.qvar, self.prop)

class All(Quantifier):
    char = chars['ALL']

class Exists(Quantifier):
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

#Returns an array of boolean values corresponding to truthfulness of their uppercase equivalents
def makesTrue(*vars):
    vs = variables(26)
    for v in vars:
        vs[v.ord] = True
    return vs

VS, TRANSFORMS = variables(26), []

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

def implies(a, b):
    return ~a | b

'''
Random generator function that takes in two ints: n and depth
n corresponds to number of random variables used in statement
depth corresponds to the maximum allocated depth of statement
'''
def rgen(n=3, depth=0):
    vs = variables(n)
    if depth < 3 and random.random() > (depth/3)/5:
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

T = Const(True)
F = Const(False)

#Takes in a propositional logic statement string and parses it
def tokenize(props_str):
    if props_str[0] != '(':
        if props_str[0] == chars['NOT']:
            return not tokenize(props_str[1:])
        return props_str[0]
    else:
        num_parens, loc, foundMedian = 0, 0, False
        while loc < len(props_str)-1 and not foundMedian:
            loc += 1
            if props_str[loc] == '(':
                num_parens += 1
            elif props_str[loc] == ')':
                num_parens -= 1
            elif (props_str[loc] == '∧' or props_str[loc] == '∨') and num_parens == 0:
                foundMedian, median = True, props_str[loc]
                first, last = props_str[1:loc-1], props_str[loc+2:len(props_str)-1]
                print(first + " " + median + " " + last)
                tokenize(first)
                tokenize(last)

