from typing import Optional

from .sub_command import SubCommand

class Command:
    def __init__(
        self,  
        command_text: str, 
        sub_commands: Optional[dict[str, SubCommand] | None]=None
    ):
        self.command_text = command_text
        self.sub_commands = sub_commands
        self.options: str | None = self._create_options_from_subcommands()
    
    def _create_options_from_subcommands(self) -> None:
        if self.sub_commands:
            if len(self.sub_commands.keys()) == 1:
                return f'{list(self.sub_commands.keys())[0]}\n'
            
            return '\n'.join(self.sub_commands.keys())
            
