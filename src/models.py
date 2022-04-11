from pydantic.dataclasses import dataclass
from typing import Dict, List, Any

# todo change
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

Survey = Dict[str, Literal[1,2,3,4,5,6,7]]


@dataclass
class Item:
    """
    Represents a generic item.
    """
    item_id: str
    title: str
    genre: str


@dataclass
class Rating:
    """
    User's rating for an item. `rating` should be a number
    between 1 and 5 (both inclusive).
    """
    item_id: str
    rating: Literal[1,2,3,4,5]
    loc: str
    level: int
    rating_date:str


@dataclass
class Preference:
    """
    Represents a predicted or actual preference. `categories`
    is a list of classes that an item belongs to.
    """
    item_id: str
    categories: List[Literal["top_n", "controversial", "hate", "hip", "no_clue"]]
