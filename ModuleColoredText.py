#!/usr/bin/python3
'''
********************************************************************************

Python Script: Text Output Module
Writter: Mojtaba Mansour Abadi
Date: 7 September 2017

This Python script is compatible with Python 2.7.
The script is used to colour and changethe style of text. Three possible
modes are avaiable: 1) no colour, 2) console, and 3) shell

********************************************************************************
'''


import sys


#################################################
NO_COLORED = 0
CON_COLORED = 1
SHL_COLORED = 2
#################################################


class ColoredText:
    
    Shell_FG = {'black':        'SYNC',
                'dark red':     'COMMENT',
                'red':    	'stderr',
                'green':        'STRING',
                'yellow':       'KEYWORD',
                'blue':         'DEFINITION',
                'purple':       'BUILTIN',
                'cyan':         'console',
                'white':        'hit',
                'black+pink':   'ERROR',
                'black+grey':   'sel'
                }  # available foreground colour for shell mode (brown colour is considered to be cyan)
    
    Console_Style = {'normal':      0,
                     'fg light':    1,
                     'fg dark':     2,
                     'italic':      3,
                     'underlined':  4,
                     'bg light':    5,
                     'bg dark':     6,
                     'reversed':    7
                     }  # available styles for console mode
    
    Console_FG = {'black':      30,
                  'red':        31,
                  'green':      32,
                  'yellow':     33,
                  'blue':       34,
                  'purple':     35,
                  'cyan':       36,
                  'white':      37
                  }  # available foreground colour for console mode

    Console_BG = {'black':      40,
                  'red':        41,
                  'green':      42,
                  'yellow':     43,
                  'blue':       44,
                  'purple':     45,
                  'cyan':       46,
                  'white':      47
                  }  # available background colour for console mode

    Print = None  # use this function to print a message at the standard console
	
    Shell = None
	
    def __init__(self, text_mode = NO_COLORED):
        if(text_mode == CON_COLORED):
            self.Print = self.Prn_Con_Col
            pass
        elif(text_mode == SHL_COLORED):
            try:
                self.Shell = sys.stdout.shell
                pass
            except AttributeError:
                raise RuntimeError("you must run this program in IDLE")
            pass
            self.Print = self.Prn_Shl_Col
        else:
            self.Print = self.Prn_No_Col
            pass
        pass

    def Prn_No_Col(self, text = '', fg = '', bg = '', style = '', src = ''):
        print(src  + text)
        pass

    def Prn_Shl_Col(self, text = '', fg = 'black', bg = '', style = '', src = ''):
        self.Shell.write(src + text + '\n', self.Shell_FG[fg])
        pass

    def Prn_Con_Col(self, text = '', fg = 'white', bg = 'black', style = 'normal', src = ''):
        frm = ';'.join([str(self.Console_Style[style]), str(self.Console_FG[fg]), str(self.Console_BG[bg])])
        S = '\033[' + frm + 'm' + src + text + '\033[0m'
        print(S)
        pass


def main():
    CT = ColoredText(text_mode = SHL_COLORED)
    CT.Print('Hello', 'dark red', 34, 55)

if __name__ == '__main__':
    main()
