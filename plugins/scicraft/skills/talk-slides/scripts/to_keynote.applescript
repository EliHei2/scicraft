-- Open a built .pptx in Keynote, set the presenter notes from build/notes, make every movie loop, set a plain
-- dissolve between slides, save a .key, export slide images and a PDF with all build stages, and close only the
-- document this script opened. Every step is logged to QA_DIR/convert.log, so a stall shows where it stopped.
--
--   osascript to_keynote.applescript BUILT.pptx NOTES_DIR|- OUT.key QA_DIR [MAX_WAIT_S=120]
--
-- Before running: make sure the author is not working in Keynote. Launching it can reopen their saved decks, and
-- the deck you open lands on their screen. Launch it clean first:
--   open -a Keynote --args -ApplePersistenceIgnoreState YES
-- and run every osascript call with a time limit:
--   perl -e 'alarm 300; exec @ARGV' osascript to_keynote.applescript ...
-- Notes are read by the shell, not by Keynote (a sandboxed app asked to read a file stops on a permission prompt).
-- The reference that "open" returns is not usable for decks with several movies, so the script waits until a
-- document with the file's name has slides. Never force-quit Keynote from a script while the author may have
-- documents open; if this stalls, see references/traps.md (Keynote).
-- Ported from the conversion that worked once in the original project; the read-back afterwards (count the build
-- stages in the PDF, look at the exported images, check that the movies still play) is yours.
property logFile : ""

on logit(m)
	do shell script "echo " & quoted form of ((do shell script "date +%H:%M:%S") & " " & m) & " >> " & quoted form of logFile
end logit

on run argv
	if (count of argv) < 4 then return "usage: osascript to_keynote.applescript BUILT.pptx NOTES_DIR|- OUT.key QA_DIR [MAX_WAIT_S]"
	set pptxPath to item 1 of argv
	set notesDir to item 2 of argv
	set keyPath to item 3 of argv
	set qaDir to item 4 of argv
	set maxWait to 120
	if (count of argv) > 4 then set maxWait to (item 5 of argv) as integer
	set logFile to qaDir & "/convert.log"
	do shell script "mkdir -p " & quoted form of qaDir
	set namePart to do shell script "basename " & quoted form of pptxPath & " .pptx"
	my logit("start " & namePart)
	tell application "Keynote"
		activate
		open (POSIX file pptxPath)
		set d to missing value
		set t to 0
		repeat while t < maxWait
			delay 2
			set t to t + 2
			try
				repeat with dd in documents
					if (name of dd) contains namePart and (count of slides of dd) > 0 then
						set d to contents of dd
						exit repeat
					end if
				end repeat
			end try
			if d is not missing value then exit repeat
		end repeat
		if d is missing value then
			my logit("no document after " & t & " s")
			return "NO DOCUMENT in Keynote after " & t & " s"
		end if
		my logit("opened after " & t & " s")
		delay 3
		set info to {}
		tell d
			set n to count of slides
			repeat with i from 1 to n
				set transition properties of slide i to {transition effect:dissolve, transition duration:0.5, transition delay:0.0, automatic transition:false}
				if notesDir is not "-" then
					set nn to text -2 thru -1 of ("0" & i)
					set nt to (do shell script "cat " & quoted form of (notesDir & "/" & nn & ".txt") & " 2>/dev/null || true")
					set presenter notes of slide i to nt
				end if
				tell slide i
					repeat with m in movies
						set repetition method of m to loop
					end repeat
					set end of info to ((i as text) & ": movies " & (count of movies) & ", images " & (count of images) & ", text items " & (count of text items))
				end tell
			end repeat
		end tell
		my logit("slides set: " & n)
		save d in (POSIX file keyPath)
		my logit("saved .key")
		export d to (POSIX file qaDir) as slide images with properties {image format:PNG, skipped slides:false}
		my logit("exported images")
		export d to (POSIX file (qaDir & "/stages.pdf")) as PDF with properties {all stages:true, PDF image quality:Best}
		my logit("exported stages pdf")
		close d saving no
		my logit("closed")
		set AppleScript's text item delimiters to linefeed
		return info as text
	end tell
end run
