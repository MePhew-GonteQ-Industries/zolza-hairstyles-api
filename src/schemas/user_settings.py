from pydantic import BaseModel
from enum import Enum
from typing import Union


class AvailableContentLanugages(str, Enum):
    polish = "pl"
    english = "en"


class AvailableThemes(str, Enum):
    dark = 'dark'
    light = 'light'


class PreferedTheme(BaseModel):
    name: str = 'prefered_theme'
    default_value: AvailableThemes = None
    current_value: AvailableThemes


class Language(BaseModel):
    name: str = 'language'
    default_value: AvailableContentLanugages = None
    current_value: AvailableContentLanugages


class ReturnSettings(BaseModel):
    name: str
    default_value: Union[str, None]
    current_value: str

    class Config:
        orm_mode = True
