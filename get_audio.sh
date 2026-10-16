#!/bin/zsh
# Phase 1, step 1: download the audio of each talk into data/audio/.
# Safe to re-run: files already downloaded are skipped, so if one fails (403), just run it again. Add talks by adding lines below.
cd "${0:A:h}"
mkdir -p data/audio
while read -r name url; do
  [[ -z $name || $name == \#* ]] && continue
  yt-dlp --no-update --no-playlist -f 'ba[ext=m4a]/ba' -o "data/audio/$name.%(ext)s" "$url" </dev/null
done <<'EOF'
# name (date_talk)              YouTube link
# --- keynotes (scripted, rehearsed) ---
1998-01-06_macworld-1998        https://www.youtube.com/watch?v=I3FiBimJSrM
2001-10-23_ipod                 https://www.youtube.com/watch?v=Mc_FiHTITHE
2005-01-11_macworld-2005        https://www.youtube.com/watch?v=WT552cAttfU
2005-06-12_stanford             https://www.youtube.com/watch?v=UF8uR6Z6KLc
2007-01-09_iphone               https://www.youtube.com/watch?v=VQKMoT-6XSg
2008-01-15_macbook-air          https://www.youtube.com/watch?v=i9XU6wk_mWY
2010-01-27_ipad                 https://www.youtube.com/watch?v=zZtWlSDvb_k
2010-06-07_wwdc-iphone-4        https://www.youtube.com/watch?v=OY3ltJL4AEw
2011-06-06_wwdc-icloud          https://www.youtube.com/watch?v=zicXhcvV5SY
# --- unscripted: interviews, Q&A, talks (2026-10-12: the main source) ---
1983-06_idca-aspen-talk         https://www.youtube.com/watch?v=t9HmOz8H0qI
1985_next-team-brainstorm       https://www.youtube.com/watch?v=bsrk81TynxU
1992_mit-sloan-talk             https://www.youtube.com/watch?v=Gk-9Fd2mEnI
1994_svha-interview             https://www.youtube.com/watch?v=1QIDm0y2hnk
1995_lost-interview             https://www.youtube.com/watch?v=M6Oxl5dAnR0
1995-04-20_smithsonian-interview https://www.youtube.com/watch?v=5ox116SZKHc
1997-05-13_wwdc-fireside-qa     https://www.youtube.com/watch?v=_LsvdlaF5_k
2003-05_d1-interview            https://www.youtube.com/watch?v=oMyZwhzy5hE
2005-05_d3-interview            https://www.youtube.com/watch?v=bc3XI-09rWE
2007-05-30_d5-with-gates        https://www.youtube.com/watch?v=wvhW8cp15tk
2010-06-01_d8-interview         https://www.youtube.com/watch?v=KEQEV6r2l2c
# --- v4 (2026-10-15): more YOUNG unscripted Steve, like the 1983 Aspen talk he likes most ---
1980_first-interview            https://www.youtube.com/watch?v=N3ponn_6Fac
1980_insanely-great-talk        https://www.youtube.com/watch?v=0lvMgMrNDlg
1981-02-18_interview            https://www.youtube.com/watch?v=DbfejwP1d3c
1981_nightline-interview        https://www.youtube.com/watch?v=3H-Y-D3-j-M
1982-06-26_academy-of-achievement-talk https://www.youtube.com/watch?v=ymbD_a-G1IQ
1985_interview                  https://www.youtube.com/watch?v=u1GygpAA4c8
1985_lund-university-talk       https://www.youtube.com/watch?v=2qLuerYx2IA
1990_machine-changed-world-interview https://www.youtube.com/watch?v=6d1tlMziz-Y
1991-07-22_pc-ten-years-interview https://www.youtube.com/watch?v=OzZB5pZTslE
EOF
