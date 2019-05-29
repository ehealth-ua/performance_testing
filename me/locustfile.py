from locust import HttpLocust, TaskSequence, seq_task
from datetime import datetime, timezone
import base64
import copy
import json
import random
import string
import time
import uuid


class SharedData(object):
  inserted_visits = {}
  inserted_conditions = {}


class MedicalEventsTaskSequence(TaskSequence):
  task_timeout = 5.0
  token = None
  client_id = None
  employee_id = None
  division_id = None
  patient_id = None
  episode_id = None
  encounter_id = None
  encounter_package = None
  error = False
  job_url = None

  @seq_task(1)
  def create_episode(self):
    self.initTasksData()
    headers = self.login_headers()

    with open("./data/create_episode.json", "r") as json_file:
      json_data = json.load(json_file)

    json_data["id"] = self.episode_id
    json_data["name"] = self.randomString(random.randint(1, 200))
    json_data["period"]["start"] = datetime.now(
      timezone.utc).strftime("%Y-%m-%d")
    json_data["managing_organization"]["identifier"]["value"] = self.client_id
    json_data["care_manager"]["identifier"]["value"] = self.employee_id

    response = self.client.post("/api/patients/{patient_id}/episodes".format(
      patient_id=self.patient_id), headers=headers, json=json_data, name="create_episode")

    if response.status_code != 202:
      self.error = True
    else:
      response_json = json.loads(response.text)
      self.job_url = response_json["data"]["links"][0]["href"]

  @seq_task(2)
  def get_episodes(self):
    if self.error:
      return

    headers = self.login_headers()

    while True:
      time.sleep(self.task_timeout)

      response = self.client.get("/api{job_url}".format(
        job_url=self.job_url), headers=headers, name="get_job")

      if response.status_code == 200 or response.status_code == 303:
        response_json = json.loads(response.text)
        if response_json["data"]["status"] != "pending":
          break

    self.client.get("/api/patients/{patient_id}/episodes".format(
      patient_id=self.patient_id), headers=headers, name="get_episodes")

  @seq_task(3)
  def get_episode(self):
    if self.error:
      return

    headers = self.login_headers()

    self.client.get("/api/patients/{patient_id}/episodes/{episode_id}".format(
      patient_id=self.patient_id, episode_id=self.episode_id), headers=headers, name="get_episode")

  @seq_task(4)
  def create_encounter_package(self):
    if self.error:
      return

    headers = self.login_headers()
    self.encounter_id = str(uuid.uuid4())
    visit_id = str(uuid.uuid4())

    with open("./data/create_encounter_package.json", "r") as json_file:
      json_data = json.load(json_file)

    with open("./data/condition.json", "r") as json_file:
      condition_data = json.load(json_file)

    with open("./data/encounter.json", "r") as json_file:
      encounter = json.load(json_file)

    encounter["id"] = self.encounter_id
    encounter["date"] = datetime.now(timezone.utc).isoformat()
    encounter["episode"]["identifier"]["value"] = self.episode_id
    encounter["performer"]["identifier"]["value"] = self.employee_id
    encounter["division"]["identifier"]["value"] = self.division_id
    encounter["prescriptions"] = self.randomString(random.randint(1, 2000))

    reference_previous_visit = bool(random.getrandbits(1))
    reference_previous_condition = bool(random.getrandbits(1))

    if self.patient_id not in SharedData.inserted_visits:
      SharedData.inserted_visits[self.patient_id] = []

    if self.patient_id not in SharedData.inserted_conditions:
      SharedData.inserted_conditions[self.patient_id] = []

    if reference_previous_visit and len(SharedData.inserted_visits[self.patient_id]) == 0:
      reference_previous_visit = False

    if reference_previous_condition and len(SharedData.inserted_conditions[self.patient_id]) == 0:
      reference_previous_condition = False

    if len(SharedData.inserted_visits[self.patient_id]) > 200:
      SharedData.inserted_visits[self.patient_id].pop(0)

    if reference_previous_visit:
      encounter["visit"]["identifier"]["value"] = random.choice(
        SharedData.inserted_visits[self.patient_id])
      del json_data["visit"]
    else:
      encounter["visit"]["identifier"]["value"] = visit_id
      json_data["visit"]["id"] = visit_id

    min_conditions_count = 0

    if len(SharedData.inserted_conditions[self.patient_id]) == 0 or not reference_previous_condition:
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

      condition["context"]["identifier"]["value"] = self.encounter_id
      condition["asserted_date"] = datetime.now(timezone.utc).isoformat()
      conditions.append(condition)

      if len(SharedData.inserted_conditions[self.patient_id]) > 200:
        SharedData.inserted_conditions[self.patient_id].pop(0)

    if reference_previous_condition:
      encounter["diagnoses"][0]["condition"]["identifier"]["value"] = random.choice(
        SharedData.inserted_conditions[self.patient_id])
    else:
      encounter["diagnoses"][0]["condition"]["identifier"]["value"] = random.choice(conditions)[
        "id"]

    self.encounter_package = {"encounter": encounter, "conditions": conditions}
    signed_data = base64.b64encode(json.dumps(
      self.encounter_package).encode("ascii"))
    json_data["signed_data"] = signed_data.decode("ascii")

    response = self.client.post("/api/patients/{patient_id}/encounter_package".format(
      patient_id=self.patient_id), headers=headers, json=json_data, name="create_encounter_package")

    if response.status_code == 202:
      response_json = json.loads(response.text)
      self.job_url = response_json["data"]["links"][0]["href"]

      while True:
        time.sleep(self.task_timeout)

        job_response = self.client.get("/api{job_url}".format(
          job_url=self.job_url), headers=headers, name="get_job")

        if job_response.status_code == 200 or job_response.status_code == 303:
          response_json = json.loads(job_response.text)
          if response_json["data"]["status"] == "processed":
            SharedData.inserted_visits[self.patient_id].append(visit_id)

            for x in range(conditions_count):
              SharedData.inserted_conditions[self.patient_id].append(
                conditions[x]["id"])

          if response_json["data"]["status"] == "failed" or response_json["data"]["status"] == "failed_with_error":
            print(reference_previous_visit)
            self.error = True

          if response_json["data"]["status"] != "pending":
            break

    if response.status_code != 202:
      self.error = True

  @seq_task(5)
  def update_episode(self):
    if self.error:
      return

    headers = self.login_headers()

    with open("./data/update_episode.json", "r") as json_file:
      json_data = json.load(json_file)

    json_data["name"] = self.randomString(random.randint(1, 200))
    json_data["care_manager"]["identifier"]["value"] = self.employee_id

    self.client.patch("/api/patients/{patient_id}/episodes/{episode_id}".format(
      patient_id=self.patient_id, episode_id=self.episode_id), headers=headers, json=json_data, name="update_episode")

  @seq_task(6)
  def get_encounters(self):
    if self.error:
      return

    headers = self.login_headers()

    self.client.get("/api/patients/{patient_id}/episodes/{episode_id}/encounters".format(
      patient_id=self.patient_id, episode_id=self.episode_id), headers=headers, name="get_encounters")

  @seq_task(7)
  def get_encounter(self):
    if self.error:
      return

    headers = self.login_headers()

    self.client.get("/api/patients/{patient_id}/episodes/{episode_id}/encounters/{encounter_id}".format(
      patient_id=self.patient_id, episode_id=self.episode_id, encounter_id=self.encounter_id), headers=headers, name="get_encounter")

  @seq_task(8)
  def cancel_encounter_package(self):
    if self.error:
      return

    headers = self.login_headers()

    with open("./data/cancel_encounter_package.json", "r") as json_file:
      json_data = json.load(json_file)

    self.encounter_package["encounter"]["cancellation_reason"] = {
      "coding": [{"system": "eHealth/cancellation_reasons", "code": "typo"}]}
    self.encounter_package["encounter"]["explanatory_letter"] = self.randomString(
      random.randint(1, 2000))
    self.encounter_package["encounter"]["status"] = "entered_in_error"
    conditions_count = len(self.encounter_package["conditions"])

    for x in range(conditions_count):
      self.encounter_package["conditions"][x]["verification_status"] = "entered_in_error"

    signed_data = base64.b64encode(json.dumps(
      self.encounter_package).encode("ascii"))
    json_data["signed_data"] = signed_data.decode("ascii")

    self.client.patch("/api/patients/{patient_id}/encounter_package".format(
      patient_id=self.patient_id), headers=headers, json=json_data, name="cancel_encounter_package")

  @seq_task(9)
  def close_episode(self):
    if self.error:
      return

    headers = self.login_headers()

    with open("./data/close_episode.json", "r") as json_file:
      json_data = json.load(json_file)

    json_data["period"]["end"] = datetime.now(
      timezone.utc).strftime("%Y-%m-%d")
    json_data["closing_summary"] = self.randomString(random.randint(1, 2000))

    self.client.patch("/api/patients/{patient_id}/episodes/{episode_id}/actions/close".format(
      patient_id=self.patient_id, episode_id=self.episode_id), headers=headers, json=json_data, name="close_episode")

  @seq_task(10)
  def get_conditions(self):
    if self.error:
      return

    headers = self.login_headers()

    self.client.get("/api/patients/{patient_id}/conditions".format(
      patient_id=self.patient_id, episode_id=self.episode_id), headers=headers, name="get_conditions")

  @seq_task(11)
  def get_condition(self):
    if self.error:
      return

    headers = self.login_headers()
    condition_id = SharedData.inserted_conditions[self.patient_id][len(
      SharedData.inserted_conditions[self.patient_id]) - 1]

    self.client.get("/api/patients/{patient_id}/conditions/{condition_id}".format(
      patient_id=self.patient_id, episode_id=self.episode_id, condition_id=condition_id), headers=headers, name="get_condition")

  def initTasksData(self):
    with open("./data/context_data.txt", "r") as context_data_file:
      context_data = context_data_file.read().splitlines()

    context = random.choice(context_data)
    [self.client_id, self.employee_id, self.division_id,
     self.patient_id, self.token] = context.split(";")
    self.episode_id = str(uuid.uuid4())

  def randomString(self, stringLength=10):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(stringLength))

  def login_headers(self):
    return {
      "x-consumer-id": str(uuid.uuid4()),
      "Authorization": "Bearer {token}".format(token=self.token),
      "api-key": self.locust.api_key
    }


class WebsiteUser(HttpLocust):
  host = "http://localhost:4000"
  api_key = "some_api_key"
  task_set = MedicalEventsTaskSequence
