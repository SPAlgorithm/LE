# Ladhe's Quad Conjecture videos (built 2026-09-02 with Higgsfield)

YouTube (uploaded 2026-09-03; the links stay the same when the videos go public):
- Video 1, "Ladhe's Quad Conjecture: A New Pattern in Prime Quadruplets": https://youtu.be/_XSOJ0Yj77Q
- Video 2, "Build Any Number From Prime Quadruplets (Ladhe's Quad Conjecture, Part 2)": https://youtu.be/JNWvt3hS540

Hosted MP4 copies (Higgsfield CDN, may not be permanent):

Video 1, "A new pattern in prime numbers" (28 min 31 s, 1920x1080, narration + burned captions, 724 MB, revision 5):
https://d2ol7oe51mr4n9.cloudfront.net/user_3GBezdTDuv0nklNP50XdEhyeDgq/5c5b63b5-1523-4790-8afc-437a3678ba0e.mp4
(earlier revisions still online: revision 4 https://d2ol7oe51mr4n9.cloudfront.net/user_3GBezdTDuv0nklNP50XdEhyeDgq/dbd8c21d-2e8f-4314-bdb3-a5025d3199bb.mp4 ; revision 3 https://d2ol7oe51mr4n9.cloudfront.net/user_3GBezdTDuv0nklNP50XdEhyeDgq/b06f8dc4-b07e-40fa-9922-2967c76033b0.mp4)
(revision 2, 27 min 19 s, still online: https://d2ol7oe51mr4n9.cloudfront.net/user_3GBezdTDuv0nklNP50XdEhyeDgq/6d26e87b-3ab1-454a-bfae-e0dded44904a.mp4)

Video 2, "Build any number from prime quadruplets" (10 min 57 s, 232 MB):
https://d2ol7oe51mr4n9.cloudfront.net/user_3GBezdTDuv0nklNP50XdEhyeDgq/64ad3026-fd9a-4828-b83e-5c3cb0949ac4.mp4

Thumbnails: thumbnail_video1.png, thumbnail_video2.png (also in this folder).

How they were made: scripts (script_video1.md, script_video2.md) -> narration lines via Higgsfield text2speech_v2
(ElevenLabs, voice Cillian) -> 20 hero illustrations (seedream_v5_pro, Editorial Motion Graphics preset) ->
build/gen_edit.py generates a higgsedit edit.jsx (native motion graphics) with Whisper-timed captions
(build/captions.py) -> rendered in the Higgsfield sandbox (build/build.sh). Total cost about 160 credits.

Local copies: Ladhe_Quad_Conjecture_Video1.mp4 (revision 5, 724 MB, downloaded 2026-09-03), Build_Any_Number_Video2.mp4 (232 MB, 2026-09-02), in this folder.

Revision 2 (2026-09-02): captions now take every word's spelling from the script (names such as Ladhe's were mis-transcribed by Whisper in revision 1); both files above replaced.

Revision 3 (2026-09-03), Video 1 only: title card now reads "Every prime quadruplet is an additive, multiplicative or exponential combination of its predecessors" (matching the paper's new title), and a new 51 s scene "No base needed" (scene 58, cut in after scene 36) shows the base-free M1 and E3 equations of 854921. Video 2 unchanged.

Revision 4 (2026-09-03), Video 1 only: scene 58 re-recorded for the one-power E3 rule (854921 = (829^2) + 166849 + 823 + 5 + 3 and 19497221 = (11^7) + 9439 + 199 + 197 + 193 + 19 + 3). Video 2 unchanged.

Revision 5 (2026-09-03), Video 1 only: scene 58 re-recorded for the powers-first E3 rule (854921 = (829^2) + (11^5) + (17^3) + 1489 + 107 + 101 + 19 and 19497221 = (11^7) + (2^13) + 829 + 827 + 199 + 3); the wrapped equation line of revision 4 is fixed. Video 2 unchanged.
