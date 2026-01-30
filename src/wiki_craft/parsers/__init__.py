"""Document parsers for various file formats."""

from wiki_craft.parsers.base import BaseParser, ParserRegistry
from wiki_craft.parsers.epub import EPUBParser
from wiki_craft.parsers.html import HTMLParser
from wiki_craft.parsers.markdown import MarkdownParser
from wiki_craft.parsers.office import ExcelParser, WordParser
from wiki_craft.parsers.pdf import PDFParser

# Register all parsers
ParserRegistry.register(PDFParser)
ParserRegistry.register(WordParser)
ParserRegistry.register(ExcelParser)
ParserRegistry.register(MarkdownParser)
ParserRegistry.register(HTMLParser)
ParserRegistry.register(EPUBParser)

__all__ = [
    "BaseParser",
    "ParserRegistry",
    "PDFParser",
    "WordParser",
    "ExcelParser",
    "MarkdownParser",
    "HTMLParser",
    "EPUBParser",
]
