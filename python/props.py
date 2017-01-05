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

def bold(str):
    return '\033[1m{}\033[0m'.format(str)

def red(str):
    return '\033[91m{}\033[0m'.format(str)

def green(str):
    return '\033[94m{}\033[0m'.format(str)

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

def transform(condition = always_T):
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
            while loc < len(string) - 1 and not found:
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

def generate_table(statement, ord = -1):
    if ord == -1:
        ord = statement.ord + 1
    
    try:
        assert ord > statement.ord

        def calc(b):
            return green('T') if b else red('F')

        return [[char(i) for i in range(ord)] + [str(statement)]] + \
        [[calc(truth[i]) for i in range(len(truth))] + [calc(statement(truth))] for truth in opts(ord)]
    except AssertionError:
        print(bold('Error: ') + "Order is too small or too large (Max size: 26).")

def check_equivalency(s1, s2):
    table1, table2 = generate_table(1), generate_table(2)

def print_table(statement):
    statement = read(statement)
    table, l = generate_table(statement), len(str(statement))
    o = len(table[0]) - 1

    def print_header():
        print(bold('Propositional Statement: ') + table[0][o] + "\n")
        print('╔══' + '══╦══'.join('═' for i in range(o)) + '══╦══' + '═' * l + "══╗")
        print('║  ' + '  ║  '.join(table[0][:o]) + '  ║  ' + table[0][o] + '  ║')
        print('╠══' + '══╬══'.join('═' for i in range(o)) + '══╬══' + '═' * l + "══╣")

    def print_row(t):
        print('║  ' + '  ║  '.join(t[:o]) + \
            '  ║  ' + ' ' * (l // 2) + t[o] + \
            ' ' * (l // 2 - (1 - l % 2)) + '  ║')

    def print_footer():
        print('╚══' + '══╩══'.join('═' for i in range(o)) + '══╩══' + '═' * l + "══╝\n")

    print_header()
    [print_row(t) for t in table[1:]]
    print_footer()

'''
Random generator function that takes in two ints: n and depth
n corresponds to number of random variables used in statement
depth corresponds to the maximum allocated depth of statement
'''
def rgen(vars):
    def helper(n, depth):
        vs = variables(n)
        if depth < 3 and random.random() > (depth/default_n)/5:
            x, depth = int(random.random()*3), depth + 1
            return {
                0: Not(helper(n, depth)),
                1: And(helper(n, depth), helper(n, depth)),
                2: Or(helper(n, depth), helper(n, depth))
            }[x]
        else:
            return random.choice(VS[:n])
    try:
        assert len(vars) <= 2
        if not len(vars):
            return helper(default_n, default_depth).__repr__()
        elif len(vars) == 1:
            return helper(int(vars[0]), default_depth).__repr__()
        else:
            return helper(int(vars[0]), int(vars[1])).__repr__()
    except (AssertionError, ValueError):
        print(red("Error:") + " wrong number of inputs.\n")

def rtable(n = default_n, depth = default_depth):
    return print_table(rgen([n, depth]))

def help():
    print("\nList of commands:\n")
    print("\t" + bold('help') + "\t\tPulls up this list of information.")
    print("\t" + bold('rgen') + "\t\tGenerates a random propositional statement.")
    print("\t" + bold('rtable') + "\t\tGenerates a truth table for a random propositional statement.")
    print("\t" + bold('table') + "\t\tGenerates a truth table for a propositional statement. Format: 'table <statement>'")
    print("\t" + bold('settings') + "\tPulls up a menu to edit the program settings.")
    print("\t" + bold('quit, exit') + "\tTerminates the program.")
    print("\n")

def settings():
    global default_n, default_depth
    print("\nWelcome to the settings panel! Here you may edit the program settings." + \
          "Program settings are wiped at the start of every session; in other words, " + \
          "they " + bold("reset when you exit the program") + ". We haven't yet created an option of saving " + \
          "your settings just yet; they'll be included in the next release!")
    print("\nBelow is a list of parameters and their current values. To change each value, simply type the name of the " + \
          "parameter and your preferred value.")
    print("\t" + bold('n') + "\t\t" + str(default_n) + "\t\tSets the number of random variables used.")
    print("\t" + bold('depth') + "\t\t"  + str(default_depth) + "\t\tSets the maximumsize of the randomly generated statements.")
    print("\nTo leave this panel, please type either " + bold('exit') + " or " + bold('quit') + '.\n')
    while True:
        raw = input(bold('Settings: > '))
        if raw == 'exit' or raw == 'quit':
            print("\n")
            return
        inputs = raw.split(' ')
        if len(inputs) != 2:
            print(red('Error: ' ) + 'wrong number of inputs.\n')
        elif inputs[0] == 'n':
            try:
                assert int(inputs[1]) <= len(VS) and int(inputs[1]) > 0
                default_n = int(inputs[1])
                print('\nSuccess: n set to ' + str(default_n) + "\n")
            except (AssertionError, ValueError):
                print(red('Error: ' ) + 'value must be set to integer between 1 and 26.\n')
        elif inputs[0] == 'depth':
            try:
                assert int(inputs[1]) <= 5 and int(inputs[1]) > 0
                defaut_depth = int(inputs[1])
                print('\nSuccess: depth set to ' + str(default_depth) + "\n")
            except (AssertionError, ValueError):
                print(red('Error: ' ) + 'value must be set to integer between 1 and 5.\n')
        else:
            print(red('Error: ' ) + 'Cannot read input variable.')

def run():
    print(chr(27) + "[2J")
    print("\nWelcome to Propositional Calculator v0.0.2a! Type " + bold('help') + " for a guide to using this program.\n")
    while True:
        raw = input(bold('> '))
        if raw[0:5] == 'table':
            if len(raw) <= 6:
                print(red('Error: ' ) + 'Need to provide propositional statement.\n')
            else:
                try:
                    print_table(raw[6:])
                except (SyntaxError, ValueError, NameError, AttributeError):
                    print(red('Error: ' ) + 'Improperly formatted inputs.\n')
        else:
            inputs = raw.split(' ')
            if inputs[0] == 'rgen':
                if len(inputs) == 1:
                    print(rgen([]))
                else:
                    print(rgen(inputs[1:]))
            elif inputs[0] == 'rtable':
                rtable()
            elif inputs[0] == 'quit' or inputs[0] == 'exit':
                quit()
            elif inputs[0] == 'help':
                help()
            elif inputs[0] == 'settings':
                settings()
            else:
                print(red('Error: ' ) + 'Cannot read input.\n')

run()
