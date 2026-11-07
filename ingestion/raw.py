import gzip
import os
import logging
from pathlib import Path
"""
    read from data all files
    in: data [directory]
    out: list of rows
"""


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
logger_format = logging.Formatter(
    fmt='%(asctime)s|%(levelname)s|%(name)s|%(message)s',
    datefmt='%d-%b-%Y %H:%M:%S %p'
)
console = logging.StreamHandler()
console.setFormatter(logger_format)
logger.addHandler(console)
file = logging.FileHandler(Path(__file__).parent /'raw.log')
file.setFormatter(logger_format)
logger.addHandler(file)


def to_rows(path:str):
    data_dir=Path(path)
    rows = []
    try:
        files= os.listdir(data_dir)
    except Exception as e:    
        logger.error('Cannot read directory %s: %s', path, e)
        return rows    
    for file in files:
        file_path=data_dir / file
        try:
            open_type = gzip.open(file_path, mode='rt') if file.endswith('.gz') else open(file_path)
            with open_type as f:
                rows.extend(f.readlines())
        except Exception as e:
            logger.error('Error reading %s: %s', file, e)
    return rows   
        
if __name__=='__main__':
    data = to_rows('./test_bad')
    print(len(data))