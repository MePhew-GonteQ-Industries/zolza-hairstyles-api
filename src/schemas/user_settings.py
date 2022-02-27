from pydantic import BaseModel, validator
from enum import Enum
from typing import List, Union


class AvailableSettings(str, Enum):
    language = "language"
    preferred_theme = "preferred_theme"


class AvailableContentLanguages(str, Enum):
    polish = "pl"
    english = "en"


class AvailableThemes(str, Enum):
    dark = "dark"
    light = "light"


class PreferredThemeBase(BaseModel):
    name: AvailableSettings = AvailableSettings.preferred_theme
    current_value: AvailableThemes

    class Config:
        orm_mode = True


class PreferredThemeCreate(PreferredThemeBase):
    default_value: Union[AvailableThemes, None] = None


class LanguageBase(BaseModel):
    name: AvailableSettings = AvailableSettings.language
    current_value: AvailableContentLanguages

    class Config:
        orm_mode = True


class LanguageCreate(LanguageBase):
    default_value: Union[AvailableContentLanguages, None] = None


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

    @validator("current_value", pre=True)
    def ensure_valid_setting(cls, value, values):
        match values.get("name"):
            case AvailableSettings.language:
                if value not in (v for v in AvailableContentLanguages):
                    raise ValueError(
                        f"value is not a valid enumeration member; permitted: "
                        + ", ".join([f"'{v.value}'" for v in AvailableContentLanguages])
                    )
            case AvailableSettings.preferred_theme:
                if value not in (v for v in AvailableThemes):
                    raise ValueError(
                        f"value is not a valid enumeration member; permitted: "
                        + ", ".join([f"'{v.value}'" for v in AvailableThemes])
                    )
        return value

    class Config:
        orm_mode = True


class UpdateSetting(BaseModel):
    name: AvailableSettings
    new_value: Union[AvailableContentLanguages, AvailableThemes]

    @validator("new_value", pre=True)
    def ensure_valid_setting(cls, value, values):
        match values.get("name"):
            case AvailableSettings.language:
                if value not in (v for v in AvailableContentLanguages):
                    raise ValueError(
                        f"value is not a valid enumeration member; permitted: "
                        + ", ".join([f"'{v.value}'" for v in AvailableContentLanguages])
                    )
            case AvailableSettings.preferred_theme:
                if value not in (v for v in AvailableThemes):
                    raise ValueError(
                        f"value is not a valid enumeration member; permitted: "
                        + ", ".join([f"'{v.value}'" for v in AvailableThemes])
                    )
        return value

    class Config:
        orm_mode = True


class UpdateSettings(BaseModel):
    settings: List[UpdateSetting]

    @validator("settings", pre=True)
    def ensure_settings_limit(cls, v):
        if len(v) > len(AvailableSettings):
            raise ValueError("Each setting can be specified only once")

        unique_elements = set(val["name"] for val in v)
        if len(unique_elements) != len(v):
            raise ValueError("Each setting can be specified only once")

        return v

    class Config:
        orm_mode = True
