"""
To do list:
1. Create a multiple choice propositional statement generator that tests one's knowledge of these statements.
2. Port over system to React Native
"""

import string, random
chars = {'ALL': '∀', 'EXISTS': '∃', 'EQUALS': '≡', 'AND': '∧', 'OR': '∨', 'NOT': '¬'}
default_n, default_depth = 3, 0

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
        return all([self(truth) == that(truth) for truth in opts(max(self.ord, that.ord) + 1)])


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

class Not(UnaryOp):
    symbol = chars['NOT']

    def __invert__(self):
        return self.arg

    def __call__(self, values):
        return not self.arg(values)

class BinaryOp(Prop):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return '({} {} {})'.format(self.left, self.symbol, self.right)

    @property
    def ord(self):
        return max(self.left.ord, self.right.ord)

class Or(BinaryOp):
    symbol = chars['OR']

    def __call__(self, values):
        return self.left(values) or self.right(values)

class And(BinaryOp):
    symbol = chars['AND']

    def __call__(self, values):
        return self.left(values) and self.right(values)

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

A, B, C, D, E = VS[:5]
T, F = Const(True), Const(False)

#Reads in a propositional logic statement string and converts it to an object
def read(propositional):
    def helper(string):
        if string[0] != '(':
            if string[0] == chars['NOT']:
                return Not(helper(string[1:]))
            return eval(string[0])
        else:
            parens, loc, found = 0, 0, False
            while loc < len(string)-1 and not found:
                loc += 1
                if string[loc] == '(':
                    parens += 1
                elif string[loc] == ')':
                    parens -= 1
                elif (string[loc] == chars['AND'] or string[loc] == chars['OR']) and not parens:
                    found, median = True, string[loc]
                    first, last = string[1:loc-1], string[loc+2:len(string)-1]
                    return And(helper(first), helper(last)) if median == chars['AND'] \
                    else Or(helper(first), helper(last))
    return helper(replaceStr(propositional))

def replaceStr(string):
    assert type(string) is str
    old_chars = {'&': chars['AND'], '|': chars['OR'], '~': chars['NOT'], \
                 '^': chars['AND'], 'v': chars['OR'], '!': chars['NOT']}
    return "".join(s if s not in old_chars else old_chars[s] for s in string)

def table(statement):
    statement = read(statement)
    o, s = statement.ord + 1, str(statement)
    l = len(str(statement))

    def print_header():
        print('\n\033[1mPropositional Statement:\033[0m ' + s + "\n")
        print('╔══' + '══╦══'.join('═' for i in range(o)) + '══╦══' + '═' * l + "══╗")
        print('║  ' + '  ║  '.join(char(i) for i in range(o)) + '  ║  ' + s + '  ║')
        print('╠══' + '══╬══'.join('═' for i in range(o)) + '══╬══' + '═' * l + "══╣")

    def print_row(truth, result):
        print('║  ' + '  ║  '.join(calc(truth[i]) for i in range(len(truth))) + \
            '  ║  ' + ' ' * (l // 2) + calc(result) + \
            ' ' * (l // 2 - (1 - l % 2)) + '  ║')

    def print_footer():
        print('╚══' + '══╩══'.join('═' for i in range(o)) + '══╩══' + '═' * l + "══╝\n")

    def calc(b):
        return '\033[94mT\033[0m' if b else '\033[91mF\033[0m'

    print_header()
    for truth in opts(o):
        print_row(truth, statement(truth))
    print_footer()

'''
Random generator function that takes in two ints: n and depth
n corresponds to number of random variables used in statement
depth corresponds to the maximum allocated depth of statement
'''
def rgen(n = default_n, depth = default_depth):
    def helper(n, depth):
        vs = variables(n)
        if depth < 3 and random.random() > (depth/default_n)/5:
            x, depth = random.random(), depth + 1
            if x < 1/3:
                return Not(helper(n, depth))
            elif x < 2/3:
                return And(helper(n, depth), helper(n, depth))
            else:
                return Or(helper(n, depth), helper(n, depth))
        else:
            return random.choice(VS[:n])
    return helper(n, depth).__repr__()

def rtable(n = default_n, depth = default_depth):
    return table(rgen(n, depth))

def help():
    print("\nList of commands:\n")
    print("\t\033[1mhelp\033[0m\t\tPulls up this list of information.")
    print("\t\033[1mrgen\033[0m\t\tGenerates a random propositional statement.")
    print("\t\033[1mrtable\033[0m\t\tGenerates a truth table for a random propositional statement.")
    print("\t\033[1mtable\033[0m\t\tGenerates a truth table for a propositional statement. Format: 'table <statement>'")
    print("\t\033[1msettings\033[0m\tPulls up a menu to edit the program settings.")
    print("\t\033[1mexit, quit\033[0m\tTerminates the program.")
    print("\n")

def settings():
    global default_n, default_depth
    print("\nWelcome to the settings panel! Here you may edit the program settings." + \
          "Program settings are wiped at the start of every session; in other words, " + \
          "they \033[1mreset when you exit the program\033[0m. We haven't yet created an option of saving " + \
          "your settings just yet; they'll be included in the next release!")
    print("\nBelow is a list of parameters and their current values. To change each value, simply type the name of the " + \
          "parameter and your preferred value.")
    print("\t\033[1mn\033[0m\t\t" + str(default_n) + "\t\tSets the number of random variables used.")
    print("\t\033[1mdepth\033[0m\t\t"  + str(default_depth) + "\t\tSets the maximumsize of the randomly generated statements.")
    print("\nTo leave this panel, please type either \033[1mexit\033[0m or \033[1mquit\033[0m.\n")
    while True:
        raw = input("\033[1mSettings: > \033[0m")
        if raw == 'exit' or raw == 'quit':
            print("\n")
            return
        inputs = raw.split(' ')
        if len(inputs) != 2:
            print('\033[91mError:\033[0m wrong number of inputs.\n')
        elif inputs[0] == 'n':
            try:
                assert int(inputs[1]) <= 26 and int(inputs[1]) > 0
                default_n = int(inputs[1])
                print('\nSuccess: n set to ' + str(default_n) + "\n")
            except (AssertionError, ValueError):
                print('\n\033[91mError:\033[0m value must be set to integer between 1 and 26\n')
        elif inputs[0] == 'depth':
            try:
                assert int(inputs[1]) <= 5 and int(inputs[1]) > 0
                defaut_depth = int(inputs[1])
                print('\nSuccess: depth set to ' + str(default_depth) + "\n")
            except (AssertionError, ValueError):
                print('\n\033[91mError:\033[0m value must be set to integer between 1 and 5\n')
        else:
            print("\033[91mError:\033[0m Cannot read input")

def run():
    print(chr(27) + "[2J")
    print("\nWelcome to Propositional Calculator v0.0.2a! Type \033[1mhelp\033[0m for a guide to using this program.\n")
    while True:
        raw = input("\033[1m> \033[0m")
        if raw[0:5] == 'table':
            if len(raw) <= 6:
                print("\033[91mError:\033[0m Need to provide propositional statement.\n")
            else:
                try:
                    table(raw[6:])
                except (SyntaxError, ValueError, NameError, AttributeError):
                    print("\033[91mError:\033[0m Improperly formatted inputs.\n")
        else:
            inputs = raw.split(' ')
            if inputs[0] == 'rgen':
                if len(inputs) == 1:
                    print(rgen())
                else:
                    if len(inputs) == 2:
                        print("\033[91mError:\033[0m Improper length of inputs.\n")
                    else:
                        print(rgen(int(inputs[1]), int(inputs[2])))
            elif inputs[0] == 'rtable':
                rtable()
            elif inputs[0] == 'quit' or inputs[0] == 'exit':
                quit()
            elif inputs[0] == 'help':
                help()
            elif inputs[0] == 'settings':
                settings()
            else:
                print("\033[91mError:\033[0m Cannot read input.\n")

run()
