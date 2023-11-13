from enum import Enum
from typing import List, Union

import langcodes
from pydantic import field_validator, ConfigDict, BaseModel, validator


class AvailableSettings(str, Enum):
    language = "language"
    preferred_theme = "preferred_theme"


class DefaultContentLanguages(str, Enum):
    polish = langcodes.Language.get(langcodes.standardize_tag("pl")).language
    english = langcodes.Language.get(langcodes.standardize_tag("en")).language


class AvailableThemes(str, Enum):
    dark = "dark"
    light = "light"


class PreferredThemeBase(BaseModel):
    name: AvailableSettings = AvailableSettings.preferred_theme
    current_value: AvailableThemes
    model_config = ConfigDict(from_attributes=True)


class PreferredThemeCreate(PreferredThemeBase):
    default_value: Union[AvailableThemes, None] = None


class LanguageBase(BaseModel):
    name: AvailableSettings = AvailableSettings.language
    current_value: str
    model_config = ConfigDict(from_attributes=True)


class LanguageCreate(LanguageBase):
    default_value: Union[str, None] = None


class ReturnSetting(BaseModel):
    name: AvailableSettings
    default_value: Union[str, None] = None
    current_value: str
    model_config = ConfigDict(from_attributes=True)


class ReturnSettings(BaseModel):
    settings: List[ReturnSetting]
    model_config = ConfigDict(from_attributes=True)


class SettingBase(BaseModel):
    name: AvailableSettings
    current_value: str

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("current_value", pre=True)
    def ensure_valid_setting(cls, value, values):
        if values.get("name") == AvailableSettings.preferred_theme:
            if value not in (v for v in AvailableThemes):
                raise ValueError(
                    f"value is not a valid enumeration member; permitted: "
                    + ", ".join([f"'{v.value}'" for v in AvailableThemes])
                )
        elif not langcodes.Language.get(value).is_valid():
            raise ValueError("value is not a valid ietf language tag ")
        return value

    model_config = ConfigDict(from_attributes=True)


class UpdateSetting(BaseModel):
    name: AvailableSettings
    new_value: Union[str, AvailableThemes]

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("new_value", pre=True)
    def ensure_valid_setting(cls, value, values):
        if values.get("name") == AvailableSettings.preferred_theme:
            if value not in (v for v in AvailableThemes):
                raise ValueError(
                    f"value is not a valid enumeration member; permitted: "
                    + ", ".join([f"'{v.value}'" for v in AvailableThemes])
                )
        elif not langcodes.Language.get(value).is_valid():
            raise ValueError("value is not a valid ietf language tag ")
        return value

    model_config = ConfigDict(from_attributes=True)


class UpdateSettings(BaseModel):
    settings: List[UpdateSetting]

    @field_validator("settings", mode="before")
    @classmethod
    def ensure_settings_limit(cls, v):
        if len(v) > len(AvailableSettings):
            raise ValueError("Each setting can be specified only once")

        unique_elements = set(val["name"] for val in v)
        if len(unique_elements) != len(v):
            raise ValueError("Each setting can be specified only once")

        return v

    model_config = ConfigDict(from_attributes=True)
