from pydantic import BaseModel, validator
from enum import Enum
from typing import List, Union

# TODO: Ensure everything works as intended


class AvailableSettings(str, Enum):
    language = 'language'
    prefered_theme = 'prefered_theme'


class AvailableContentLanugages(str, Enum):
    polish = "pl"
    english = "en"


class AvailableThemes(str, Enum):
    dark = 'dark'
    light = 'light'


class PreferredThemeBase(BaseModel):
    name: AvailableSettings = AvailableSettings.prefered_theme
    current_value: AvailableThemes

    class Config:
        orm_mode = True


class PreferredThemeCreate(PreferredThemeBase):
    default_value: AvailableThemes = None


class LanguageBase(BaseModel):
    name: AvailableSettings = AvailableSettings.language
    current_value: AvailableContentLanugages

    class Config:
        orm_mode = True


class LanguageCreate(LanguageBase):
    default_value: AvailableContentLanugages = None


class ReturnSetting(BaseModel):
    name: AvailableSettings
    default_value: Union[str, None]
    current_value: str

    class Config:
        orm_mode = True


class ReturnSettings(BaseModel):
    settings: List[ReturnSetting]

    class Config:
        orm_mode = True


class SettingBase(BaseModel):
    name: AvailableSettings
    current_value: str

    @validator('*', pre=True)
    def validate(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Each setting must be a valid dict')

        match v.get('name'):
            case AvailableSettings.language.value:
                match v.get('current_value'):
                    case AvailableContentLanugages.english.value:
                        return v
                    case AvailableContentLanugages.polish.value:
                        return v
                    case _:
                        raise ValueError(f"value is not a valid enumeration member; permitted: "
                                         f"'{AvailableContentLanugages.polish.value}', "
                                         f"'{AvailableContentLanugages.english.value}'")
            case AvailableSettings.prefered_theme.value:
                match v.get('current_value'):
                    case AvailableThemes.dark.value:
                        return v
                    case AvailableThemes.light.value:
                        return v
                    case _:
                        raise ValueError(f"value is not a valid enumeration member; permitted: "
                                         f"'{AvailableThemes.dark.value}', "
                                         f"'{AvailableThemes.light.value}'")

    class Config:
        orm_mode = True


class UpdateSettings(BaseModel):
    settings: List[SettingBase]

    @validator('settings', pre=True)
    def ensure_settings_limit(cls, v):
        if len(v) > 2:
            raise ValueError('Each setting can be specified only once')

        unique_elements = set(val for dic in v for val in dic.values()
                              if val == AvailableSettings.prefered_theme.value
                              or val == AvailableSettings.language.value)
        if len(unique_elements) != len(v):
            raise ValueError('Each setting can be specified only once')

        return v

    class Config:
        orm_mode = True
