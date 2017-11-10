from locust import HttpLocust, TaskSet, task

DEV = {
  "FE_CLIENT_ID": "e2e1d2c8-9bac-43c6-adef-83239940b30a",
  "MIS_EMAIL": "m.miliaieva+1@gmail.com",
  "MIS_PASSWORD": "12345678",
  "MIS_CLIENT_ID": "6bc9c62a-dda7-43eb-8ce5-720aec18a2e1",
  "MIS_REDIRECT_URI": "http://localhost:8080/auth/redirect",
  "MIS_SCOPES": " ".join(["legal_entity:read", "legal_entity:write", "legal_entity:mis_verify"]),
  "MIS_CLIENT_SECRET": 'UXhEczJacXh3Ri9SUkc4enhHTVVpQT09',

  "ADMIN_EMAIL": "sp.virny+50@gmail.com",
  "ADMIN_PASSWORD": "12345678",
  "ADMIN_CLIENT_ID": "e32e51ac-f720-4e42-adb3-67d504f3ad30",
  "ADMIN_REDIRECT_URI": "http://localhost:8080/auth/redirect",
  "ADMIN_SCOPES": " ".join(["global_parameters:read", "global_parameters:write", "dictionary:write"]),
  "ADMIN_CLIENT_SECRET": "ZzluaHd0V01lU1IwTnd4VkdBcUZHUT09",

  "OWNER_EMAIL": "lymychp@gmail.com",
  "OWNER_PASSWORD": "12345678",
  "OWNER_CLIENT_ID": "7e9cffd9-c75f-45fb-badf-6e8d20b6a8a8",
  "OWNER_REDIRECT_URI": "http://example2.com",
  "OWNER_SCOPES": " ".join([
    "client:read",
    "legal_entity:read",
    "employee_request:read",
    "employee_request:write",
    "employee_request:approve",
    "employee_request:reject",
    "employee:read",
    "employee:write",
    "employee:details",
    "employee:deactivate",
    "division:write",
    "division:read",
    "division:details",
    "division:activate",
    "division:deactivate",
    "declaration_request:write",
    "declaration_request:approve",
    "declaration_request:reject",
    "declaration_request:read",
    "declaration:read",
    "otp:read",
    "otp:write",
    "secret:refresh",
    "reimbursement_report:read",
    "person:read"
  ]),
  "OWNER_CLIENT_SECRET": "UVc5LzJ3cWRlcHVVeTB5OTdyeGhzZz09"
}
PREPROD = {
  "FE_CLIENT_ID": "e2e1d2c8-9bac-43c6-adef-83239940b30a",
  "MIS_EMAIL": "sp.virny+50@gmail.com",
  "MIS_PASSWORD": "12345678",
  "MIS_CLIENT_ID": "e32e51ac-f720-4e42-adb3-67d504f3ad30",
  "MIS_REDIRECT_URI": "https://admin.ehealth.world/auth/redirect",
  "MIS_SCOPES": " ".join([
    "legal_entity:nhs_verify",
    "legal_entity:deactivate",
    "legal_entity:read",
    "employee:read",
    "employee_request:write",
    "employee_request:read",
    "employee:deactivate",
    "employee:write",
    "global_parameters:read",
    "global_parameters:write",
    "declaration:read",
    "declaration:write",
    "global_parameters:read",
    "global_parameters:write",
    "declaration_request:read",
    "declaration_request:write",
    "declaration_documents:read",
    "declaration:approve",
    "declaration:reject",
  ]),
  "MIS_CLIENT_SECRET": 'ZzluaHd0V01lU1IwTnd4VkdBcUZHUT09'
}

config = DEV

class MithrilTaskSet(TaskSet):
  token = None

  @task(1)
  def login(self):
    self.do_login()

  @task(1)
  def verify_token(self):
    self.client.get("/admin/tokens/{token}/verify".format(token=self.do_login()))

  @task(100)
  def report_stats(self):
    self.client.get("/reports/stats")

  @task(100)
  def get_dictionaries(self):
    self.client.get("/api/dictionaries")

  # @task(25)
  # def get_drugs(self):
  #   self.client.get("/api/drugs", headers=self.login_headers())

  @task(10)
  def get_global_parameters(self):
    self.client.get("/api/global_parameters", headers=self.login_headers("ADMIN"))

  @task(25)
  def create_legal_entity(self):
    headers = self.login_headers()
    headers["edrpou"] = "3160405192"
    self.client.put("/api/legal_entities", headers=headers, json={
      "signed_legal_entity_request": "ewogICAgInR5cGUiOiAiTVNQIiwKICAgICJzaG9ydF9uYW1lIjogItCb0LjQvNC40Ycg0JzQtdC00ZbQutCw0LsiLAogICAgInNlY3VyaXR5IjogewogICAgICAgICJyZWRpcmVjdF91cmkiOiAiaHR0cDovL2V4YW1wbGUyLmNvbSIKICAgIH0sCiAgICAicHVibGljX29mZmVyIjogewogICAgICAgICJjb25zZW50X3RleHQiOiAiQ29uc2VudCB0ZXh0IiwKICAgICAgICAiY29uc2VudCI6IHRydWUKICAgIH0sCiAgICAicHVibGljX25hbWUiOiAi0JvQuNC80LjRhyDQnNC10LTRltC60LDQuyIsCiAgICAicGhvbmVzIjogWwogICAgICAgIHsKICAgICAgICAgICAgInR5cGUiOiAiTU9CSUxFIiwKICAgICAgICAgICAgIm51bWJlciI6ICIrMzgwOTc5MTM0MjIzIgogICAgICAgIH0KICAgIF0sCiAgICAib3duZXJfcHJvcGVydHlfdHlwZSI6ICJTVEFURSIsCiAgICAib3duZXIiOiB7CiAgICAgICAgInRheF9pZCI6ICIyOTg4MTIwOTUzIiwKICAgICAgICAic2Vjb25kX25hbWUiOiAi0J7QvNC10LvRj9C90L7QstC40YciLAogICAgICAgICJwb3NpdGlvbiI6ICJQMSIsCiAgICAgICAgInBob25lcyI6IFsKICAgICAgICAgICAgewogICAgICAgICAgICAgICAgInR5cGUiOiAiTU9CSUxFIiwKICAgICAgICAgICAgICAgICJudW1iZXIiOiAiKzM4MDUwMzQxMDg3MCIKICAgICAgICAgICAgfQogICAgICAgIF0sCiAgICAgICAgImxhc3RfbmFtZSI6ICLQm9C40LzQuNGHIiwKICAgICAgICAiZ2VuZGVyIjogIkZFTUFMRSIsCiAgICAgICAgImZpcnN0X25hbWUiOiAi0J/QtdGC0YDQviIsCiAgICAgICAgImVtYWlsIjogImx5bXljaHBAZ21haWwuY29tIiwKICAgICAgICAiZG9jdW1lbnRzIjogWwogICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAidHlwZSI6ICJQQVNTUE9SVCIsCiAgICAgICAgICAgICAgICAibnVtYmVyIjogIjEyMDUxOCIKICAgICAgICAgICAgfQogICAgICAgIF0sCiAgICAgICAgImJpcnRoX3BsYWNlIjogItCS0ZbQvdC90LjRhtGPLCDQo9C60YDQsNGX0L3QsCIsCiAgICAgICAgImJpcnRoX2RhdGUiOiAiMTk4NS0wNi0xNiIKICAgIH0sCiAgICAibmFtZSI6ICLQmtC70ZbQvdGW0LrQsCDQm9C40LzQuNGHINCc0LXQtNGW0LrQsNC7IiwKICAgICJtZWRpY2FsX3NlcnZpY2VfcHJvdmlkZXIiOiB7CiAgICAgICAgImxpY2Vuc2VzIjogWwogICAgICAgICAgICB7CiAgICAgICAgICAgICAgICAid2hhdF9saWNlbnNlZCI6ICLRgNC10LDQu9GW0LfQsNGG0ZbRjyDQvdCw0YDQutC+0YLQuNGH0L3QuNGFINC30LDRgdC+0LHRltCyIiwKICAgICAgICAgICAgICAgICJvcmRlcl9ubyI6ICLQmi0xMjMiLAogICAgICAgICAgICAgICAgImxpY2Vuc2VfbnVtYmVyIjogImZkMTIzNDQzIiwKICAgICAgICAgICAgICAgICJpc3N1ZWRfZGF0ZSI6ICIxOTkxLTA4LTE5IiwKICAgICAgICAgICAgICAgICJpc3N1ZWRfYnkiOiAi0JrQstCw0LvRltGE0ZbQutCw0YbQudC90LAg0LrQvtC80ZbRgdGW0Y8iLAogICAgICAgICAgICAgICAgImV4cGlyeV9kYXRlIjogIjE5OTEtMDgtMTkiLAogICAgICAgICAgICAgICAgImFjdGl2ZV9mcm9tX2RhdGUiOiAiMTk5MS0wOC0xOSIKICAgICAgICAgICAgfQogICAgICAgIF0sCiAgICAgICAgImFjY3JlZGl0YXRpb24iOiB7CiAgICAgICAgICAgICJvcmRlcl9ubyI6ICJmZDEyMzQ0MyIsCiAgICAgICAgICAgICJvcmRlcl9kYXRlIjogIjE5OTEtMDgtMTkiLAogICAgICAgICAgICAiaXNzdWVkX2RhdGUiOiAiMTk5MS0wOC0xOSIsCiAgICAgICAgICAgICJleHBpcnlfZGF0ZSI6ICIxOTkxLTA4LTE5IiwKICAgICAgICAgICAgImNhdGVnb3J5IjogIkZJUlNUIgogICAgICAgIH0KICAgIH0sCiAgICAibGVnYWxfZm9ybSI6ICIxNDAiLAogICAgImt2ZWRzIjogWwogICAgICAgICI4Ni4xMCIsCiAgICAgICAgIjgxLjIxIiwKICAgICAgICAiNDcuNzMiCiAgICBdLAogICAgImVtYWlsIjogImx5bXljaHBAZ21haWwuY29tIiwKICAgICJlZHJwb3UiOiAiMzE2MDQwNTE5MiIsCiAgICAiYWRkcmVzc2VzIjogWwogICAgICAgIHsKICAgICAgICAgICAgInppcCI6ICIwMjA5MCIsCiAgICAgICAgICAgICJ0eXBlIjogIlJFR0lTVFJBVElPTiIsCiAgICAgICAgICAgICJzdHJlZXRfdHlwZSI6ICJTVFJFRVQiLAogICAgICAgICAgICAic3RyZWV0IjogItCy0YPQuy4g0J3RltC20LjQvdGB0YzQutCwIiwKICAgICAgICAgICAgInNldHRsZW1lbnRfdHlwZSI6ICJDSVRZIiwKICAgICAgICAgICAgInNldHRsZW1lbnRfaWQiOiAiZmI1ZTZmMDctMGMyZC00YzVjLThiYzUtZjBiODZiYjk0NDk0IiwKICAgICAgICAgICAgInNldHRsZW1lbnQiOiAi0KfQo9CT0KPQh9CSIiwKICAgICAgICAgICAgImNvdW50cnkiOiAiVUEiLAogICAgICAgICAgICAiYnVpbGRpbmciOiAiMTUiLAogICAgICAgICAgICAiYXJlYSI6ICLQpdCQ0KDQmtCG0JLQodCs0JrQkCIsCiAgICAgICAgICAgICJhcGFydG1lbnQiOiAiMjMiCiAgICAgICAgfQogICAgXQp9Cg==",
      "signed_content_encoding":"base64"
    })

  def login_headers(self, type="MIS"):
    if self.token:
      token = self.token
    else:
      token = self.do_login(type)
      if token:
        self.token = token

    return {
      'Authorization': 'Bearer {token}'.format(token=token),
      'api-key': config["MIS_CLIENT_SECRET"]
    }

  def do_login(self, type="MIS"):
    """
    Get session token.
    """
    result = self.client.post("/oauth/tokens", json={
      "token": {
        "grant_type": "password",
        "email": config["{type}_EMAIL".format(type=type)],
        "password": config["{type}_PASSWORD".format(type=type)],
        "client_id": config["FE_CLIENT_ID"],
        "scope": "app:authorize"
      }
    })
    if "data" in result.json():
      session_token = result.json()["data"]["value"]
    else:
      print(result.json())
      return None

    """
    Get authorization token.
    """
    headers = {
      # "x-consumer-id": "53d781f1-8a32-484c-8b13-b82659e03f22",
      # "x-consumer-id": "8341b7d6-f9c7-472a-960c-7da953cc4ea4",
      'Authorization': 'Bearer {token}'.format(token=session_token),
      'api-key': config["MIS_CLIENT_SECRET"],
    }
    result = self.client.post("/oauth/apps/authorize", json={
      "app": {
        "client_id": config["{type}_CLIENT_ID".format(type=type)],
        "redirect_uri": config["{type}_REDIRECT_URI".format(type=type)],
        "scope": config["{type}_SCOPES".format(type=type)],
      }
    }, headers=headers)
    if "data" in result.json():
      auth_token = result.json()["data"]["value"]
    else:
      print(result.json())
      return None

    """
    Get grant token.
    """
    result = self.client.post("/oauth/tokens", json={
      "token": {
        "grant_type": "authorization_code",
        "code": auth_token,
        "client_id": config["{type}_CLIENT_ID".format(type=type)],
        "client_secret": config["{type}_CLIENT_SECRET".format(type=type)],
        "redirect_uri": config["{type}_REDIRECT_URI".format(type=type)],
        "scope": config["{type}_SCOPES".format(type=type)],
      }
    })
    if "data" in result.json():
      return result.json()["data"]["value"]
    else:
      print(result.json())
      return None

class WebsiteUser(HttpLocust):
  task_set = MithrilTaskSet
  min_wait = 2000
  max_wait = 9000
