#!/bin/bash
# Usage: paste the full SSH string when prompted

printf "SSH over exposed TCP connection string:\n"
read RUNPOD_SSH

# Extract IP as number or . after @ until space or end
RUNPOD_IP=$(echo "$RUNPOD_SSH" | sed -E 's/.*@([0-9.]+).*/\1/')

# Extract port as number after -p flag until space or end
RUNPOD_PORT=$(echo "$RUNPOD_SSH" | sed -E 's/.*-p ([0-9]+).*/\1/')

# Verification prompt
echo ""
echo "Connecting to host $RUNPOD_IP port $RUNPOD_PORT."
read -p "Proceed? (yes/no): " confirm
if [[ "$confirm" != "yes" ]]; then
    echo "Aborted by user."
    exit 1
fi
echo ""

# Copy GitHub key
scp -P $RUNPOD_PORT -i ~/.ssh/runpod -o StrictHostKeyChecking=no \
    ~/.ssh/runpod_github root@$RUNPOD_IP:/root/.ssh/id_rsa

# Fix perms, add GitHub to known_hosts, start shell
ssh -t -p $RUNPOD_PORT -i ~/.ssh/runpod root@$RUNPOD_IP '
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan github.com >> ~/.ssh/known_hosts 2>/dev/null
    cd ~ && exec bash -l
'
