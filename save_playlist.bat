@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
uv run acestream_search > playlist.m3u
echo Playlist saved to playlist.m3u with UTF-8 encoding
