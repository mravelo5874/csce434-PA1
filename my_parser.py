#!/usr/bin/env python3
import sys
import time
import enum

# --------------------------------
#   Marco Ravelo
#   CSCE 434 - Compiler Design
#   Assignment #1 - 2/2/2021 
#   file: my_parser.py
# --------------------------------

# Resources used:
# - https://www.booleanworld.com/building-recursive-descent-parsers-definitive-guide/#content
# - https://cyberzhg.github.io/toolbox/left_rec

# character lists:
whitespace = ' \n\t\r\v\f'
alpha_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
alphaNums_chars = '01234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
nums_chars = '01234567890'
valid_chars = '01234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_:;=+-*^()'

# Grammar:
# <program>   -> begin <stmt_list> end 
# <stmt>      -> <id> := <expr> | ε
# <stmt_list> -> <stmt_list> ; <stmt> | <stmt>
# <expr>      -> <expr> + <term> | <expr> - <term> | <term>
# <term>      -> <term> * <factor> | <term> div <factor> | <term> mod <factor> | <factor>
# <factor>    -> <primary>^<factor>| <primary>
# <primary>   -> <id> | <num> | ( <expr> )

# Grammar w/ left recursion removed:
#    program -> begin stmt_list end
#       stmt -> id := expr
#             | ϵ
#  stmt_list -> id := expr stmt_list'
#             | stmt_list'
#       expr -> term expr'
#       term -> factor term'
#     factor -> primary ^ factor
#             | primary
#    primary -> id
#             | num
#             | ( expr )
# stmt_list' -> ; stmt stmt_list'
#             | ϵ
#      expr' -> + term expr'
#             | - term expr'
#             | ϵ
#      term' -> * factor term'
#             | div factor term'
#             | mod factor term'
#             | ϵ

class KeywordType(enum.Enum):
    PRGRM_KEYWORD = 1
    ASSIGNMENT = 2
    OPERATOR = 3
    PARENTHESIS = 4
    STMT_TERMINATOR = 5

# accepts text position and formats an error message for the parser
class ParseError(Exception):
    def __init__(self, pos, lines, msg):
        self.pos = pos
        self.lines = lines
        self.msg = msg
        
    def __str__(self):
        sum = 0
        count = 0
        while (sum <= self.pos):
            sum += len(self.lines[count])
            count += 1
        sum -= len(self.lines[count - 1])
        # print ('sum: %i, count: %i, pos: %i' % (sum, count, self.pos))
        line_num = count
        pos_num = self.pos - sum + 1

        return 'ParseError: %s at line %s pos %s' % (self.msg, line_num, pos_num)

# the base parser class
class MyParser:
    # --------------------------------
    #   INITIALIZER
    # --------------------------------

    def __init__(self, print_tree, time_parse):
        self.text = ''
        self.lines = None
        self.pos = -1
        self.len = -1
        self.output = []
        self.tabs = 0
        self.print = print_tree
        self.time = time_parse
        self.errors = []

    # --------------------------------
    #   HELPER FUNCTIONS
    # --------------------------------

    # skips over whitespace
    def ignore_whitespace(self):
        # skip any whitespace chars
        while (self.pos < self.len and self.text[self.pos] in whitespace):
            self.pos += 1
        return

    # gets the next word separated by whitespace
    def get_next_word(self, any_valid_symbol=False, limit=sys.maxsize):
        self.ignore_whitespace()

        non_valid = ';+-*^()'
        if (any_valid_symbol):
            non_valid = ''

        # create word until whitespace detected or EOF
        temp_pos = self.pos
        count = 0
        while (count < limit and temp_pos <= self.len and self.text[temp_pos] not in whitespace and self.text[temp_pos] not in non_valid):
            temp_pos += 1
            count += 1
        
        word_found = self.text[self.pos:temp_pos]

        # check to see if word is in the format: num div num | num mod num
        if ('div' in word_found and word_found != 'div'):
            split_list = word_found.split('div')
            while ("" in split_list):
                split_list.remove("")
            print (split_list)
            is_num = True
            if (len(split_list) == 1):
                word_found = 'div'
            else:
                for word in split_list:
                    for char in word:
                        if (char not in nums_chars):
                            is_num = False
                if (is_num and len(split_list) == 2):
                    word_found = split_list[0]
            
        elif ('mod' in word_found and word_found != 'mod'):
            split_list = word_found.split('mod')
            while ("" in split_list): 
                split_list.remove("")
            print (split_list)
            is_num = True
            if (len(split_list) == 1):
                word_found = 'mod'
            else:
                for word in split_list:
                    for char in word:
                        if (char not in nums_chars):
                            is_num = False
                if (is_num and len(split_list) == 2):
                    word_found = split_list[0]

        # make sure word is valid
        index = 0
        for char in word_found:
            index += 1
            if (char not in valid_chars):
                raise ParseError(self.pos + index, self.lines, 'Invaild word (%s)' % word_found)
        
        self.pretty_print_tabs('word found: %s' % word_found)
        return word_found
    
    # attempts to match the given keyword
    def match(self, keyword, keyword_type):
        word = self.get_next_word(True, len(keyword))
        if (word == keyword):
            self.pos += len(keyword)
            self.pretty_print_tabs('matched: %s' % keyword)
            return

        raise ParseError(self.pos, self.lines, 'Expected keyword of type \'%s\' but found \'%s\'' % (keyword_type.name, word))

    # attempts to find and return an id
    def get_id(self):
        self.ignore_whitespace()

        id_found = self.get_next_word()

        if (len(id_found) == 0):
            raise ParseError(self.pos, self.lines, 'Missing id')
        
        # ensure chars in id are allowed:
        # '<id> represents any valid sequence of characters and digits starting with a character'
        if (id_found[0] not in alpha_chars):
            raise ParseError(self.pos, self.lines, 'Invalid id (must start with character)')
            
        for i in range(1, len(id_found) - 1):
            if (id_found[i] not in alphaNums_chars):
                raise ParseError(self.pos + i, self.lines, 'Invaild id (invaild char -> %s)' % id_found[i])
        
        self.pos += len(id_found)
        self.pretty_print_tabs("id found: %s" % id_found)
        return id_found

    # attempts to get the next number
    def get_number(self):
        self.ignore_whitespace()

        num_found = self.get_next_word()
        if (num_found == ''):
            raise ParseError(self.pos, self.lines, 'Expected number character (empty number)')

        for num in num_found:
            if (num not in nums_chars):
                raise ParseError(self.pos, self.lines, 'Expected number character (invalid number -> %s)' % num)
        
        self.pos += len(num_found)
        self.pretty_print_tabs("number found: %s" % num_found)
        return num_found
    
    # used to print out the parse tree
    def pretty_print(self, name, start=True):
        # return if print false
        if (not self.print):
            return

        if (start):
            for i in range(self.tabs):
                print ('- ', end='')
            print ('%i <%s: start' % (self.tabs, name))
            self.tabs += 1
        else:
            self.tabs -= 1
            for i in range(self.tabs):
                print ('x ', end='')
            print ('%i >%s: end' % (self.tabs, name))
    
    # print out words w tabs
    def pretty_print_tabs(self, word):
        # return if print false
        if (not self.print):
            return

        for i in range(self.tabs):
            print ('- ', end='')
        print (' *%s' % word)

    # determine what error to show user
    def determine_errors(self):
        index = 0
        max_index = 0
        max_pos = 0
        errors = []
        for error in self.errors:
            if (error.pos >= max_pos):
                max_pos = error.pos
                max_index = index
            index += 1

        for error in self.errors:
            if (error.pos == max_pos):
                errors.append(error)

        return errors

    # --------------------------------
    #   PARSING FUNCTIONS
    # --------------------------------

    # starts parsing
    def parse(self, lines):
        # combine all text into a single string
        for element in lines:
            self.text += element
        self.lines = lines
        self.pos = 0
        self.len = len(self.text) - 1
        self.output = []
        self.tabs = 0
        self.errors = []

        # time parse
        if (self.time):
            start_time = time.perf_counter()

        # being parsing
        self.pretty_print('parse', True)
        try:
            self.program()
        except ParseError as error:
            errors = self.determine_errors()
            if (len(errors) > 0):
                print (errors[0])

            # count = 0
            # print ('Possible Errors:')
            # for error in errors:
            #     print ('%i %s' % (count, error))
            #     count += 1
            
            return None
        self.pretty_print('parse', False)

        # print parse time
        if (self.time):
            total_time = time.perf_counter() - start_time
            print ('Parse time: %f' % round(total_time, 3))

        return self.output

    #    program -> begin stmt_list end
    def program(self):
        self.pretty_print('program', True)
        try:
            self.match('begin', KeywordType.PRGRM_KEYWORD)
            self.stmt_list()
            self.match('end', KeywordType.PRGRM_KEYWORD)
        except ParseError as error1:
            self.errors.append(error1)
            raise error1
        self.pretty_print('program', False)
        return
    
    #  stmt_list -> id := expr stmt_list'
    #             | stmt_list'
    def stmt_list(self):
        self.pretty_print('stmt_list', True)
        prev_pos = self.pos
        try:
            id = self.get_id()
            self.match(':=', KeywordType.ASSIGNMENT)
            self.expr()
            self.stmt_list_prime()
        except ParseError as error1:
            self.errors.append(error1)
            try: 
                self.pos = prev_pos
                self.expr_prime()
            except ParseError as error2:
                self.errors.append(error2)
                raise error2
        self.pretty_print('stmt_list', False)
        return
    
    #       stmt -> id := expr
    #             | ϵ
    def stmt(self):
        self.pretty_print('stmt', True)
        prev_pos = self.pos
        try:
            id = self.get_id()
            self.match(':=', KeywordType.ASSIGNMENT)
            self.expr()
        except ParseError as error1:
            self.errors.append(error1)
            # check to see if stmt = ϵ
            self.pos = prev_pos
            word = self.get_next_word()
            if (word != 'end'):
                raise ParseError(self.pos, self.lines, 'Expected keyword \'end\' but found \'%s\'' % word)
            self.pretty_print_tabs('ϵ')
        self.pretty_print('stmt', False)
        return
    
    #       expr -> term expr'
    def expr(self):
        self.pretty_print('expr', True)
        try:
            self.term()
            self.expr_prime()
        except ParseError as error1:
            self.errors.append(error1)
            raise error1
        self.pretty_print('expr', False)
        return

    #       term -> factor term'
    def term(self):
        self.pretty_print('term', True)
        try:
            self.factor()
            self.term_prime()
        except ParseError as error1:
            self.errors.append(error1)
            raise error1
        self.pretty_print('term', False)
        return

        
    #     factor -> primary ^ factor
    #             | primary
    def factor(self):
        self.pretty_print('factor', True)
        prev_pos = self.pos
        try:
            self.primary()
            self.match('^', KeywordType.OPERATOR)
            self.factor()
        except ParseError as error1:
            self.errors.append(error1)
            try:
                self.pos = prev_pos
                self.primary()
            except ParseError as error2:
                self.errors.append(error2)
                raise error2
        self.pretty_print('factor', False)
        return

    #    primary -> id
    #             | num
    #             | ( expr )
    def primary(self):
        self.pretty_print('primary', True)
        prev_pos = self.pos
        try:
            id = self.get_id()
        except ParseError as error1:
            self.errors.append(error1)
            try:
                self.pos = prev_pos
                num = self.get_number()
            except ParseError as error2:
                self.errors.append(error2)
                try:
                    self.pos = prev_pos
                    self.match('(', KeywordType.PARENTHESIS)
                    self.expr()
                    self.match(')', KeywordType.PARENTHESIS)
                except ParseError as error3:
                    self.errors.append(error3)
                    raise error3
        self.pretty_print('primary', False)
        return

    # stmt_list' -> ; stmt stmt_list'
    #             | ϵ
    def stmt_list_prime(self):
        self.pretty_print('stmt_list_prime', True)
        prev_pos = self.pos
        try:
            self.match(';', KeywordType.STMT_TERMINATOR)
            self.stmt()
            self.stmt_list_prime()
        except ParseError as error1:
            self.errors.append(error1)
            # check to see if stmt_list' = ϵ
            self.pos = prev_pos
            word = self.get_next_word()
            if (word != 'end'):
                raise ParseError(self.pos, self.lines, 'Expected keyword \'end\' but found \'%s\'' % word)
            self.pretty_print_tabs('ϵ')
        self.pretty_print('stmt_list_prime', False)
        return

    #      expr' -> + term expr'
    #             | - term expr'
    #             | ϵ
    def expr_prime(self):
        self.pretty_print('expr_prime', True)
        prev_pos = self.pos
        try:
            self.match('+', KeywordType.OPERATOR)
            self.term()
            self.expr_prime()
        except ParseError as error1:
            self.errors.append(error1)
            self.pos = prev_pos
            try:
                self.pos = prev_pos
                self.match('-', KeywordType.OPERATOR)
                self.term()
                self.expr_prime()
            except ParseError as error2:
                self.errors.append(error2)
                # check to see if expr' = ϵ
                self.pos = prev_pos
                word = self.get_next_word()
                if (word == ';'):
                    raise ParseError(self.pos, self.lines, 'Expected character \';\' but found \'%s\'' % word)
                self.pretty_print_tabs('ϵ')
        self.pretty_print('expr_prime', False)
        return

    #      term' -> * factor term'
    #             | / factor term'
    #             | mod factor term'
    #             | ϵ
    def term_prime(self):
        self.pretty_print('term_prime', True)
        prev_pos = self.pos
        try:
            self.match('*', KeywordType.OPERATOR)
            self.factor()
            self.term_prime()
        except ParseError as error1:
            self.errors.append(error1)
            self.pos = prev_pos
            try:
                self.match('div', KeywordType.OPERATOR)
                self.factor()
                self.term_prime()
            except ParseError as error2:
                self.errors.append(error2)
                self.pos = prev_pos
                try:
                    self.match('mod', KeywordType.OPERATOR)
                    self.factor()
                    self.term_prime()
                except ParseError as error3:
                    self.errors.append(error3)
                    # check to see if term' = ϵ
                    self.pos = prev_pos
                    next_word = self.get_next_word()
                    if (next_word not in '+-;'):
                        raise ParseError (self.pos, self.lines, 'Expected character ( + | - | ; )')
                    self.pretty_print_tabs('ϵ')
        self.pretty_print('term_prime', False)
        return