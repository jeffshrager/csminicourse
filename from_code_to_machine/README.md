This is a simple code-to-bytecode-to-hardware stack for a languge
called "Irony", and a very simple OS, called "PathOS".

The top level is "pathos.py", which imports "irony.py". (Irony.py 
can be run separately. See the "main" call at the end of the module.) 

PathOS can create, edit, compile, and run programs written in Irony. 
The "comp" and "exec" commands in pathos compile the sources (.s) to 
assembly (byte code, .a files) and then execute the reuslting assembly 
on the emulated hardware. (See "pathos_demo.log".) There's no pure 
(numerical) machine langage phase; The virtual hardware treats 
the byte codes produced by the compiler as op codes.  However, it does 
have a stack, memory, and registers.

Everything here was written in about 5 total hours with the help of
claude and chatgpt (mostly Claude). As many of us who use LLMs to
assist in coding quickly discover, they are bad at keeping track of
even margianlly complex or large projects, and don't deal well with
conceptually intricate programming concepts. They were basically
incapable of implementing recursion correctly, or generalizing to the
correct level, and they kept losing their place in the series of
steps. (IMHO, the attention model is the wrong model of working and
short term memory!) Eventually they would just lose track entirely and
be unable to do even simple tasks, at which point I had to reset the
session entirely, reload the latest versions of the code base we were
working on, and then re-explain the project, where we were in it, and
what to do next. In the end I had to give them nearly step-by-step
guidance to get it right, and the way I wanted it to be, and to be
understanable and teachable.

Operating systems being conceptually simpler than programming
languges, PathOS was easier for Claude to write and work with than
Irony, and was almost entirely written by Claude, although based on
several paragraph of detailed spec.  And Claude was able to plug Irony
into PATHOS, that is, to create comp and exec commands without much
guidance! (Even so, it got lost multiple times and I had to resort to
resetting it, as described above.) Note that PathOS is NOT written in
Irony, nor does it run on the Irony VM. Maybe I'll work on that next.

