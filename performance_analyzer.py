import datetime
import json
import time
import urllib.parse
from enum import Enum

import requests
from fastapi import status
from matplotlib import pyplot as plt

VERSION = "1.0.0"

URL = "http://localhost:8000/api"
# URL = "https://zolza-hairstyles.pl/api"
EMAIL = "test@test.pl"
PASSWORD = "Testing5!"


class AuthEndpoints(Enum):
    LOGIN = "auth/login"
    LOGOUT = "auth/logout"


class ResourceEndpoints(Enum):
    ME = "users/me"
    USERS = "users"
    SESSIONS = "auth/sessions"
    SETTINGS = "settings"
    APPOINTMENT_SLOTS = "appointments/slots"
    MY_APPOINTMENTS = "appointments/mine"
    ALL_APPOINTMENTS = "appointments/all"
    SERVICES = "services"
    SERVICE_DETAILS = "services/details"


class PerformanceAnalyzer:
    url: str
    auth_endpoints: AuthEndpoints
    resource_endpoints: ResourceEndpoints
    email: str
    password: str
    iterations: int

    bearer: str

    performance_data: dict = {"iterations": [], "total_run_time": None}

    def __init__(
        self,
        url,
        auth_endpoints: AuthEndpoints,
        resource_endpoints: ResourceEndpoints,
        email,
        password,
        iterations: int,
        report_prefix: str | None = None,
    ):
        self.url = url
        self.auth_endpoints = auth_endpoints
        self.resource_endpoints = resource_endpoints
        self.email = email
        self.password = password
        self.iterations = iterations
        self.report_prefix = report_prefix

    def _build_endpoint_url(self, endpoint: AuthEndpoints | ResourceEndpoints):
        return f"{self.url}/{endpoint.value}"

    def _get_auth_headers(self):
        if not self.bearer:
            raise Exception("Not Authenticated")

        return {"Authorization": f"Bearer {self.bearer}"}

    def _ensure_request_success(self, response):
        if response.status_code != status.HTTP_200_OK:
            raise Exception("Request failed: ", response.json())

    def _login(self):
        payload = f"grant_type=password&username={urllib.parse.quote(self.email)}&password={urllib.parse.quote(self.password)}"

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        response = requests.post(
            self._build_endpoint_url(self.auth_endpoints.LOGIN),
            headers=headers,
            data=payload,
        )

        self._ensure_request_success(response)

        self.bearer = response.json()["access_token"]

    def _logout(self):
        response = requests.post(
            self._build_endpoint_url(self.auth_endpoints.LOGOUT),
            headers=self._get_auth_headers(),
        )
        self._ensure_request_success(response)

    def _test_request(self, endpoint: ResourceEndpoints):
        response = requests.get(
            self._build_endpoint_url(endpoint), headers=self._get_auth_headers()
        )
        self._ensure_request_success(response)

    def _test_endpoints(self):
        endpoints_times = []

        for endpoint in self.resource_endpoints:
            start_time = time.time()
            self._test_request(endpoint)
            end_time = time.time()
            endpoint_time = end_time - start_time
            print(f"{endpoint.name} took {endpoint_time}")
            endpoints_times.append({"name": endpoint.name, "time": endpoint_time})

        return endpoints_times

    def _create_graphs(self, filename):
        endpoints = [
            endpoint["name"]
            for endpoint in self.performance_data["iterations"][0]["endpoints_times"]
        ]

        endpoints_count = len(self.performance_data["iterations"][0]["endpoints_times"])
        endpoints_times = [[] for _ in range(endpoints_count)]
        for i in range(endpoints_count):
            for j in range(len(self.performance_data["iterations"])):
                endpoints_times[i].append(
                    self.performance_data["iterations"][j]["endpoints_times"][i]["time"]
                )

        endpoints_average_times = []
        for endpoint_times in endpoints_times:
            endpoints_average_times.append(sum(endpoint_times) / self.iterations)

        plt.figure(figsize=(10, 6), num="API performance")
        plt.barh(endpoints, endpoints_average_times, color="skyblue")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Endpoints")
        plt.title("Time taken by each endpoint")
        plt.gca().invert_yaxis()  # Invert y-axis to have the endpoints listed from top to bottom

        plt.tight_layout()

        plt.savefig(f"{filename}.png")
        plt.savefig(f"{filename}.pdf")

        plt.show()

    def _save_data(self, filename):
        with open(f"{filename}.json", "w") as output_file:
            output_file.write(json.dumps(self.performance_data, indent=2))

    def run(self):
        run_start_time = time.time()

        for iteration in range(self.iterations):
            print(f"Starting iteration #{iteration + 1}")

            iteration_start_time = time.time()

            login_start_time = time.time()
            self._login()
            login_end_time = time.time()
            login_time = login_end_time - login_start_time
            print(f"LOGIN took {login_time}")

            test_endpoints_times = self._test_endpoints()

            logout_start_time = time.time()
            self._logout()
            logout_end_time = time.time()
            logout_time = logout_end_time - logout_start_time
            print(f"LOGOUT took {logout_time}")

            endpoints_times = [
                {"name": "LOGIN", "time": login_time},
                *test_endpoints_times,
                {"name": "LOGOUT", "time": logout_time},
            ]

            iteration_end_time = time.time()

            iteration_time = iteration_end_time - iteration_start_time

            print(f"Iteration #{iteration + 1} time: {iteration_time}")
            self.performance_data["iterations"].append(
                {"endpoints_times": endpoints_times, "iteration_time": iteration_time}
            )

        run_end_time = time.time()
        total_run_time = run_end_time - run_start_time

        print(f"Total run time: {total_run_time}")
        self.performance_data["total_run_time"] = total_run_time

        timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename = f"{self.report_prefix} PA V{VERSION} {timestamp} I-{self.iterations}"
        self._save_data(filename)
        self._create_graphs(filename)


def main():
    report_prefix = input("Please enter report prefix: ")

    performance_analyzer = PerformanceAnalyzer(
        URL, AuthEndpoints, ResourceEndpoints, EMAIL, PASSWORD, 10, report_prefix
    )
    performance_analyzer.run()


if __name__ == "__main__":
    main()
