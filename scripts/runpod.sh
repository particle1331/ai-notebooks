#!/bin/bash
printf "\nSSH over exposed TCP connection string:\n"
read RUNPOD_SSH

RUNPOD_IP=$(echo "$RUNPOD_SSH" | sed -E 's/.*@([0-9.]+).*/\1/')
RUNPOD_PORT=$(echo "$RUNPOD_SSH" | sed -E 's/.*-p ([0-9]+).*/\1/')
echo ""
echo "IP:   $RUNPOD_IP"
echo "Port: $RUNPOD_PORT"

# Verification prompt
read -p "Are the captured values correct? (yes/no) " confirm
if [[ "$confirm" != "yes" ]]; then
    echo "Aborted by user."
    exit 1
fi
echo ""

ssh-keyscan -p $RUNPOD_PORT $RUNPOD_IP >> ~/.ssh/known_hosts

scp -P $RUNPOD_PORT -i ~/.ssh/runpod \
    ~/.ssh/runpod_github root@$RUNPOD_IP:/root/.ssh/runpod_github

ssh -t -p $RUNPOD_PORT -i ~/.ssh/runpod root@$RUNPOD_IP '
    # Set secure permissions for SSH directory and key
    chmod 700 ~/.ssh
    chmod 600 ~/.ssh/runpod_github

    # Add GitHub to known_hosts and set permissions
    ssh-keyscan github.com >> ~/.ssh/known_hosts
    chmod 644 ~/.ssh/known_hosts

    # Start SSH agent and load the key
    eval "$(ssh-agent -s)" > /dev/null;
    ssh-add ~/.ssh/runpod_github

    # Launch interactive shell to keep the session alive
    cd ~ && exec bash -l
'
