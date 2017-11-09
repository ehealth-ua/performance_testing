from locust import HttpLocust, TaskSet, task

DEV = {
  "FE_CLIENT_ID": "e2e1d2c8-9bac-43c6-adef-83239940b30a",
  "MIS_EMAIL": "m.miliaieva+1@gmail.com",
  "MIS_PASSWORD": "12345678",
  "MIS_CLIENT_ID": "6bc9c62a-dda7-43eb-8ce5-720aec18a2e1",
  "MIS_REDIRECT_URI": "http://localhost:8080/auth/redirect",
  "MIS_SCOPES": 'legal_entity:read legal_entity:write legal_entity:mis_verify',
  "MIS_CLIENT_SECRET": 'UXhEczJacXh3Ri9SUkc4enhHTVVpQT09'
}
PREPROD = {
  "FE_CLIENT_ID": "e2e1d2c8-9bac-43c6-adef-83239940b30a",
  "MIS_EMAIL": "sp.virny+50@gmail.com",
  "MIS_PASSWORD": "12345678",
  "MIS_CLIENT_ID": "e32e51ac-f720-4e42-adb3-67d504f3ad30",
  "MIS_REDIRECT_URI": "https://admin.ehealth.world/auth/redirect",
  "MIS_SCOPES": 'legal_entity:nhs_verify legal_entity:deactivate legal_entity:read employee:read employee_request:write employee_request:read employee:deactivate employee:write  global_parameters:read global_parameters:write declaration:read declaration:write  global_parameters:read global_parameters:write declaration_request:read declaration_request:write declaration_documents:read declaration:approve declaration:reject',
  "MIS_CLIENT_SECRET": 'ZzluaHd0V01lU1IwTnd4VkdBcUZHUT09'
}

class MithrilTaskSet(TaskSet):
  @task(1)
  def login(self):
    self.do_login()

  @task(1)
  def verify_token(self):
    self.client.get("/admin/tokens/{token}/verify".format(token=self.do_login()))

  # def user_details(self):
  #   self.client.get("/admin/tokens/_%/user")

  # @task(100)
  # def report_stats(self):
  #   self.client.get("/reports/stats")

  def do_login(self):
    config = PREPROD
    """
    Get session token.
    """
    result = self.client.post("/oauth/tokens", json={
      "token": {
        "grant_type": "password",
        "email": config["MIS_EMAIL"],
        "password": config["MIS_PASSWORD"],
        "client_id": config["FE_CLIENT_ID"],
        "scope": "app:authorize"
      }
    })
    if "data" in result.json():
      session_token = result.json()["data"]["value"]
    else:
      return None

    """
    Get authorization token.
    """
    headers = {
      # "x-consumer-id": "53d781f1-8a32-484c-8b13-b82659e03f22",
      # "x-consumer-id": "8341b7d6-f9c7-472a-960c-7da953cc4ea4",
      'Authorization': 'Bearer {token}'.format(token=session_token)
    }
    result = self.client.post("/oauth/apps/authorize", json={
      "app": {
        "client_id": config["MIS_CLIENT_ID"],
        "redirect_uri": config["MIS_REDIRECT_URI"],
        "scope": config["MIS_SCOPES"],
      }
    }, headers=headers)
    if "data" in result.json():
      auth_token = result.json()["data"]["value"]
    else:
      return None

    """
    Get grant token.
    """
    result = self.client.post("/oauth/tokens", json={
      "token": {
        "grant_type": "authorization_code",
        "code": auth_token,
        "client_id": config["MIS_CLIENT_ID"],
        "client_secret": config["MIS_CLIENT_SECRET"],
        "redirect_uri": config["MIS_REDIRECT_URI"],
        "scope": config["MIS_SCOPES"],
      }
    })
    if "data" in result.json():
      return result.json()["data"]["value"]
    else:
      return None

class WebsiteUser(HttpLocust):
  task_set = MithrilTaskSet
  min_wait = 2000
  max_wait = 9000
