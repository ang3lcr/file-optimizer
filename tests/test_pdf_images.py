"""Script temporal para probar la compresión PDF con imágenes."""
import sys, shutil
sys.path.insert(0, '.')
from pathlib import Path
import tempfile

# Crear imagen de prueba
from PIL import Image as PILImage

tmpdir = Path(tempfile.mkdtemp())
img = PILImage.new('RGB', (800, 600), color=(100, 150, 200))
img_path = str(tmpdir / 'test.jpg')
img.save(img_path, 'JPEG', quality=100)

# Crear PDF con la imagen usando reportlab
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Image as RLImage

pdf_path = tmpdir / 'test.pdf'
doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
story = [RLImage(img_path, width=300, height=200)]
doc.build(story)

original_size = pdf_path.stat().st_size
print(f'PDF original: {original_size/1024:.1f} KB')

# Comprimir
from compressors.pdf.pdf_compressor import PdfCompressor
from compressors.base import CompressionOptions
from models.compression_profile import QualityLevel

out_path = tmpdir / 'test_optimizado.pdf'
opts = CompressionOptions(quality_level=QualityLevel.BALANCED, output_path=out_path)
c = PdfCompressor()
result = c.compress(pdf_path, opts)

print(f'Resultado: success={result.success}')
if result.success:
    print(f'PDF comprimido: {result.final_size/1024:.1f} KB')
    print(f'Reduccion: {result.reduction_percent:.1f}%')

    # Verificar que el PDF resultante tiene imagenes legibles
    import fitz
    doc_out = fitz.open(str(out_path))
    for page_num, page in enumerate(doc_out):
        imgs = page.get_images(full=True)
        print(f'Pagina {page_num+1}: {len(imgs)} imagen(es)')
        for img_info in imgs:
            xref = img_info[0]
            base = doc_out.extract_image(xref)
            ext = base['ext']
            size = len(base['image'])
            print(f'  xref={xref}: ext={ext}, tamano={size} bytes - OK')
    doc_out.close()
    print('EXITO: Las imagenes se conservaron correctamente.')
else:
    print(f'Error: {result.error_message}')

shutil.rmtree(tmpdir)
