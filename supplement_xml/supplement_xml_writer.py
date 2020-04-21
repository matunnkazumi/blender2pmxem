#
# supplement_xml_writer.py
#
# These codes are licensed under CC0.
# http://creativecommons.org/publicdomain/zero/1.0/deed.ja
#

from xml.etree.ElementTree import TreeBuilder
from xml.etree.ElementTree import Element

from .supplement_xml import obj_to_elm


class UtilTreeBuilder(TreeBuilder):
    def __init__(self):
        super().__init__()

    def new_line(self):
        self.data("\n")

    def start_end(self, tag_name: str, data: str) -> Element:
        self.start(tag_name, {})
        self.data(data)
        return self.end(tag_name)

    def start_with_obj(self, tag_name: str, obj) -> Element:
        elm = self.start(tag_name, {})
        obj_to_elm(obj, elm)
        return elm

    def self_closing_with_obj(self, tag_name: str, obj) -> Element:
        elm = self.self_closing(tag_name)
        obj_to_elm(obj, elm)
        return elm

    def self_closing(self, tag_name: str) -> Element:
        self.start(tag_name)
        return self.end(tag_name)
