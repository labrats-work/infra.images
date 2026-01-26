#!/bin/sh
set -e
xfce4-session --version
vncserver --help 2>&1 | head -1
websockify --help 2>&1 | head -1
firefox --version
which start-vnc
