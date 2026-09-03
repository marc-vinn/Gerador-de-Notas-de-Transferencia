"""
Legacy XLSParser wrapper redirecting to the modern unified SpreadsheetParser.
"""
from .spreadsheet_parser import SpreadsheetParser

class XLSParser(SpreadsheetParser):
    pass
