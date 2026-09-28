tell application "Mail"
  set mb to mailbox "INBOX" of account "Google"
  set out to ""
  repeat with i from 1 to 40
    set m to message i of mb
    set s to subject of m as text
    set f to sender of m as text
    if s contains "Typebot" or s contains "Cal.com" or s contains "Formbricks" or s contains "locale" or f contains "typebot" or f contains "cal.com" or f contains "formbricks" or f contains "jan.ai" then
      set out to out & (date received of m as text) & " | " & f & " | " & s & linefeed
    end if
  end repeat
  if out is "" then set out to "NO MATCHES in top 40 - no replies yet"
  return out
end tell
