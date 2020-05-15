#
# prop_store.py
#
# These codes are licensed under CC0.
# http://creativecommons.org/publicdomain/zero/1.0/deed.ja
#

import bpy
from bpy.types import LayerCollection

from dataclasses import dataclass

from typing import List
from typing import Tuple


def traverse(vl):
    yield vl
    for child in vl.children:
        yield from traverse(child)


@dataclass
class CollectionPropSave:
    exclude: bool = False
    hide_viewport: bool = False
    collection_hide_viewport: bool = False


def convert_collection(lc: LayerCollection) -> Tuple[LayerCollection, CollectionPropSave]:
    return (lc, CollectionPropSave(lc.exclude, lc.hide_viewport, lc.collection.hide_viewport))


class PropStore:
    collection_data: List[Tuple[LayerCollection, CollectionPropSave]]

    def __init__(self):

        self.collection_data = [convert_collection(c)
                                for c in traverse(bpy.context.view_layer.layer_collection)]
        for c in self.collection_data:
            c[0].exclude = False
            c[0].hide_viewport = False
            c[0].collection.hide_viewport = False

    def restore(self):
        for c in self.collection_data:
            c[0].exclude = c[1].exclude
            c[0].hide_viewport = c[1].hide_viewport
            c[0].collection.hide_viewport = c[1].collection_hide_viewport
