#!/bin/bash

chown root:`id -gn $SUDO_USER` /dev/uinput
chmod 660 /dev/uinput
