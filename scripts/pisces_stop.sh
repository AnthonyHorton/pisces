#!/bin/bash
byobu-tmux switch-client -t pisces # Make sure we're sending shutdown commands to the right session

byobu-tmux send-keys -t 2 -l 'pisces.stop_all()' # Shutdown pisces
byobu-tmux send-keys -t 2 'C-m'
sleep 10s # Give it time
byobu-tmux send-keys -t 2 'C-d'
sleep 5s
byobu-tmux send-keys -t 2 'C-m' # Exit console

byobu kill-session -t pisces
