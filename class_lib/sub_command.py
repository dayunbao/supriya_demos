class SubCommand:
    def __init__(
        self,
        callback: callable,
        command_text: str,
    ):
        self.callback = callback
        self.command_text = command_text
