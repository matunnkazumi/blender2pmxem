#
# supplement_xml.py
#
# These codes are licensed under CC0.
# http://creativecommons.org/publicdomain/zero/1.0/deed.ja
#

from xml.etree.ElementTree import Element

from typing import Optional
from typing import Union
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
            elif v == Union[str, None]:
                setattr(obj, k, val)
            elif v == Union[int, None]:
                setattr(obj, k, int(val))
            elif v == Union[float, None]:
                setattr(obj, k, float(val))
        else:
            if v == Union[str, None] or v == Union[int, None] or v == Union[float, None]:
                setattr(obj, k, None)

    return obj


def obj_to_elm(obj: Type[T], element: Element):

    for k, v in obj.__annotations__.items():
        if v not in [str, int, float, Union[str, None], Union[int, None], Union[float, None]]:
            continue
        val = getattr(obj, k)
        if val is not None:
            element.set(k, str(val))


class Morph:
    group: int = 4
    name: Optional[str]
    name_e: Optional[str]
    b_name: str


class EdgeColor:
    a: float = 1.0
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0


class Diffuse:
    a: Optional[float]
    r: Optional[float]
    g: Optional[float]
    b: Optional[float]


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
    name: Optional[str]
    name_e: Optional[str]
    on_edge: int = 0
    on_shadow: int = 0
    toon: Optional[str]
    use_systemtoon: int = 1
    power: float = 1.0

    edge_color: Optional[EdgeColor]
    diffuse: Optional[Diffuse]
    specular: Optional[Specular]
    ambient: Optional[Ambient]
    sphere: Optional[Sphere]
