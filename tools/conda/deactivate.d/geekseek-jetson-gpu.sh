#!/usr/bin/env bash

export LD_LIBRARY_PATH="${_GEEKSEEK_PREV_LD_LIBRARY_PATH-}"
unset _GEEKSEEK_PREV_LD_LIBRARY_PATH

if [[ "${_GEEKSEEK_SET_DISPLAY-}" == "1" ]]; then
  unset DISPLAY
  unset _GEEKSEEK_SET_DISPLAY
fi
if [[ "${_GEEKSEEK_SET_XAUTHORITY-}" == "1" ]]; then
  unset XAUTHORITY
  unset _GEEKSEEK_SET_XAUTHORITY
fi
