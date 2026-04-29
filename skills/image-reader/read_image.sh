#!/bin/bash
if [ $# -ne 1 ]; then
  echo "Usage: $0 <image-file>"
  exit 1
fi
identify "$1"