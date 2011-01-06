# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# formula.py
#
# A formula parser implemented using PLY
#      copyright Yosuke Matsusaka <yosuke.matsusaka@aist.go.jp> 2009
#-----------------------------------------------------------------------------

# History
# 2009/7/9 First version
# 2011/1/6 Modified for super template

import copy
import ply.lex as lex
import ply.yacc as yacc

class Symbol:
    def __init__(self, id):
        self._id = id
        self._name = ""
        self._type = ""
        self.split_id()

    # split the id defined in the script
    def split_id(self):
        sid = self._id.split(':', 1)
        if len(sid) == 2:
            self._name = sid[0]
            self._type = sid[1]
        else:
            self._name = sid[0]
            self._type = True

    def __str__(self):
        return ":".join((self._name, self._type))

# Formula type
class Formula:
    def __init__(self):
        self.type = ""
        self.lhs = None
        self.rhs = None

    def __str__(self):
        return "(%s %s %s)" % (self.lhs, self.type, self.rhs)

    def simplify(self):
        if isinstance(self.lhs, Formula):
            self.lhs = self.lhs.simplify()
        if isinstance(self.rhs, Formula):
            self.rhs = self.rhs.simplify()
        if (isinstance(self.lhs, float) and isinstance(self.rhs, float)):
            return eval("%f %s %f" % (self.lhs, self.type, self.rhs))
        return self

    def getsymbols_recur(self, buf):
        if isinstance(self.lhs, Symbol):
            buf.append(self.lhs)
        elif isinstance(self.lhs, Formula):
            buf = self.lhs.getsymbols_recur(buf)
        if isinstance(self.rhs, Symbol):
            buf.append(self.rhs)
        elif isinstance(self.rhs, Formula):
            buf = self.rhs.getsymbols_recur(buf)
        return buf

    def getsymbols(self):
        buf = []
        return self.getsymbols_recur(buf)

# Lexer
class FormulaLexer:

    tokens = (
        'NAME','NUMBER','STRING',
        'PLUS','MINUS','TIMES','DIVIDE',
        'EQUALS','NEQUALS','G','GE','L','LE','ASSIGNS','CONNECTS',
        'LPAREN','RPAREN',
        )

    # Tokens
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_EQUALS = r'=='
    t_NEQUALS = r'!='
    t_ASSIGNS = r'='
    t_CONNECTS = r':='
    t_G = r'>'
    t_GE = r'>='
    t_L = r'<'
    t_LE = r'<='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_NAME = r'[a-zA-Z_][a-zA-Z0-9_\.:]*'
    t_STRING = r'".*"'

    def t_NUMBER(self, t):
        r'\d+'
        try:
            t.value = float(t.value)
        except ValueError:
            print "Number too large", t.value
            t.value = 0
        return t

    # Ignored characters
    t_ignore = " \t"

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_error(self, t):
        print "Illegal character '%s'" % t.value[0]
        t.lexer.skip(1)

    def __init__(self):
        self.lexer = lex.lex(module=self)

# Parsing rules
class FormulaParser:

    precedence = (
        ('left','PLUS','MINUS'),
        ('left','TIMES','DIVIDE'),
        ('right','UMINUS'),
        )

    def p_statement_op(self, t):
        '''statement : NAME CONNECTS expression
        | NAME ASSIGNS expression
        | NAME G expression
        | NAME GE expression
        | NAME L expression
        | NAME LE expression
        | NAME EQUALS expression
        | NAME NEQUALS expression'''
        self.atom = Formula()
        self.atom.type = t[2]
        self.atom.lhs = Symbol(t[1])
        self.atom.rhs = t[3]

    def p_expression_binop(self, t):
        '''expression : expression PLUS expression
        | expression MINUS expression
        | expression TIMES expression
        | expression DIVIDE expression'''
        t[0] = Formula()
        t[0].type = t[2]
        t[0].lhs = t[1]
        t[0].rhs = t[3]

    def p_expression_uminus(self, t):
        'expression : MINUS expression %prec UMINUS'
        t[0] = -t[2]

    def p_expression_group(self, t):
        'expression : LPAREN expression RPAREN'
        t[0] = t[2]

    def p_expression_number(self, t):
        'expression : NUMBER'
        t[0] = float(t[1])

    def p_expression_name(self, t):
        'expression : NAME'
        t[0] = Symbol(t[1])

    def p_expression_string(self, t):
        'expression : STRING'
        t[0] = t[1].strip('"')

    def p_error(self, t):
        print "Syntax error"

    def parse(self, s):
        self.parser.parse(s, lexer=self.lexer.lexer)
        return self.atom

    def __init__(self):
        self.lexer = FormulaLexer()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self)
