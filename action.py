#!/usr/bin/env python3

import signal
import sys


###
# MAIN METHOD
###

def main():
    print()
    print(' * Composite action test')
    print()


# Handle interrupt
def signal_handler(_, __):
    print(' ')
    sys.exit(0)


####
# MAIN
####

# Set up Ctrl-C handler
signal.signal(signal.SIGINT, signal_handler)

# Invoke main method
if __name__ == '__main__':
    main()
