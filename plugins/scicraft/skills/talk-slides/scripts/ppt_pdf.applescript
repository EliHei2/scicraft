-- Read a deck back in Microsoft PowerPoint: open it, report for each slide the shapes, the movies and the animation
-- effects in its timeline's main sequence, save it as PDF, close it. Compare the counts with the file as built:
--
--   open -a "Microsoft PowerPoint" DECK.pptx          (first, through the system: a scripted open stops on
--                                                       "Grant File Access"; it puts the deck on the author's
--                                                       screen, so say so before)
--   perl -e 'alarm 120; exec @ARGV' osascript ppt_pdf.applescript DECK.pptx OUT.pdf > readback.txt
--   python3 readback_compare.py DECK.pptx readback.txt
--
-- Output: one line per slide, "slide 3: shapes 7, movies 1, effects 2", then "slides N". A count PowerPoint would
-- not give is printed as "?". A slide whose movie count matches but whose effect count is 0 has lost the timing
-- that starts its clip. This proves that PowerPoint imports the file and keeps the timing; it does not prove that
-- clips start in a show, so say that in the report. A scripted Save as PDF may write inside PowerPoint's sandbox
-- (~/Library/Containers/com.microsoft.Powerpoint/Data/Documents/): look for the file there.
-- The per-slide movie and effect counts are Suggested, not yet tested in real work (the slide and shape counts were).
on run argv
	if (count of argv) < 2 then return "usage: osascript ppt_pdf.applescript DECK.pptx OUT.pdf"
	set src to item 1 of argv
	set pdf to item 2 of argv
	tell application "Microsoft PowerPoint"
		launch
		open (POSIX file src)
		delay 6
		set p to active presentation
		set n to count of slides of p
		set report to ""
		repeat with i from 1 to n
			set s to slide i of p
			set nShapes to "?"
			set nMovies to "?"
			set nEffects to "?"
			try
				set nShapes to (count of shapes of s) as string
			end try
			try
				set nMovies to (count of (shapes of s whose shape type is shape type media)) as string
			end try
			try
				set nEffects to (count of effects of main sequence of timeline of s) as string
			end try
			set report to report & "slide " & i & ": shapes " & nShapes & ", movies " & nMovies & ", effects " & nEffects & linefeed
		end repeat
		save p in (POSIX file pdf) as save as PDF
		delay 2
		close p saving no
		return report & "slides " & n
	end tell
end run
