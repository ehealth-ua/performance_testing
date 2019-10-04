from locust import HttpLocust, TaskSet, task
from settings import *
from itertools import cycle
import csv


def load_tokens():
    with open(f'./data/{environment.lower()}_tokens.csv', 'r') as csv_file:
        return list(csv.DictReader(csv_file, delimiter=';'))


user_tokens = load_tokens()


def get_user_token():
    for user in cycle(user_tokens):
        yield user


user_tokens_generator = get_user_token()


class TokenVerifyTasks(TaskSet):

    @task(1)
    def verify_token(self):
        token = next(user_tokens_generator)['value']
        if token:
            headers = {
                'api-key': config[environment]['MIS_API_KEY']
            }
            self.client.get('/admin/tokens/{token}/verify'.format(token=token), headers=headers, name='verify_token')


class VerifyLocust(HttpLocust):
    task_set = TokenVerifyTasks
    min_wait = 2000
    max_wait = 9000
