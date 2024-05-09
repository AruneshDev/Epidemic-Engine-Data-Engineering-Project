#!/usr/bin/env python3
"""mapper.py"""

# input comes from STDIN (standard input)
# write some useful code here and print to STDOUT
import sys

# Process each line from stdin
for line in sys.stdin:
    # Skip the header
    if line.startswith('EventID'):
        continue
    
    # Split the line into components
    _, _, _, event_location, _ = line.strip().split(',')
    
    # Emit the event type and a count of 1
    print(f'{event_location}\t1')