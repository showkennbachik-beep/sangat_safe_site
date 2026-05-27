import fitz  # PyMuPDF
from datetime import datetime


def convert_to_pdfa(pdf_path, output_path):
    doc = fitz.open(pdf_path)

    # Set document metadata for PDF/A compliance
    metadata = doc.metadata
    metadata["producer"] = "PyMuPDF PDF/A Converter"
    metadata["creator"] = "PDF Tools"
    metadata["creationDate"] = datetime.now().strftime("D:%Y%m%d%H%M%S")
    metadata["modDate"] = datetime.now().strftime("D:%Y%m%d%H%M%S")
    doc.set_metadata(metadata)

    # Set XMP metadata with PDF/A conformance level B
    xmp = (
        '<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        '<rdf:Description rdf:about=""'
        ' xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/">'
        "<pdfaid:part>1</pdfaid:part>"
        "<pdfaid:conformance>B</pdfaid:conformance>"
        "</rdf:Description>"
        "</rdf:RDF>"
        "</x:xmpmeta>"
        '<?xpacket end="w"?>'
    )
    doc.set_xml_metadata(xmp)

    # Save with deflate compression and full garbage collection
    doc.save(output_path, deflate=True, garbage=4)
    doc.close()

    return output_path
