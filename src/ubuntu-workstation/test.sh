#!/bin/sh
set -e
which xfce4-session
vncserver --help 2>&1 | head -1
websockify --help 2>&1 | head -1
firefox --version
which start-vnc
