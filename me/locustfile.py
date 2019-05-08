from locust import HttpLocust, TaskSequence, seq_task
from datetime import datetime
import base64
import copy
import json
import random
import string
import time
import uuid


class MedicalEventsTaskSequence(TaskSequence):
  task_timeout = 10.0
  client_id = None
  employee_id = None
  division_id = None
  patient_id = None
  episode_id = None
  inserted_conditions = []
  encounter_package = None
  api_key = "some_api_key"

  @seq_task(1)
  def create_episode(self):
    self.initTasksData()
    headers = self.login_headers()

    with open("./data/create_episode.json", "r") as json_file:
      json_data = json.load(json_file)

    json_data["id"] = self.episode_id
    json_data["name"] = self.randomString(random.randint(1, 200))
    json_data["period"]["start"] = datetime.today().strftime("%Y-%m-%d")
    json_data["managing_organization"]["identifier"]["value"] = self.client_id
    json_data["care_manager"]["identifier"]["value"] = self.employee_id

    self.client.post("/api/patients/{patient_id}/episodes".format(
      patient_id=self.patient_id), headers=headers, json=json_data)

  @seq_task(2)
  def create_encounter_package(self):
    time.sleep(self.task_timeout)
    headers = self.login_headers()
    encounter_id = str(uuid.uuid4())
    visit_id = str(uuid.uuid4())

    with open("./data/create_encounter_package.json", "r") as json_file:
      json_data = json.load(json_file)

    with open("./data/condition.json", "r") as json_file:
      condition_data = json.load(json_file)

    with open("./data/encounter.json", "r") as json_file:
      encounter = json.load(json_file)

    encounter["id"] = encounter_id
    encounter["date"] = datetime.today().strftime("%Y-%m-%d")
    encounter["visit"]["identifier"]["value"] = visit_id
    encounter["episode"]["identifier"]["value"] = self.episode_id
    encounter["performer"]["identifier"]["value"] = self.employee_id
    encounter["division"]["identifier"]["value"] = self.division_id
    encounter["prescriptions"] = self.randomString(random.randint(1, 2000))

    reference_previous_condition = bool(random.getrandbits(1))

    if reference_previous_condition and len(self.inserted_conditions) == 0:
      reference_previous_condition = False

    min_conditions_count = 0

    if len(self.inserted_conditions) == 0 or not reference_previous_condition:
      min_conditions_count = 1

    conditions_count = random.randint(min_conditions_count, 3)
    conditions = []

    for x in range(conditions_count):
      condition = copy.deepcopy(condition_data)
      condition["id"] = str(uuid.uuid4())
      condition["primary_source"] = bool(random.getrandbits(1))

      if condition["primary_source"]:
        del condition["report_origin"]
        condition["asserter"]["identifier"]["value"] = self.employee_id
      else:
        del condition["asserter"]

      condition["context"]["identifier"]["value"] = encounter_id
      condition["asserted_date"] = datetime.today().strftime("%Y-%m-%d")
      conditions.append(condition)
      self.inserted_conditions.append(condition["id"])

      if len(self.inserted_conditions) > 200:
        self.inserted_conditions.pop(0)

    if reference_previous_condition:
      encounter["diagnoses"][0]["condition"]["identifier"]["value"] = random.choice(
        self.inserted_conditions)
    else:
      encounter["diagnoses"][0]["condition"]["identifier"]["value"] = random.choice(conditions)[
        "id"]

    self.encounter_package = {"encounter": encounter, "conditions": conditions}
    signed_data = base64.b64encode(str(self.encounter_package).encode("ascii"))
    json_data["visit"]["id"] = visit_id
    json_data["signed_data"] = signed_data.decode("ascii")

    self.client.post("/api/patients/{patient_id}/encounter_package".format(
      patient_id=self.patient_id), headers=headers, json=json_data)

  @seq_task(3)
  def update_episode(self):
    headers = self.login_headers()

    with open("./data/update_episode.json", "r") as json_file:
      json_data = json.load(json_file)

    json_data["name"] = self.randomString(random.randint(1, 200))
    json_data["care_manager"]["identifier"]["value"] = self.employee_id

    self.client.patch("/api/patients/{patient_id}/episodes/{episode_id}".format(
      patient_id=self.patient_id, episode_id=self.episode_id), headers=headers, json=json_data)

  @seq_task(4)
  def cancel_encounter_package(self):
    time.sleep(self.task_timeout)
    headers = self.login_headers()

    with open("./data/cancel_encounter_package.json", "r") as json_file:
      json_data = json.load(json_file)

    self.encounter_package["encounter"]["cancellation_reason"] = {
      "coding": [{"system": "eHealth/cancellation_reasons", "code": "misspelling"}]}
    self.encounter_package["encounter"]["explanatory_letter"] = self.randomString(
      random.randint(1, 2000))
    signed_data = base64.b64encode(str(self.encounter_package).encode("ascii"))
    json_data["signed_data"] = signed_data.decode("ascii")

    self.client.patch("/api/patients/{patient_id}/encounter_package".format(
      patient_id=self.patient_id), headers=headers, json=json_data)

  @seq_task(5)
  def close_episode(self):
    headers = self.login_headers()

    with open("./data/close_episode.json", "r") as json_file:
      json_data = json.load(json_file)

    json_data["period"]["end"] = datetime.today().strftime("%Y-%m-%d")
    json_data["closing_summary"] = self.randomString(random.randint(1, 2000))

    self.client.patch("/api/patients/{patient_id}/episodes/{episode_id}/actions/close".format(
      patient_id=self.patient_id, episode_id=self.episode_id), headers=headers, json=json_data)

  # Helpers
  def initTasksData(self):
    with open("./data/context_data.txt", "r") as txt_file:
      lines = txt_file.read().splitlines()
      line = random.choice(lines)
      [self.client_id, self.employee_id, self.division_id,
       self.patient_id, self.token] = line.split(";")
      self.episode_id = str(uuid.uuid4())

  def randomString(self, stringLength=10):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))

  def login_headers(self):
    return {
      "x-consumer-id": str(uuid.uuid4()),
      "Authorization": "Bearer {token}".format(token=self.token),
      "api-key": self.api_key
    }


class WebsiteUser(HttpLocust):
  host = "http://localhost:4000"
  task_set = MedicalEventsTaskSequence
  min_wait = 2000
  max_wait = 9000
