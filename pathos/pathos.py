import random
import os
from typing import Dict, List, Optional, Tuple

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
        
        # Create initial /etc/passwd with root user
        passwd_content = ["root secret /users/root"]
        self.create_file_abs("/etc/passwd", passwd_content)
    
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
        """Logout current user"""
        if self.current_user:
            username = self.current_user.userid
            self.current_user = None
            self.fs.current_dir = self.fs.root  # Reset to root directory
            return f"LOGOUT:{username}"  # Special return code for logout
        return "No user logged in"
    
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
            'mkdir': self.cmd_mkdir,
            'del': self.cmd_del,
            'print': self.cmd_print,
            'create': self.cmd_create,
            'change': self.cmd_change,
            'mkuser': self.cmd_mkuser,
            'logout': self.cmd_logout,
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