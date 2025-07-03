import random
import os
from typing import Dict, List, Optional, Tuple

# Import the IRONY language compiler and executor
try:
    from irony import parse, compile_all, execute, test_full
except ImportError:
    # Fallback if irony module not available
    def irony_compile(source):
        return ["# IRONY compiler not available"]
    def irony_execute(code, debug=False):
        return ["IRONY executor not available"]

class User:
    def __init__(self, userid: str, password: str, home_dir: str):
        self.userid = userid
        self.password = password
        self.home_dir = home_dir

class File:
    def __init__(self, name: str, content: List[str], disk_location: int):
        self.name = name
        self.content = content  # List of lines
        self.disk_location = disk_location

class Directory:
    def __init__(self, name: str):
        self.name = name
        self.files: Dict[str, File] = {}
        self.subdirs: Dict[str, 'Directory'] = {}
        self.parent: Optional['Directory'] = None

class FileSystem:
    def __init__(self):
        self.root = Directory("/")
        self.current_dir = self.root
        self.next_disk_location = 1000
        self._setup_initial_structure()
    
    def _setup_initial_structure(self):
        # Create basic directory structure
        self.mkdir_abs("/etc")
        self.mkdir_abs("/users")
        self.mkdir_abs("/users/root")
        self.mkdir_abs("/users/test")
        
        # Create initial /etc/passwd with root and test users
        passwd_content = [
            "root secret /users/root",
            "test test /users/test"
        ]
        self.create_file_abs("/etc/passwd", passwd_content)
        
        # Create sample IRONY programs for test user
        # Fibonacci program
        fib_source = [
            "def fib n",
            "if n < 2",
            "return n",
            "end",
            "a = fib n - 1",
            "b = fib n - 2",
            "return a + b",
            "end",
            "",
            "main = fib 9",
            "print main"
        ]
        self.create_file_abs("/users/test/fibonacci.s", fib_source)
        
        # For loop program
        for_loop_source = [
            "sum = 0",
            "for i from 1 to 5",
            "sum = sum + i",
            "print i",
            "end",
            "print sum",
            "",
            "for j from 10 to 12", 
            "print j",
            "end"
        ]
        self.create_file_abs("/users/test/loops.s", for_loop_source)
        
        # Even/odd mutual recursion program
        even_odd_source = [
            "def is_even n",
            "if n < 1",
            "return 1",
            "end", 
            "return is_odd n - 1",
            "end",
            "",
            "def is_odd n", 
            "if n < 1",
            "return 0",
            "end",
            "return is_even n - 1", 
            "end",
            "",
            "result = is_even 6",
            "print result",
            "result = is_even 5",
            "print result"
        ]
        self.create_file_abs("/users/test/evenodd.s", even_odd_source)
    
    def get_next_disk_location(self) -> int:
        """Generate a random disk location"""
        location = random.randint(10000, 99999)
        self.next_disk_location = location + 1
        return location
    
    def mkdir_abs(self, path: str) -> bool:
        """Create directory with absolute path"""
        if path.startswith("/"):
            path = path[1:]  # Remove leading slash
        
        if not path:
            return False
            
        parts = path.split("/")
        current = self.root
        
        for part in parts:
            if part not in current.subdirs:
                new_dir = Directory(part)
                new_dir.parent = current
                current.subdirs[part] = new_dir
            current = current.subdirs[part]
        return True
    
    def create_file_abs(self, path: str, content: List[str]) -> bool:
        """Create file with absolute path"""
        if not path.startswith("/"):
            return False
            
        dir_path, filename = path.rsplit("/", 1)
        if dir_path == "":
            dir_path = "/"
            
        target_dir = self.get_directory_by_path(dir_path)
        if target_dir is None:
            return False
            
        disk_loc = self.get_next_disk_location()
        target_dir.files[filename] = File(filename, content, disk_loc)
        return True
    
    def get_directory_by_path(self, path: str) -> Optional[Directory]:
        """Get directory object by path"""
        if path == "/":
            return self.root
            
        if path.startswith("/"):
            path = path[1:]
            current = self.root
        else:
            current = self.current_dir
            
        if not path:
            return current
            
        parts = path.split("/")
        for part in parts:
            if part == "..":
                if current.parent:
                    current = current.parent
            elif part in current.subdirs:
                current = current.subdirs[part]
            else:
                return None
        return current
    
    def get_current_path(self) -> str:
        """Get current directory path"""
        if self.current_dir == self.root:
            return "/"
            
        path_parts = []
        current = self.current_dir
        while current and current != self.root:
            path_parts.append(current.name)
            current = current.parent
        
        return "/" + "/".join(reversed(path_parts))

class Shell:
    def __init__(self):
        self.fs = FileSystem()
        self.current_user: Optional[User] = None
        self.users: Dict[str, User] = {}
        self._load_users()
    
    def _load_users(self):
        """Load users from /etc/passwd"""
        passwd_file = self.fs.root.subdirs["etc"].files.get("passwd")
        if passwd_file:
            for line in passwd_file.content:
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        userid, password, home_dir = parts[0], parts[1], parts[2]
                        self.users[userid] = User(userid, password, home_dir)
    
    def login(self, userid: str, password: str) -> bool:
        """Attempt to log in user"""
        if userid in self.users and self.users[userid].password == password:
            self.current_user = self.users[userid]
            # Set current directory to user's home
            home_dir = self.fs.get_directory_by_path(self.current_user.home_dir)
            if home_dir:
                self.fs.current_dir = home_dir
            return True
        return False
    
    def cmd_cd(self, args: List[str]) -> str:
        """Change directory command"""
        if not args:
            # Go to home directory
            if self.current_user:
                home_dir = self.fs.get_directory_by_path(self.current_user.home_dir)
                if home_dir:
                    self.fs.current_dir = home_dir
                    return ""
            return "No home directory"
        
        target_path = args[0]
        target_dir = self.fs.get_directory_by_path(target_path)
        if target_dir:
            self.fs.current_dir = target_dir
            return ""
        else:
            return f"Directory not found: {target_path}"
    
    def cmd_listdir(self, args: List[str]) -> str:
        """List directory contents"""
        result = []
        
        # List subdirectories
        for dirname in sorted(self.fs.current_dir.subdirs.keys()):
            result.append(f"{dirname}/")
        
        # List files
        for filename, file_obj in sorted(self.fs.current_dir.files.items()):
            result.append(f"{filename} (disk: {file_obj.disk_location})")
        
        return "\n".join(result) if result else "Directory is empty"
    
    def cmd_mkdir(self, args: List[str]) -> str:
        """Create directory"""
        if not args:
            return "Usage: mkdir <dirname>"
        
        dirname = args[0]
        if dirname in self.fs.current_dir.subdirs:
            return f"Directory already exists: {dirname}"
        
        new_dir = Directory(dirname)
        new_dir.parent = self.fs.current_dir
        self.fs.current_dir.subdirs[dirname] = new_dir
        return f"Directory created: {dirname}"
    
    def cmd_del(self, args: List[str]) -> str:
        """Delete file"""
        if not args:
            return "Usage: del <filename>"
        
        filename = args[0]
        if filename in self.fs.current_dir.files:
            del self.fs.current_dir.files[filename]
            return f"File deleted: {filename}"
        else:
            return f"File not found: {filename}"
    
    def cmd_print(self, args: List[str]) -> str:
        """Print file contents with line numbers"""
        if not args:
            return "Usage: print <filename>"
        
        filename = args[0]
        if filename not in self.fs.current_dir.files:
            return f"File not found: {filename}"
        
        file_obj = self.fs.current_dir.files[filename]
        result = []
        line_num = 10
        
        for line in file_obj.content:
            result.append(f"{line_num:3d} {line}")
            line_num += 10
        
        return "\n".join(result) if result else "File is empty"
    
    def cmd_create(self, args: List[str]) -> str:
        """Create new file with interactive input"""
        if not args:
            return "Usage: create <filename>"
        
        filename = args[0]
        if filename in self.fs.current_dir.files:
            return f"File already exists: {filename}"
        
        print(f"Creating file: {filename}")
        print("Enter lines of text (empty line to finish):")
        
        content = []
        line_num = 10
        
        while True:
            try:
                line = input(f"{line_num:3d} ")
                if line == "":
                    break
                content.append(line)
                line_num += 10
            except EOFError:
                break
        
        disk_loc = self.fs.get_next_disk_location()
        self.fs.current_dir.files[filename] = File(filename, content, disk_loc)
        return f"File created: {filename} (disk: {disk_loc})"
    
    def cmd_change(self, args: List[str]) -> str:
        """Edit existing file"""
        if not args:
            return "Usage: change <filename>"
        
        filename = args[0]
        if filename not in self.fs.current_dir.files:
            return f"File not found: {filename}"
        
        file_obj = self.fs.current_dir.files[filename]
        
        print(f"Editing file: {filename}")
        print("Current contents:")
        print(self.cmd_print([filename]))
        print("\nEnter line number and new text (empty line to finish):")
        print("Format: <line_number> <text> or just <line_number> to delete")
        
        while True:
            try:
                line = input("edit> ")
                if line == "":
                    break
                
                parts = line.split(" ", 1)
                if not parts[0].isdigit():
                    print("Line number must be numeric")
                    continue
                
                line_num = int(parts[0])
                line_index = (line_num - 10) // 10
                
                if len(parts) == 1:
                    # Delete line
                    if 0 <= line_index < len(file_obj.content):
                        del file_obj.content[line_index]
                        print(f"Line {line_num} deleted")
                    else:
                        print(f"Line {line_num} not found")
                else:
                    # Add or replace line
                    new_text = parts[1]
                    if line_index < len(file_obj.content):
                        file_obj.content[line_index] = new_text
                        print(f"Line {line_num} replaced")
                    else:
                        # Extend list if necessary
                        while len(file_obj.content) <= line_index:
                            file_obj.content.append("")
                        file_obj.content[line_index] = new_text
                        print(f"Line {line_num} added")
                        
            except EOFError:
                break
            except ValueError:
                print("Invalid line number")
        
        return f"File {filename} updated"
    
    def cmd_mkuser(self, args: List[str]) -> str:
        """Create new user"""
        if len(args) < 2:
            return "Usage: mkuser <userid> <password>"
        
        userid, password = args[0], args[1]
        
        if userid in self.users:
            return f"User already exists: {userid}"
        
        # Create home directory
        home_dir = f"/users/{userid}"
        if not self.fs.mkdir_abs(home_dir):
            return f"Could not create home directory: {home_dir}"
        
        # Add user to /etc/passwd
        passwd_file = self.fs.root.subdirs["etc"].files["passwd"]
        passwd_file.content.append(f"{userid} {password} {home_dir}")
        
        # Add to users dict
        self.users[userid] = User(userid, password, home_dir)
        
        return f"User created: {userid}"
    
    def cmd_logout(self, args: List[str]) -> str:
        """Log out current user"""
        if self.current_user:
            username = self.current_user.userid
            self.current_user = None
            # Reset to root directory
            self.fs.current_dir = self.fs.root
            return f"LOGOUT:{username}"
        else:
            return "No user currently logged in"
    
    def cmd_help(self, args: List[str]) -> str:
        """Show available commands"""
        help_text = [
            "Available commands:",
            "cd [dir]",
            "listdir / ls",
            "mkdir <dirname>",
            "del <filename>",
            "print <filename> / cat <filename>",
            "create <filename>",
            "change <filename>",
            "comp <source_file> <assembly_file>",
            "exec <assembly_file> [debug]",
            "mkuser <userid> <password>",
            "logout",
            "help / ?",
            "exit / quit"
        ]
        return "\n".join(help_text)
    
    def cmd_comp(self, args: List[str]) -> str:
        """Compile IRONY source file to assembly"""
        if len(args) < 2:
            return "Usage: comp <source_file> <assembly_file>"
        
        source_file = args[0]
        assembly_file = args[1]
        
        # Check if source file exists
        if source_file not in self.fs.current_dir.files:
            return f"Source file not found: {source_file}"
        
        # Check if assembly file already exists
        if assembly_file in self.fs.current_dir.files:
            return f"Assembly file already exists: {assembly_file}"
        
        # Get source code
        source_content = self.fs.current_dir.files[source_file].content
        
        try:
            # Compile using IRONY compiler
            ast = parse(source_content)
            assembly_code = compile_all(ast)
            # Convert tuples to strings for storage
            assembly_code = [str(instr) for instr in assembly_code]
            
            # Create assembly file
            disk_loc = self.fs.get_next_disk_location()
            self.fs.current_dir.files[assembly_file] = File(assembly_file, assembly_code, disk_loc)
            
            return f"Compiled {source_file} -> {assembly_file} (disk: {disk_loc})"
            
        except Exception as e:
            return f"Compilation error: {str(e)}"
    
    def cmd_exec(self, args: List[str]) -> str:
        """Execute IRONY assembly file"""
        if not args:
            return "Usage: exec <assembly_file> [debug]"
        
        assembly_file = args[0]
        debug_mode = len(args) > 1 and args[1].lower() == "debug"
        
        # Check if assembly file exists
        if assembly_file not in self.fs.current_dir.files:
            return f"Assembly file not found: {assembly_file}"
        
        # Get assembly code
        assembly_content = self.fs.current_dir.files[assembly_file].content
        
        try:
            # Execute using IRONY virtual machine
            code = [eval(line) for line in assembly_content]
            execute(code)
            # The execute function prints directly and stores output in the global 'output' variable
            from irony import output
            result_output = output.copy()
            
            if output:
                return "Program output:\n" + "\n".join(output)
            else:
                return "Program executed (no output)"
                
        except Exception as e:
            return f"Execution error: {str(e)}"
    
    def execute_command(self, command_line: str) -> str:
        """Execute a command"""
        if not command_line.strip():
            return ""
        
        parts = command_line.strip().split()
        cmd = parts[0]
        args = parts[1:]
        
        commands = {
            'cd': self.cmd_cd,
            'listdir': self.cmd_listdir,
            'ls': self.cmd_listdir,  # Alternative command
            'mkdir': self.cmd_mkdir,
            'del': self.cmd_del,
            'print': self.cmd_print,
            'cat': self.cmd_print,  # Alternative command
            'create': self.cmd_create,
            'change': self.cmd_change,
            'mkuser': self.cmd_mkuser,
            'logout': self.cmd_logout,
            'comp': self.cmd_comp,
            'exec': self.cmd_exec,
            'help': self.cmd_help,
            '?': self.cmd_help,  # Alternative command
        }
        
        if cmd in commands:
            return commands[cmd](args)
        else:
            return f"Unknown command: {cmd}"
    
    def run(self):
        """Main shell loop"""
        print("PATHOS Operating System")
        print("======================")
        
        while True:  # Main system loop
            # Login loop
            while not self.current_user:
                try:
                    userid = input("Login: ")
                    password = input("Password: ")
                    
                    if self.login(userid, password):
                        print(f"Welcome, {userid}!")
                        break
                    else:
                        print("Invalid login")
                except EOFError:
                    print("\nGoodbye!")
                    return
            
            # Command loop
            while self.current_user:  # Continue until logout
                try:
                    current_path = self.fs.get_current_path()
                    prompt = f"{self.current_user.userid}:{current_path}$ "
                    command = input(prompt)
                    
                    if command.strip().lower() in ['exit', 'quit']:
                        print("Goodbye!")
                        return
                    
                    result = self.execute_command(command)
                    if result:
                        if result.startswith("LOGOUT:"):
                            # Handle logout
                            username = result.split(":", 1)[1]
                            print(f"Goodbye, {username}!")
                            # Re-load users in case new ones were created
                            self._load_users()
                            # Go back to login loop
                            break
                        else:
                            print(result)
                            
                except EOFError:
                    print("\nGoodbye!")
                    return
                except KeyboardInterrupt:
                    print("\nUse 'exit' to quit or 'logout' to switch users")

if __name__ == "__main__":
    shell = Shell()
    shell.run()
