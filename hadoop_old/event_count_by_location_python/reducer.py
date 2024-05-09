#!/usr/bin/env python3
"""reducer.py"""

# input comes from STDIN (standard input)
# write some useful code here and print to STDOUT

import sys
from collections import defaultdict

# Create a dictionary to hold the event type counts
event_counts = defaultdict(int)

# Process each line from stdin
for line in sys.stdin:
    # Split the line into components
    event_location, count = line.strip().split('\t')
    
    # Sum the counts for each event type
    event_counts[event_location] += int(count)

# Emit the total count for each event type
for event_location, count in event_counts.items():
    print(f'{event_location}\t{count}')