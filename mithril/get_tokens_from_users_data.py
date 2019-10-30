from settings import *
import csv
import requests


urls = {
    'DEV': 'https://api.dev.edenlab.com.ua',
    'PREPROD': 'https://api-preprod.ehealth-ukraine.org'
}

def load_user_params():
    with open(f'./data/{environment.lower()}_users.csv', 'r') as csv_file:
        return list(csv.DictReader(csv_file, delimiter=';'))


def get_tokens():

    def login():
        # Get session token
        response = requests.post(url + '/auth/login', json={
            'token': {
                'grant_type': 'password',
                'email': user_params['email'],
                'password': user_params['password'],
                'client_id': config[environment]['AUTH_CLIENT_ID'],
                'scope': 'app:authorize'
            }
        })
        if 'data' in response.json():
            session_token = response.json()['data']['value']
        else:
            print(f'Failed get session token by user: {user_params["email"]}')
            return None

        # Get authorization token
        headers = {
            'Authorization': 'Bearer {token}'.format(token=session_token)
        }
        response = requests.post(url + '/oauth/apps/authorize', json={
            'app': {
                'client_id': user_params['client_id'],
                'redirect_uri': user_params['redirect_uri'],
                'scope': user_params['scope'],
            }
        }, headers=headers)
        if 'data' in response.json():
            auth_token = response.json()['data']['value']
        else:
            print(f'Failed get authorization token by user: {user_params["email"]}')
            return None

        # Get grant token
        response = requests.post(url + '/oauth/tokens', json={
            'token': {
                'grant_type': 'authorization_code',
                'code': auth_token,
                'client_id': user_params['client_id'],
                'client_secret': user_params['client_secret'],
                'redirect_uri': user_params['redirect_uri'],
                'scope': user_params['scope'],
            }
        })
        if 'data' in response.json():
            return response.json()['data']['value']
        else:
            print(f'Failed get grant token by user: {user_params["email"]}')
            return None

    url = urls[environment]
    tokens = []
    for user_params in load_user_params():
        token = login()
        if token:
            tokens.append(token)

    if tokens:
        print('value')
        for token in tokens:
            print(token)
    else:
        print('Failed to get tokens')


if __name__ == '__main__':
    get_tokens()
