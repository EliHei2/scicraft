#!/bin/bash
# Bisect a Keynote import that stalls: try to open each given .pptx in Keynote and report OK (slides, movies) or
# FAIL. Make one test deck per feature first (movies, fade-ins, notes written into the file, text-frame settings),
# then the deck without movies, each movie alone, and two, three, six movies together. In the original project
# every piece opened on its own: the stall came from the state Keynote was in, not from the deck.
#
#   bash keynote_try.sh [--may-restart] DECK.pptx [DECK.pptx ...]
#
# A refused file leaves a modal alert that scripts cannot dismiss, and every later open then hangs. This script
# never force-quits a Keynote that was already running (the author's decks may be open in it): it stops at the
# first failure and says so, and the author closes the alert. Only with --may-restart, and only if this script
# itself launched Keynote, is Keynote stopped and launched again without restoring windows. Only documents this
# script opened are closed. Needs macOS, Keynote, osascript and perl (for the time limit).
set -u
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] || [ $# -eq 0 ]; then
  sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
fi
MAY_RESTART=0
if [ "$1" = "--may-restart" ]; then MAY_RESTART=1; shift; fi
LAUNCHED_HERE=0
if ! pgrep -x Keynote >/dev/null; then
  open -a Keynote --args -ApplePersistenceIgnoreState YES
  perl -e 'select(undef,undef,undef,7)'
  LAUNCHED_HERE=1
fi
status=0
for f in "$@"; do
  out=$(perl -e 'alarm 100; exec @ARGV' osascript -e "tell application \"Keynote\"
activate
open (POSIX file \"$f\")
set t to 0
repeat while t < 60
delay 2
set t to t + 2
try
set d to front document
set ns to count of slides of d
if ns > 0 then
set nm to 0
repeat with i from 1 to ns
set nm to nm + (count of movies of slide i of d)
end repeat
close d saving no
return \"OK after \" & t & \" s, slides \" & ns & \", movies \" & nm
end if
end try
end repeat
return \"FAIL no document\"
end tell" 2>&1 | tail -1)
  echo "$(basename "$f"): ${out:-FAIL timeout}"
  case "$out" in
    OK*) ;;
    *)
      status=1
      if [ $MAY_RESTART -eq 1 ] && [ $LAUNCHED_HERE -eq 1 ]; then
        kill -TERM "$(pgrep -x Keynote)" 2>/dev/null
        perl -e 'select(undef,undef,undef,3)'
        open -a Keynote --args -ApplePersistenceIgnoreState YES
        perl -e 'select(undef,undef,undef,7)'
      else
        echo "stopped: Keynote may show an alert now. Ask the author to close it; this script does not quit Keynote."
        exit 1
      fi
      ;;
  esac
done
exit $status
