#
# supplement_xml.py
#
# These codes are licensed under CC0.
# http://creativecommons.org/publicdomain/zero/1.0/deed.ja
#

from xml.etree.ElementTree import Element

from typing import Optional
from typing import TypeVar
from typing import Type

T = TypeVar('T')


def elm_to_obj(element: Element, klass: Type[T]) -> T:
    obj = klass()

    for k, v in obj.__annotations__.items():
        val = element.get(k)
        if val is not None:
            if v is int:
                setattr(obj, k, int(val))
            elif v is str:
                setattr(obj, k, val)
            elif v is float:
                setattr(obj, k, float(val))

    return obj


def obj_to_elm(obj: Type[T], element: Element):

    for k, v in obj.__annotations__.items():
        val = getattr(obj, k)
        if val is not None:
            element.set(k, str(val))


class EdgeColor:
    a: float = 0.0
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0


class Diffuse:
    a: float = 0.0
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0


class Specular:
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0


class Ambient:
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0


class Sphere:
    path: str
    type: int


class Material:
    b_name: str
    both: int = 0
    drop_shadow: int = 0
    edge_size: float = 1.0
    ground_shadow: int = 0
    name: str
    name_e: str
    on_edge: int = 0
    on_shadow: int = 0
    toon: int = 0
    use_systemtoon: int = 0
    power: float = 1.0

    edge_color: Optional[EdgeColor]
    diffuse: Optional[Diffuse]
    specular: Optional[Specular]
    ambient: Optional[Ambient]
    sphere: Optional[Sphere]
