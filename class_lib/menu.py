from .command import Command

class Menu:
    def __init__(self, commands: dict[str, Command]):
        self.commands = commands
        self.main_menu_command: Command = list(self.commands.values())[0]
        self._current_command = self.main_menu_command 
        self.options_for_current_command = self.main_menu_command.options

    @property
    def current_command(self) -> Command:
        return self._current_command
    
    @current_command.setter
    def current_command(self, command: Command) -> None:
        self._current_command = command
        if self._current_command.options is None:
           self.main_menu_command.options
        else: 
            self.options_for_current_command = self._current_command.options
    
    def find_command_by_text(self, text: str, commands: dict[str, Command]) -> Command | None:
        if text in commands:
            return commands[text]
        
        for value in commands.values():
            if isinstance(value, dict):  # If the value is another dictionary, recurse
                result = self.find_command_by_text(text=text, commands=value)
                if result is not None:
                    return result
        
        return None  # Return None if the key is not found

    def set_current_command(self, command_text: str) -> None:
        result = self.find_command_by_text(text=command_text, commands=self.commands)
        if result is not None:
            self.current_command = result