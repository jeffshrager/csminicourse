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
stack. ("compiler_for" and "virtual_hardware_for" and solutions; The
idea, of course, is not to give these to the student!)

(You'd think that it ought be the other way round: Start with for
loops and then ask the student to add recursion, but it's much harder
to add recursion than loops, so I put recursion into the base, and
then ask the student to add for loops, which, being much simpler, is a
plausible exercise, whereas adding recursion would be way too complex
for a beginner.)

You'll see that I also asked the LLMs to make presentations. Those are
here "as is" (actually, they didn't work, but for a stupid minor
reason, so as-is plus a tiny bit of work), and you'll see that
although these are a reasonable start, they definitely aren't complete
teaching materials.

The files "pathos.py" (which imports "irony.py") is a simple OS whose
goal is to create, edit, compile, and run programs written in
Irony. ("irony.py" is a combined version of compiler.py and
virtual_hardware.py, but leaves out the byte code interpreter.) The
"comp" and "exec" commands in pathos compile (to byte code) and then
execute the reuslting (on the emulated hardware). See
"pathos_demo.log".

Everything here was written in about 5 total hours using a combination
of claude and chatgpt. This wasn't as easy as I'd hoped. As many folks
who use LLMs to assist in coding discover, they are bad at keeping
track of even margianlly complex or large projects. They were
basically incapable of implementing recursion correctly, or
generalizing to the correct level, and they kept losing their place,
so I had to clears the decks several times and reload the latest
versions, and then re-explain what I wanted, and other annoying
machinations. In the end I had to give them nearly step-by-step
guidance to get it right, and the way I wanted it to be understanable
and teachable. That said, to their credit, once I had the compiler and
hardware emulator the way I wanted it, I could feed those to the LLM
and was able to understand it and make reasonable changes. For
example, the entire FOR LOOP extension was done completely by
Claude. (PATHOS was also mostly written by claude, with my detailed
guidance, but it's much simpler than Irony.)

