#!/bin/bash
mkdir -p /tmp/fc; rm -f /tmp/fc/*
S="curl -s --unix-socket /run/kvmd/kvmd.sock"
/tmp/k key Home; sleep 0.3; /tmp/k key ArrowDown; sleep 0.3; /tmp/k key ArrowDown; sleep 0.3; /tmp/k snap; cp /tmp/s.jpg /tmp/fc/000-picker.jpg; /tmp/k key Enter
t0=$(date +%s); n=0; off=0
while [ $(( $(date +%s)-t0 )) -lt 240 ]; do
  n=$((n+1)); f=$(printf "/tmp/fc/%04d.jpg" $n)
  $S "http://localhost/streamer/snapshot" -o $f
  if head -c1 $f | grep -q "{"; then rm -f $f; off=$((off+1)); [ $off -ge 6 ] && break; else off=0; fi
  sleep 0.25
done
ls /tmp/fc | wc -l
