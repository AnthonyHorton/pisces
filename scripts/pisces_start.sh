#!/bin/bash
byobu-tmux new-session -d -s pisces -n pisces # Create a new detached Byobu session called pisces
byobu-tmux split-window -v -p 67
byobu-tmux split-window -v -p 33

byobu-tmux send-keys -t 0 'cd $PISCES/logs' 'C-m'
byobu-tmux send-keys -t 0 'grc tail -n 1000 -F pisces.log' 'C-m' # Start watching the log

byobu-tmux send-keys -t 0 'cd $PISCES/data' 'C-m'
byobu-tmux send-keys -t 0 'tail -n 1000 -F pisces.dat' 'C-m' # Start watching the data

byobu-tmux send-keys -t 2 'cd $PISCES' 'C-m'
byobu-tmux send-keys -t 2 -R 'ipython' 'C-m'
sleep 10s # Need to wait a while for the console to start, otherwise console commands get lost
byobu-tmux send-keys -t 2 'from pisces.core import Pisces' 'C-m'
sleep 3s # Waiting for the import prevents formatting getting messed up
byobu-tmux send-keys -t 2 -l 'pisces = Pisces()' # Literal flag needed for this one
byobu-tmux send-keys -t 2 'C-m' # Start pisces
