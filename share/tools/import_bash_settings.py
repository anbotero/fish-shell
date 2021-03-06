#!/usr/bin/env python

"""
<OWNER> = Siteshwar Vashisht 
<YEAR> = 2012 

Copyright (c) 2012, Siteshwar Vashisht 
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os, sys, re

import bash_converter

config_file = None
output_buff = ""
prompt_buff = ""
i = 0
quote_started = False
bash_builtins = ["export"]

#Remove leading and trailing single quotes from a string
def remove_single_quotes(input):
    start = 0
    end = len(input)
    if input[0] == "'":
        start = 1
    if input[end-1] == "'":
        end = end - 1 
    return input[start:end]

#Find outside quotes
def contains_outside_quotes(input, ch):
    in_quotes = False

    i = 0
    
    while i < len(input):
        if input[i] == ch and in_quotes == False:
            return True
        elif input[i] == '\\' and in_quotes == True:
            i = i+1    
        elif input[i] == '"':
            in_quotes = not in_quotes
        elif input[i] == "'" and not in_quotes:
            i = i + 1
            while input[i] != "'":
                i = i + 1    

        i = i + 1

    return False 


#Replace characters outside double quotes
def replace_outside_quotes(input, oldchar, newchar, change_all = True):
    in_quotes = False
    newstr = [] 

    i = 0
    
    while i < len(input):
        if input[i] == oldchar and in_quotes == False:
            newstr.append(newchar)
            i = i+1

            if change_all == True:
                continue    
            else:
                while i < len(input):
                    newstr.append(input[i])
                    i = i + 1
                #Break loop and return all the characters in list by joining them
                break    
        elif input[i] == '\\' and in_quotes == True:
            newstr.append(input[i])
            i = i+1    
        elif input[i] == '"':
            in_quotes=not in_quotes
        elif input[i] == "'" and not in_quotes:
            newstr.append(input[i])
            i = i + 1
            while input[i] != "'":
                newstr.append(input[i])
                i = i + 1    

        newstr.append(input[i])
        i = i + 1

    return ''.join(newstr)    


#Parse input passed to the script
def parse_input(input):
    global output_buff
    env_regex = re.compile("(.*?)=(.*)")    
    env_regex_matched = re.search(env_regex, input)

    while env_regex_matched != None:
        env_name = env_regex_matched.group(1)
        env_value = env_regex_matched.group(2)
        env_var = env_regex_matched.group(0)    

        if env_name[:5] == "alias":
            add_alias(env_name[6:], env_value)
            input = input[env_regex_matched.end():]

        elif env_name == "PS1":
            if len(env_value) > 0:
                parse_bash_prompt(env_value)    
            input = input[env_regex_matched.end():]

        elif env_name == "PATH":
            output_buff += "set -x " + env_name + ' ' + env_value.replace(":"," ")
            input = input[env_regex_matched.end():]

        else:
            full_value = env_value 
            input = input[env_regex_matched.end():]
            while len(env_value) > 0 and env_value[len(env_value)-1] == "\\":
                one_line_regex = re.compile("\n.*")
                one_line_matched = re.search(one_line_regex, input)
                env_value = one_line_matched.group(0)
                full_value = full_value + env_value
                input = input[one_line_matched.end():]

            output_buff += "set_default " + env_name + ' "' + full_value + '"'
        #Move to next line
        output_buff += "\n"
        config_file.write(output_buff)
        output_buff = ""
        env_regex_matched = re.search(env_regex, input)

#Add an alias as a function in fish
def add_alias(alias_name, alias_value):
        global output_buff
        alias_value = remove_single_quotes(alias_value)

        output_buff += "function " + alias_name
        output_buff = bash_converter.parse_input(alias_value, output_buff)
        output_buff += " $argv\nend;\n"

def parse_control_sequence():
    ch = next_prompt_char()
    ch2 = None
    
    while (ch != ""):
        if ch == "\\":
            ch2 = next_prompt_char()
            if (ch2 == "]"):
                return
        ch = next_prompt_char()


def is_digit(ch):
    if ch>='0' and ch<='9': 
        return True
    return False

def set_prompt_buff(value):
    global i, buff
    i = 0
    buff = value 

def next_prompt_char():
    global i, buff
    if (i < len(buff)):
        next = buff[i] 
        i = i+1
    else:
        next = ""
    return next

def unget_prompt_char():
    global i
    i = i - 1

def add_to_echo(str, is_special=True):
    global quote_started
    
    if (is_special == True):
        if (quote_started == True):
            config_file.write('"')
            quote_started = False
    else:
        if (quote_started == False):
            config_file.write('"')
            quote_started = True

    config_file.write(str)

def check_end_quote():
    global quote_started

    if quote_started == True:
#        print "Ending quote",
        config_file.write('"')

def parse_bash_prompt(bash_prompt):
    set_prompt_buff(bash_prompt)

    config_file.write("function fish_prompt\n")

    if ("\\$" in bash_prompt):
        config_file.write("\tif test (id -u) -eq \"0\"\n") 
        config_file.write("\t\tset uid_prompt \"#\"\n") 
        config_file.write("\telse\n") 
        config_file.write("\t\tset uid_prompt \"\\$\"\n") 
        config_file.write("\tend;\n")

    config_file.write('\techo -n ')
    
    ch = next_prompt_char()
    ch2 = None
    while (ch != ""):
        if ( ch == "\\"):
            ch2 = next_prompt_char()    
            if (ch2 == ""):
                continue
            elif (ch2 == "a"):
                add_to_echo('\\a')
            elif (ch2 == "d"):
                add_to_echo(' (date +"%a %b %d")')
            elif (ch2 == "e"):
                add_to_echo('\e')
            elif (ch2 == "h"):
                add_to_echo("(hostname | cut -d\".\" -f1)")
            elif (ch2 == "H"):
                add_to_echo("(hostname)")
            elif (ch2 == "j"):
                add_to_echo("(jobs | wc -l)")
            elif (ch2 == "l"):
                add_to_echo("basename (tty)")
            elif (ch2 == "n"):
                add_to_echo(' \\n ')
            elif (ch2 == "r"):
                add_to_echo(' \\r ')
            elif (ch2 == "s"):
                add_to_echo("fish", False)
            elif (ch2 == "t"):
                add_to_echo('(date +"%H:%M:%S")')
            elif (ch2 == "T"):
                add_to_echo('(date +"%I:%M:%S")')
            elif (ch2 == "@"):
                add_to_echo('(date +"%I:%M %p")')
            elif (ch2 == "u"):
                add_to_echo("$USER")
            elif (ch2 == "w"):
                add_to_echo("(pwd)")
            elif (ch2 == "W"):
                add_to_echo("(basename ( pwd ) )")
            elif (ch2 == "$"):
                add_to_echo("$uid_prompt ")    
            elif (is_digit(ch2)):
                temp = int(ch2)
                ch = next_prompt_char()
                if (is_digit(ch)):
                    temp = (temp*8) + int(ch)
                else:
                    add_to_echo(chr(temp), False)
                    unget_prompt_char()    
                ch = next_prompt_char()
                if (is_digit(ch)):
                    temp = ((temp/10)*64) + ((temp%10)*8) + int(ch)
                    add_to_echo(chr(temp), False)
                else:
                    add_to_echo(chr(temp), False)
                    unget_prompt_char()    
            elif (ch2 == "\\"):
                add_to_echo("\\")
            elif (ch2 == "["):
                parse_control_sequence()
            elif (ch2 ==  "]"):
#                print "Unexpected ]"
                pass
            elif (ch2 == "v" or ch2 == "V"):
                add_to_echo("(fish -v 2>| cut -d\" \" -f3)")
            else:
#                print "Unknown escape character"
                pass
        else:
            if (ch == "$"):
                add_to_echo("\\", False)

            add_to_echo(ch,False)
        ch = next_prompt_char()
    check_end_quote()
    config_file.write("\nend\n")

if __name__  == "__main__":
    input = sys.stdin.read()
    config_file = open("{0}/.config/fish/bash_config.fish".format(os.environ["HOME"]),"a") 
    parse_input(input)
