copyright = """
Copyright (c) 2017, Daniel Zhang and Max Ovsianskin
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. All advertising materials mentioning features or use of this software
   must display the following acknowledgement:
   This product includes software developed by Daniel Zhang and Max Ovsianskin.
4. The names of these contributors may not be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY DANIEL ZHANG AND MAX OVSIANSKIN ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL DANIEL ZHANG AND MAX OVSIANSKIN BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

"""
To do list:
1. Create question class?
2. Create a method of keeping track of their progress (Maybe a quiz function that contains item 2) 
3. Port over system to React Native
"""

import string, random

chars = {'ALL': '∀', 'EXISTS': '∃', 'EQUALS': '≡', 'AND': '∧', 'OR': '∨', 'NOT': '¬'}
default = {'n': 3, 'depth': 0}
commands = {
'about' : 'Prints more information about this program.',
'help': 'Pulls up this list of information',
'generate': 'Generates a random propositional statement',
'table' : 'Generates a truth table for a given statement. Format: "table <statement1>, <statement2>, ..., <statementn>"',
'rtable' : 'Generates a truth table for a random propositional statement',
'equals' : 'Checks if two statements are equal. Format: "equals? <statement1>, <statement2>"',
'simplify' : 'Simplifies a propositional statement. Format: "simplify <statement>"',
'settings' : 'Pulls up a menu to edit the program settings',
'quit' : 'Terminates the program',
'exit' : 'Terminates the program',
'question' : 'Prints out a quiz question'
}

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

    #Note: This does not work for some reason; currently using my less elegant solution involving tables
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
        elif string[0:3] == '({}('.format(chars['NOT']) and string[len(string)-1] == ')':
            return Not(helper(string[2:len(string)-1]))
        elif string[0:2] == '((' and string[len(string)-1] == ')':
            return helper(string[1:len(string)-1])
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

#Replaces a set of symbols with characters that the read function can parse
def replaceStr(string):
    assert type(string) is str
    old_chars = {'&': chars['AND'], '|': chars['OR'], '~': chars['NOT'], \
                 '^': chars['AND'], 'v': chars['OR'], '!': chars['NOT']}
    return "".join(s if s not in old_chars else old_chars[s] for s in string)

#Checks the logical equivalency of two Strings (NOT PropositionalVariable objects)
def check_equivalency(s1, s2):
    s1, s2 = read(s1), read(s2)
    ord = max(s1.ord, s2.ord) + 1
    table1, table2 = generate_table([s1], ord), generate_table([s2], ord)
    assert len(table1) == len(table2) and len(table1[0]) == len(table2[0])
    return all([table1[i][len(table1[0])-1] == table2[i][len(table1[0])-1] for i in range(1, len(table1))])

#Takes in a PropositionalVariable object (NOT a string) and simplifies the corresponding statement
def do_simplify(s1):
    if type(s1) == PropositionalVariable:
        return s1
    if type(s1) == Not:
        if type(s1.arg) == Not:
            return do_simplify(s1.arg.arg)
        if type(s1.arg) == Or and type(s1.arg.left) == Not and type(s1.arg.right) == Not:
            return And(do_simplify(s1.arg.left.arg), do_simplify(s1.arg.right.arg))
        if type(s1.arg) == And and type(s1.arg.left) == Not and type(s1.arg.right) == Not:
            return Or(do_simplify(s1.arg.left.arg), do_simplify(s1.arg.right.arg))
        return Not(do_simplify(s1.arg))
    if (type(s1) == And or type(s1) == Or) and s1.left == s1.right:
        return do_simplify(s1.left)
    if type(s1) == And:
        return And(do_simplify(s1.left), do_simplify(s1.right))
    if type(s1) == Or:
        return Or(do_simplify(s1.left), do_simplify(s1.right))

"""
Generates a table of statements given an array of PropositionalVariable objects (NOT Strings)
with an optional variable that lists requested order. (Order in this case means how many variables)
are shown. For example, someone can request, for some reason, a truth table for ~A with the results
given inputs A, B, C, D, and E by requesting ord = 5.
"""
def generate_table(statements, ord = -1):
    if ord == -1:
        ord = max([s.ord for s in statements]) + 1
    
    try:
        assert all([ord > s.ord for s in statements])

        def calc(b):
            return green('T') if b else red('F')

        return [[char(i) for i in range(ord)] + [str(s) for s in statements]] + \
        [[calc(truth[i]) for i in range(len(truth))] + [calc(s(truth)) for s in statements] for truth in opts(ord)]
    except AssertionError:
        print(bold('Error: ') + "Order is too small or too large (Max size: 26).")

#Generates a random question for the question function to parse.
def generate_q(n = default['n'], depth = default['depth']):
    s = [rgen([n, depth]) for _ in range(4)]
    answer = int(random.random() * 4)
    
    for x in range(4):
        if x != answer and check_equivalency(s[x], s[answer]):
            s[x] = rgen([n, depth])

    return answer, s

'''
Random generator function that takes in two ints: n and depth
n corresponds to number of random variables used in statement
depth corresponds to the maximum allocated depth of statement
'''
def rgen(args):
    def helper(n, depth):
        if depth < 3 and random.random() > (depth/default['n'])/5:
            return {
                0: Not(helper(n, depth + 1)),
                1: And(helper(n, depth + 1), helper(n, depth + 1)),
                2: Or(helper(n, depth + 1), helper(n, depth + 1))
            }[int(random.random()*3)]
        else:
            return random.choice(VS[:n])
    assert len(args) <= 2
    if len(args) == 0:
        return do_simplify(helper(default['n'], default['depth'])).__repr__()
    elif len(args) == 1:
        return do_simplify(helper(int(args[0]), default['depth'])).__repr__()
    else:
        return do_simplify(helper(int(args[0]), int(args[1]))).__repr__()

#Generates a random propositional statement (for users)
def generate(args):
    print(rgen([]))

#Generates a random table (for users)
def rtable(args):
    return table([rgen(args)])

#print_row, footer are both used in both table, qtable. Placed in global to limit code redundancy.
def print_row(table, t, o, ls):
        print('║  ' + '  ║  '.join(t[:o]) + '  ║║  ' + \
            '  ║  '.join(' ' * (ls[i - o] // 2) + t[i] + ' ' * (ls[i - o] // 2 - (1 - ls[i - o] % 2)) for i in range(o, len(table[0]))) + '  ║')

def print_footer(o, ls):
    print('╚══' + '══╩══'.join('═' for i in range(o)) + '══╩╩══' + '══╩══'.join('═' * l for l in ls) + "══╝\n")

def table(args):
    statements = [read(statement) for statement in ' '.join(args).split(', ')]
    tbl, ls = generate_table(statements), [len(str(statement)) for statement in statements]
    o = len(tbl[0]) - len(statements)

    def print_header():
        print(bold('Propositional Statement(s): ') + ", ".join(tbl[0][o:]) + "\n")
        print('╔══' + '══╦══'.join('═' for i in range(o)) + '══╦╦══' + '══╦══'.join('═' * l for l in ls) + "══╗")
        print('║  ' + '  ║  '.join(tbl[0][:o]) + '  ║║  ' + '  ║  '.join(tbl[0][i] for i in range(o, len(tbl[0]))) + '  ║')
        print('╠══' + '══╬══'.join('═' for i in range(o)) + '══╬╬══' + '══╬══'.join('═' * l for l in ls) + "══╣")

    print_header()
    [print_row(tbl, t, o, ls) for t in tbl[1:]]
    print_footer(o, ls)

def qtable(statements, answer):
    statements = [read(statement) for statement in statements]
    table = generate_table(statements)
    o, ls = len(table[0]) - len(statements), [1, 1, 1, 1]

    def print_header():
        print(bold('Please select the correct truth table for the following statement: ') + statements[answer].__repr__() + "\n")
        print('╔══' + '══╦══'.join('═' for i in range(o)) + '══╦╦══' + '══╦══'.join('═' for l in ls) + "══╗")
        print('║  ' + '  ║  '.join(table[0][:o]) + '  ║║  ' + '  ║  '.join(['a', 'b', 'c', 'd']) + '  ║')
        print('╠══' + '══╬══'.join('═' for i in range(o)) + '══╬╬══' + '══╬══'.join('═' for l in ls) + "══╣")

    print_header()
    [print_row(table, t, o, ls) for t in table[1:]]
    print_footer(o, ls)

#Generates a random question (for user)
def question(*args):
    a, s = generate_q()
    qtable(s, a)
    try:
        ans = input(bold("Answer: > "))
        assert ans in ['a', 'b', 'c', 'd']
    except AssertionError:
        print(red("Error: ") + "Cannot read answer. ")
    if ord(ans) - 96 == a + 1:
        print("Success! Answer is correct.")
    else:
        print("Wrong answer. The correct answer is {}.".format(['a', 'b', 'c', 'd'][a]))

#Checks the equivalency of two statements (for users)
def equals(args):
    statements = ' '.join(args).split(', ')
    print("\n" + str(check_equivalency(statements[0], statements[1])) + "\n")

#Simplifies a logical statement (for both users and within the code)
def simplify(args):
    statements = ' '.join(args)
    print(do_simplify(read(statements)))

def help(*args):
    print("\nList of commands:\n")
    for n in commands:
        print("\t{}\t\t{}.".format(n, commands[n]) if len(n) < 8 else "\t{}\t{}.".format(n, commands[n]))
    print("\n")

def change_setting(var, req, min, max):
    global default
    try:
        assert req < max and req > min
        default[var] = req
        print('\nSuccess: {} set to {}.\n'.format(var, req))
    except (AssertionError, ValueError):
        print(red('Error: ' ) + '{} must be set to integer between {} and {}.\n'.format(var, min, max-1))

def settings(*args):
    print("\nWelcome to the settings panel! Here you may edit the program settings." + \
          "Program settings are wiped at the start of every session; in other words, " + \
          "they " + bold("reset when you exit the program") + ". We haven't yet created an option of saving " + \
          "your settings just yet; they'll be included in the next release!\nBelow is a list of parameters " + \
          "and their current values. To change each value, simply type the name of the parameter and your preferred value.")
    print("\t{}\t\t{}\t\tSets the number of random variables used.".format(bold('n'), default['n']))
    print("\t{}\t\t{}\t\tSets the maximumsize of the randomly generated statements.".format(bold('depth'), default['depth']))
    print('\nTo leave this panel, please type either {} or {} .\n'.format(bold('exit'), bold('quit')))
    while True:
        raw = input(bold('Settings: > '))
        if raw == 'exit' or raw == 'quit':
            print("\n")
            return
        inputs = raw.split(' ')
        if len(inputs) != 2:
            print(red('Error: ' ) + 'wrong number of inputs.\n')
        elif inputs[0] == 'n':
            change_setting('n', int(inputs[1]), 0, len(VS)+1)
        elif inputs[0] == 'depth':
            change_setting('depth', int(inputs[1]), 0, 6)
        else:
            print(red('Error: ' ) + 'Cannot read input variable.')

def about(*args):
    print(copyright)

def run():
    print("{}[2J\nWelcome to Propositional Calculator v0.0.5a! Type {} for a guide to using this program.\n".format(chr(27), bold('help')))
    while True:
        try:
            inputs = input(bold('> ')).split(' ')
            assert inputs[0] in commands
            eval(inputs[0])(inputs[1:])
        except (AssertionError, ValueError, TypeError, NameError):
            print(red('Error: ' ) + 'Cannot read input.')
        except IndexError:
            print(red('Error: ') + 'Wrong number of parameters specified')

run()
