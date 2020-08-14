#!/bin/bash
# Script to check if we should trigger a release or not.

# Get the message of the most recent commit
message=$(git show HEAD --pretty=format:%s | tr '[:upper:]' '[:lower:]')

case $message in
    patch*)
        kind="patch";;
    minor*)
        kind="minor";;
    major*)
        kind="major";;
    *)
        kind="";;
esac

if [ -z "$kind" ]; then
    echo "There is nothing to do."
else
    echo "Cutting ${kind} release!"
    echo "::set-output name=yes::true"
    echo "::set-output name=kind::${kind}"
fi