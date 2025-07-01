This is a (highly) simplified code-to-bytecode-to-machine stack for a
languge called "irony", and (extremely simple) OS, called "pathos".

The files "compiler.py" and "virtual_hardware.py" are the primary
irony modules.  Irony supports recursion, including mutual recursion,
but nothing fancy.  There's no lexer, so you need to put spaces
between tokens. (Being a native Lisper, I *hate* lexers!)

compiler.py takes Irony source to byte code, and has a byte-code
interpreter. virtual_hardware.py take the same byte code, but emulates
actual hardware.

These are designed to go with an exercise where the student add FOR
LOOP capability. Given the well-designed base, this is extremely
simple, but requires understanding each step of the
stack. ("compiler_for" and "virtual_hardware_for" are the solutions; The
idea, of course, is not to give these to the student!)

(You'd think that it ought be the other way round: Start with for
loops and then ask the student to add recursion, but it's much harder
to add recursion than loops, so I put recursion into the base, and
then ask the student to add for loops, which, being much simpler, is a
plausible exercise, whereas adding recursion would be way too complex
for a beginner.)

The files "pathos.py" (which imports "irony.py") is a simple OS whose
goal is to create, edit, compile, and run programs written in
Irony. ("irony.py" is a combined version of compiler.py and
virtual_hardware.py, but leaves out the byte code interpreter.) The
"comp" and "exec" commands in pathos compile (to byte code) and then
execute the reuslting byte code (basically assembly) on the emulated hardware. (See
"pathos_demo.log".)

Everything here was written in about 5 total hours using a combination
of claude and chatgpt. This wasn't as easy as I'd hoped. As many folks
who use LLMs to assist in coding discover, they are bad at keeping
track of even margianlly complex or large projects, and don't deal
well with conceptually twisty programming concepts. They were
basically incapable of implementing recursion correctly, or
generalizing to the correct level, and they kept losing their place in
the series of steps. Eventually they would just seemingly lose track
entirely and be unable to fix what turned out to be trivial errors, at
which point I had to clear the decks entirely, reload the latest
versions of the code base we were working on, and then re-explain the project and what to do next. In the end I had to give them nearly step-by-step
guidance to get it right, and the way I wanted it to be, to be
understanable and teachable. That said, to their credit, once I had
the compiler and hardware emulator the understandable and teachable
way I wanted it, I could feed those to the LLM and it was able to
understand the code and make reasonable changes. For example, the
entire FOR LOOP extension was done completely by Claude.

Operating systems being conceptually simpler than programming
languges, PATHOS was easier for the LLMs, and was almost entirely
written by Claude, although based on several paragraph of detailed
spec.  And Claude was able to plug Irony into PATHOS (that is, create
comp and exec commands) first try!

However, I then asked it to create a help command that simply listed
all the other commands, which was nearly a trivail task, and it failed
over and over, until I did one of those resets described above, and
then it worked. (The attention model is the wrong model of working and
short term memory!)

You'll see that I also asked the LLMs to make presentations. Those
are here "as is" (actually, they didn't work, but for a stupid minor
reason, so as-is plus a tiny bit of work), and you'll see that
although these are a reasonable start, they definitely aren't complete
teaching materials.
