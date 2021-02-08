#!/usr/bin/env python3
# coding=utf-8
import os.path
import sys
from my_parser import MyParser
from my_parser import ParseError

# --------------------------------
#   Marco Ravelo
#   CSCE 434 - Compiler Design
#   Assignment #1 - 2/2/2021 
#   file: main.py
# --------------------------------

# Resources used:
# - https://www.booleanworld.com/building-recursive-descent-parsers-definitive-guide/#content
# - https://cyberzhg.github.io/toolbox/left_rec

if __name__ == '__main__':

    # command line arguments
    print_tree = False
    time_parse = False
    if ('-help' in sys.argv):
        print ('\tThis program reads text from a text file and parses\n\
        the lines to be translated into hypothetical stack\n\
        machine code. The program uses a recursive descent\n\
        compiler to parse the text.\n\n\
        [Command Argument Commands]\n\
        -help\t: prints out help for the program\n\
        -print\t: prints out parse tree\n\
        -time\t: times how long parsing takes\n\
        \n\
        This program was written primarily for Python 3.9.1 64-bit.\n\
        It is not guarenteed to work on any other version.\n')
        sys.exit()
    if ('-print' in sys.argv):
        print_tree = True
    if ('-time' in sys.argv):
        time_parse = True

    while (True):
        # prompt user for input file name
        input_file = input ('Input file name [Default input.txt]: ')

        # check if blank, change to default
        if (input_file == ''):
            input_file = 'input.txt'

        if (os.path.isfile(input_file)):
            break
        else:
            print ('ImportError: could not find file', input_file)

    print ('Found file', input_file)

    # open file and read all lines (removing any '\n' chars)
    with open (input_file, 'r') as open_file:
        lines = open_file.readlines()

    # parse the text to generate stack code
    parser = MyParser(print_tree, time_parse)
    output = parser.parse(lines)

    if (output != None):
        print ('Finished parsing with no errors.')
        # print output
        print ('\nPrinting generated output:')
        for node in output:
            print (node)


    
