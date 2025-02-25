#!/bin/zsh

# DaVinci Resolve Python API環境設定
RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion"
FUSION_SCRIPT_MOD="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"

# PYTHONPATHを設定
export PYTHONPATH="$RESOLVE_SCRIPT_API:$RESOLVE_SCRIPT_LIB:$FUSION_SCRIPT_MOD:$PYTHONPATH"

# スクリプトに実行権限を付与
chmod +x davinci_resolve_generator.py

echo "DaVinci Resolve Python API環境を設定しました"
echo "PYTHONPATH = $PYTHONPATH" 