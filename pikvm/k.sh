#!/bin/bash
# usage: k key Enter | k click X Y (in 1280x720 coords) | k text "..." | k snap | k combo ControlLeft,AltLeft,Delete
S="curl -s --unix-socket /run/kvmd/kvmd.sock"
case "$1" in
  key) $S -X POST "http://localhost/hid/events/send_key?key=$2" >/dev/null;;
  combo) $S -X POST "http://localhost/hid/events/send_shortcut?keys=$2" >/dev/null;;
  click) x=$(( $2 * 65535 / 1280 - 32768 )); y=$(( $3 * 65535 / 720 - 32768 ))
         $S -X POST "http://localhost/hid/events/send_mouse_move?to_x=$x&to_y=$y" >/dev/null; sleep 0.3
         $S -X POST "http://localhost/hid/events/send_mouse_button?button=left&state=true" >/dev/null; sleep 0.1
         $S -X POST "http://localhost/hid/events/send_mouse_button?button=left&state=false" >/dev/null;;
  text) $S -X POST --data-binary "$2" "http://localhost/hid/print?limit=0" >/dev/null;;
  snap) for i in 1 2 3 4 5 6 7 8; do $S "http://localhost/streamer/snapshot" -o /tmp/s.jpg; head -c1 /tmp/s.jpg | grep -q "{" || break; sleep 1.5; done;;
esac
