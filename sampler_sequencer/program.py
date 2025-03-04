from pathlib import Path

from supriya import Buffer, Server

class Program:
    def __init__(
        self,
        name: str,
        program_number: int,
        samples_path: Path,
        server: Server,
    ):
        self.name = name
        self.program_number = program_number
        self._samples_path = samples_path
        self._server = server
        self.buffers = self._load_buffers()
        self.number_samples = len(self.buffers)
        self.selected_sample = self.buffers[0]
    
    def _load_buffers(self) -> list[Buffer]:
        buffers = []
        for sample_path in sorted(self._samples_path.rglob(pattern='*.wav')):
            buffers.append(self._server.add_buffer(file_path=str(sample_path)))
        
        return buffers
    
    def set_selected_sample(self, sample_number: int) -> Buffer:
        self.selected_sample = self.buffers[sample_number]