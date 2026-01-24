#!/bin/bash
# Sync script: Pull from upstream, preserve local changes, push to fork

echo "🔄 Syncing PyeChat..."

# Stash any local changes
if ! git diff-index --quiet HEAD --; then
    echo "📦 Stashing local changes..."
    git stash push -m "Auto-stash before sync"
    STASHED=1
else
    STASHED=0
fi

# Pull from upstream
echo "📥 Pulling from upstream (ComputerTech312)..."
if git pull upstream main; then
    echo "✅ Pulled successfully"
else
    echo "❌ Pull failed"
    exit 1
fi

# Restore stashed changes if any
if [ $STASHED -eq 1 ]; then
    echo "📦 Restoring your local changes..."
    if git stash pop; then
        echo "✅ Changes restored"
    else
        echo "⚠️  Merge conflicts - please resolve manually"
        exit 1
    fi
fi

# Push to your fork
echo "📤 Pushing to your fork (lord3nd3r)..."
if git push origin main; then
    echo "✅ Pushed successfully"
else
    echo "🔄 Normal push failed, trying force-with-lease..."
    if git push origin main --force-with-lease; then
        echo "✅ Force-pushed successfully"
    else
        echo "❌ Push failed"
        exit 1
    fi
fi

echo "🎉 Sync complete!"
