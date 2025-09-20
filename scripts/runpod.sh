#!/bin/bash
# usage: paste the full SSH string when prompted

printf "SSH over exposed TCP connection string:\n"
read RUNPOD_SSH

# extract IP as number or . after @ until space or end
RUNPOD_IP=$(echo "$RUNPOD_SSH" | sed -E 's/.*@([0-9.]+).*/\1/')

# extract port as number after -p flag until space or end
RUNPOD_PORT=$(echo "$RUNPOD_SSH" | sed -E 's/.*-p ([0-9]+).*/\1/')

# copy github key
scp -P $RUNPOD_PORT -i ~/.ssh/runpod -o StrictHostKeyChecking=yes \
    ~/.ssh/runpod_github root@$RUNPOD_IP:/root/.ssh/id_ed25519

# fix perms, add github to known_hosts, start shell
ssh -t -p $RUNPOD_PORT -i ~/.ssh/runpod root@$RUNPOD_IP '
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/id_ed25519
    ssh-keyscan github.com > ~/.ssh/known_hosts 2>/dev/null
    cd ~ && exec bash -l
'
