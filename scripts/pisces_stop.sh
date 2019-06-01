#!/bin/bash
byobu-tmux switch-client -t pisces # Make sure we're sending shutdown commands to the right session

byobu-tmux send-keys -t 1 -l 'pisces.stop_all()' # Shutdown pisces
byobu-tmux send-keys 'C-m'
sleep 5s # Give it time
byobu-tmux send-keys 'C-d' 'C-m' # Exit console

byobu kill-session -t pisces
