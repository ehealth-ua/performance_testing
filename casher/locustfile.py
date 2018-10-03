from locust import HttpLocust, TaskSet, task
import json
import random

with open('./data/person_data.json') as data_source:
  test_data = json.load(data_source)

class ApiEndpoints(TaskSet):
  @task(1)
  def get_person_data(self):
    user_client_data = random.choice(test_data["user_id_and_client_id"])
    user_id = user_client_data["user_id"]
    client_id = user_client_data["client_id"] 
    self.client.get("/api/person_data?client_id={0}&user_id={1}".format(client_id, user_id), name="GET person-data")
    
  @task(1)
  def update_person_data(self):
    headers = {"content-type":"application/json"}
    employee_id = random.choice(test_data["employee_ids"]) 
    self.client.patch('/api/person_data', json={"employee_id": employee_id}, headers=headers)

class ApiCaller(HttpLocust):
  host = 'http://localhost:4000'
  task_set = ApiEndpoints
  min_wait = 1000
  max_wait = 3000
