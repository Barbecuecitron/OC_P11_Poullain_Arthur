from locust import HttpUser, task

class UserBehavior(HttpUser):
    @task()
    def show_summary(self):
        self.client.post("/showSummary",
                         {"email":"john@simplylift.co"})

    @task()
    def display_points(self):
        self.client.get("/points_display")

    @task()
    def purchase_places(self):
        self.client.post("/purchasePlaces",
                        {"competition":"Fall Classic",
                        "club": "Simply Lift",
                        "places":"1"
                        })
    @task()
    def logout(self):
        self.client.get("/logout")