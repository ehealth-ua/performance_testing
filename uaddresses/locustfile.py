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
  current_host_num = 0


class MedicalEventsTaskSequence(TaskSequence):
  hosts_list = ["http://localhost:4000"]
  current_host = None
  total_settlement_pages = 0
  settlement_id = None
  settlement_name = None
  region_id = None
  region_name = None
  area_id = None
  area_name = None
  total_region_pages = 0
  total_area_pages = 0

  @seq_task(1)
  def get_settlements(self):
    self.init_current_host()
    headers = self.login_headers()

    page = 1

    if self.total_settlement_pages != 0:
      page = random.randint(1, self.total_settlement_pages)

    response = self.client.get(
        "{host}/v2/settlements?page={page}".format(host=self.current_host, page=page), headers=headers, name="get_settlements")

    if response.status_code == 200:
      response_json = json.loads(response.text)
      self.total_settlement_pages = response_json["paging"]["total_pages"]

      settlement = random.choice(response_json["data"])
      self.settlement_id = settlement["id"]
      self.settlement_name = settlement["name"]

  @seq_task(2)
  def get_settlement(self):
    headers = self.login_headers()
    self.client.get(
        "{host}/v2/settlements/{id}".format(host=self.current_host, id=self.settlement_id), headers=headers, name="get_settlement")

  @seq_task(3)
  def get_settlements_by_name(self):
    headers = self.login_headers()
    self.client.get("{host}/v2/settlements?name={name}".format(
        host=self.current_host, name=self.settlement_name), headers=headers, name="get_settlements_by_name")

  @seq_task(4)
  def get_regions(self):
    headers = self.login_headers()

    page = 1

    if self.total_region_pages != 0:
      page = random.randint(1, self.total_region_pages)

    response = self.client.get(
        "{host}/v2/regions?page={page}".format(host=self.current_host, page=page), headers=headers, name="get_regions")

    if response.status_code == 200:
      response_json = json.loads(response.text)
      self.total_region_pages = response_json["paging"]["total_pages"]

      region = random.choice(response_json["data"])
      self.region_id = region["id"]
      self.region_name = region["name"]

  @seq_task(5)
  def get_region(self):
    headers = self.login_headers()
    self.client.get(
        "{host}/v2/regions/{id}".format(host=self.current_host, id=self.region_id), headers=headers, name="get_region")

  @seq_task(6)
  def get_settlements_by_region(self):
    headers = self.login_headers()
    self.client.get("{host}/v2/settlements?region={region}".format(
        host=self.current_host, region=self.region_name), headers=headers, name="get_settlements_by_region")

  @seq_task(7)
  def get_areas(self):
    headers = self.login_headers()

    page = 1

    if self.total_area_pages != 0:
      page = random.randint(1, self.total_area_pages)

    response = self.client.get(
        "{host}/v2/areas?page={page}".format(host=self.current_host, page=page), headers=headers, name="get_areas")

    if response.status_code == 200:
      response_json = json.loads(response.text)
      self.total_area_pages = response_json["paging"]["total_pages"]

      area = random.choice(response_json["data"])
      self.area_id = area["id"]
      self.area_name = area["name"]

  @seq_task(8)
  def get_area(self):
    headers = self.login_headers()
    self.client.get(
        "{host}/v2/areas/{id}".format(host=self.current_host, id=self.area_id), headers=headers, name="get_area")

  @seq_task(9)
  def get_settlements_by_area(self):
    headers = self.login_headers()
    self.client.get("{host}/v2/settlements?area={area}".format(
        host=self.current_host, area=self.area_name), headers=headers, name="get_settlements_by_area")

  @seq_task(10)
  def get_settlements_by_region_area_and_name(self):
    headers = self.login_headers()
    self.client.get("{host}/v2/settlements?region={region}&area={area}&name={name}".format(
        host=self.current_host, region=self.region_name, area=self.area_name, name=self.settlement_name), headers=headers, name="get_settlements_by_region_area_and_name")

  def init_current_host(self):
    hosts_count = len(self.hosts_list)

    self.current_host = self.hosts_list[SharedData.current_host_num]

    if SharedData.current_host_num == hosts_count - 1:
      SharedData.current_host_num = 0
    else:
      SharedData.current_host_num = SharedData.current_host_num + 1

  def login_headers(self):
    return {
        "x-consumer-id": str(uuid.uuid4())
    }


class WebsiteUser(HttpLocust):
  host = "some_host"
  api_key = "some_api_key"
  task_set = MedicalEventsTaskSequence
