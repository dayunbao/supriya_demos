import threading

from .command import Command
from .menu import Menu

class TerminalInterface:
    def __init__(
        self,
        menu: Menu,
        prompt: str,
        prompt_header: str,
    ):
        self.menu = menu
        self.prompt = f'{prompt}\n'
        self.current_mode_suffix = '(Current mode is '
        self.prompt_character = '> '
        self.stop_listening_for_input: threading.Event = threading.Event()

    def listen_for_input(self) -> None:
        consumer_thread = threading.Thread(target=self._consume_input, daemon=True)
        consumer_thread.start()
        consumer_thread.join()

    def _consume_input(self) -> None:
        while not self.stop_listening_for_input.is_set():
            command_text = input(self._create_interface_prompt())
            self.menu.set_current_command(command_text=command_text.lower())
            self.commands[self.current_command].callback()
    
    def _create_interface_prompt(self) -> str:
        current_mode = f'{self.menu.current_command.command_text})\n'
        return f'{self.prompt}{self.current_mode_suffix}{current_mode}Options are:\n{self.menu.options_for_current_command}{self.prompt_character}'