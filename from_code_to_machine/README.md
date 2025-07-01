This is a (highly) simplified code-to-bytecode-to-machine stack. It supports recursion, 
including mutual recursion, but nothing fancy. 
There's no lexer, so you need to put spaces between tokens. (Being a native Lisper, I *hate* lexers!) 

The basic project has two parts: Code to Byte Code interpreter, 
and then a second part that emulates actual hardware. The hardware accepts the same byte code as interpreted by the byte-code interpreter, but treats it as assembly language, translates it to machine language, and executes on a hardware (emulated ... obviously). These are "compiler.py" and "virtual_hardware.py". 

Finally, there's an exercise where the student is asked to add for loop capability. Given the
well-designed base, this is extremely simple, but does require understanding each step of the stack. This is "compiler_for" and "virtual_hardware_for". (The idea, of course, is not to give the _for part to the student!)

(You'd think that it ought be the other way round: Start with for loops and then ask the student to add recursion, but it's much harder to add recursion than loops, so I put recursion into the base, and
then ask the student to add for loops, which, being much simpler, is a plausible exercise,
whereas adding recursion would be way too complex for a beginner.)

To answer the question that I'm sure comes immediately to mind, YES I did have help from both ChatGPT and
Claude. But it wasn't actually all that easy to get them to be helpful. As many folks who use LLMs to 
assist in coding discover, they are bad at keeping track of even margianlly complex or large projects. They were basically incapable of implementing recursion correctly, nor generalizing to the correct
level, etc. etc. And they kept losing their place. It took about 5 hours of retries and eventually 
I had to give them nearly step-by-step guidance to get it right, and the way I wanted it to be understanable and teachable. 
(To their credit, once I had it to that point, I could feed the code back to the LLMs and they could
understand it and make reasonable changes. For example, the entire FOR LOOP extension was done completely
by Claude.)

You'll see that I also asked the LLMs to make presentations. Those are here "as is" (actually, 
they didn't work, but for a stupid minor reason, so as-is plus a tiny bit of work), and you'll see that
although these are a reasonable start, they definitely aren't complete teaching materials.
