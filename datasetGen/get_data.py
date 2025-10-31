import os
import shutil
from pathlib import Path


def get_last_path_component(path):
    normalized_path = os.path.normpath(path)
    return os.path.basename(normalized_path)


class FuzzData:
    def __init__(self, source_dir=None, output=None):
        self.source_dir = Path(source_dir)
        self.output = Path(output)
    
    # cp the sel file
    def copy_sel_to_dest(self):
        last_path = get_last_path_component(self.source_dir)

        current_file_dir = Path(__file__).parent
        source_dir = Path(os.path.join(current_file_dir, "data", last_path))
        self.output.mkdir(parents=True, exist_ok=True)

        for file in source_dir.iterdir():
            if file.is_file() and file.suffix == '.sel':
                shutil.copy(file, self.output / file.name)

class FuzzGen:
    def __init__(self, source_dir=None, output=None, gen_file_path=None):
        self.source_dir = Path(source_dir)
        self.output = Path(output)
        self.gen_file = Path(gen_file_path)

    def copy_tar_to_dest(self):
        last_path = get_last_path_component(self.source_dir)

        current_file_dir = Path(__file__).parent
        source_dir = Path(os.path.join(current_file_dir, "data", last_path))

        source_file = source_dir / 'omni_test.c'
        if source_file.is_file():
            shutil.copyfile(source_file, self.output)
            shutil.copyfile(source_file, self.gen_file)
        
        
        

if __name__ == "__main__":
    copier = FuzzData("data/fuzz/")
    print(copier.copy_to_destination())
    