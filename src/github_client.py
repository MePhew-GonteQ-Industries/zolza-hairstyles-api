import requests
from requests.auth import HTTPBasicAuth
from .config import settings
from functools import lru_cache
from fastapi import HTTPException, status

auth = HTTPBasicAuth(settings.GH_APP_CLIENT_ID, settings.GH_APP_CLIENT_SECRET)

headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "Zolza Hairstyles"
}


@lru_cache()
def get_user_data(username):
    res = requests.get(f'https://api.github.com/users/{username}',
                       auth=auth,
                       headers=headers)
    if res.status_code != 200:
        if res.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='User not found')

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail='Failed to retrieve user data')

    return res.json()
