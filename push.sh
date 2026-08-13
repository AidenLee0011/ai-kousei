#!/bin/sh
# One command to finish the publish once the token can write to the repo.
#   GITHUB_AIDEN_PAT=... sh push.sh
git -c credential.helper= \
    -c credential.helper='!f(){ echo username=AidenLee0011; echo password=$GITHUB_AIDEN_PAT; }; f' \
    push -u origin main
