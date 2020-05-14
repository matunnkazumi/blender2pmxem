#
# prop_store.py
#
# These codes are licensed under CC0.
# http://creativecommons.org/publicdomain/zero/1.0/deed.ja
#

import bpy
from bpy.types import ViewLayer

from dataclasses import dataclass

from typing import List
from typing import Tuple


def traverse(vl):
    yield vl
    for child in vl.children:
        yield from traverse(child)


@dataclass
class CollectionPropSave:
    hide_viewport: bool = False


class PropStore:
    collection_data: List[Tuple[ViewLayer, CollectionPropSave]]

    def __init__(self):

        self.collection_data = [(c, CollectionPropSave(c.hide_viewport))
                                for c in traverse(bpy.context.layer_collection)]
        for c in self.collection_data:
            c[0].hide_viewport = False

    def restore(self):
        for c in self.collection_data:
            c[0].hide_viewport = c[1].hide_viewport
