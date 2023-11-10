
import os
import pdf2image
import shutil
import subprocess
import tempfile

from pathlib import Path

from .error import ScriptmakerError
from .filesystem import mkdirp


class PDFTools ():
    """ 
    Allows you to operate on generated PDFs.
    """
    
    @classmethod
    def compress (cls, filename):
        """
        Attempts to compress the target PDF. Overwrites to the same location.
        """
        pass
        filename = Path(filename).resolve()
        if filename.suffix != ".pdf":
            raise ScriptmakerError('cannot compress a non-PDF file')
    
        with tempfile.NamedTemporaryFile() as gs_file:
            subprocess.call(
                [
                    'gs', 
                    '-sDEVICE=pdfwrite', 
                    '-dCompatibilityLevel=1.4', 
                    '-dPDFSETTINGS=/prepress', 
                    '-dNOPAUSE',
                    '-dQUIET',
                    '-dBATCH',
                    f"-sOutputFile={gs_file.name}",
                    filename
                ]
            )
            shutil.copyfile(gs_file.name, filename)
        return filename
        
    
    @classmethod
    def pngify (cls, filename, output_folder = None):
        """
        Splits a PDF into PNGs of each page. If the output folder is not given, creates a pages/ directory in the same directory as the input.
        """
        filename = Path(filename)
        
        if not output_folder:
            output_folder = Path(filename.parent, 'pages')
        mkdirp(output_folder)
        
        pdf_name = filename.stem
        pages = pdf2image.convert_from_path(filename)
        page_paths = []
        
        for i, page in enumerate(pages):
            page_path = Path(output_folder, f"{pdf_name}-{i + 1}.png")
            page_paths.append(page_path)
            page.save(page_path)
    
        return page_paths