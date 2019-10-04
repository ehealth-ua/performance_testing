from locust import HttpLocust, TaskSet, task
from settings import *
from itertools import cycle
import csv


def load_user_params():
    with open(f'./data/{environment.lower()}_users.csv', 'r') as csv_file:
        return list(csv.DictReader(csv_file, delimiter=';'))


users_params = load_user_params()


def get_user_params():
    for user in cycle(users_params):
        yield user


user_params_generator = get_user_params()


class UserLoginTasks(TaskSet):

    def login(self):
        user_params = next(user_params_generator)

        # Get session token
        response = self.client.post('/auth/login', json={
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
        response = self.client.post('/oauth/apps/authorize', json={
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
        response = self.client.post('/oauth/tokens', json={
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

    @task(1)
    def verify_token(self):
        token = self.login()
        if token:
            headers = {
                'api-key': config[environment]['MIS_API_KEY']
            }
            self.client.get('/admin/tokens/{token}/verify'.format(token=token), headers=headers)


class LoginLocust(HttpLocust):
    task_set = UserLoginTasks
    min_wait = 2000
    max_wait = 9000
