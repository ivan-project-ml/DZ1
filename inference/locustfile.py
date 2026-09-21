from locust import HttpUser, task, between


class InferenceUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def predict(self):
        self.client.post(
            "/v1/predict",
            json={
                "text": "Hello it is test!!!!"
            },
        )

    @task(1)
    def health(self):
        self.client.get("/health")