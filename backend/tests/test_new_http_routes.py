import unittest
from fastapi.testclient import TestClient
from presentation.http.app import create_app
from composition import AppContext
from infrastructure.database import connect, initialize_schema
from infrastructure.seed_data import seed_default_data
from infrastructure.repositories import PetProfileRepository, NotificationRepository, RecordRepository, ScheduleRepository

class TestNewHttpRoutes(unittest.TestCase):
    def setUp(self):
        # Use a real in-memory DB instead of complex mocks to verify integration
        self.connection = connect(":memory:")
        seed_default_data(self.connection)
        
        # Seeded pets have NULL owner_user_id by default, update them for repository filter
        self.connection.execute("UPDATE pets SET owner_user_id = 'local-user'")
        self.connection.commit()
        
        # We need to build a context that uses this connection
        # For simplicity in this test, we'll patch the app's state
        self.app = create_app()
        self.app.state.app_context = AppContext(
            pet_log_agent_pipeline=None, # Not needed for these routes
            pet_profile_reader=PetProfileRepository(connection=self.connection),
            speech_to_text=None,
            record_reader=RecordRepository(connection=self.connection),
            schedule_reader=ScheduleRepository(connection=self.connection),
            notification_repository=NotificationRepository(connection=self.connection)
        )
        self.client = TestClient(self.app)

    def tearDown(self):
        self.connection.close()

    def test_get_me(self):
        response = self.client.get("/api/v1/me")
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["id"], "local-user")

    def test_pets_crud(self):
        # List (should have 3 seeded pets)
        response = self.client.get("/api/v1/pets")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]["pets"]), 3)

        # Create
        response = self.client.post("/api/v1/pets", json={"name": "New Cat", "species": "cat", "breed": "Tabby"})
        self.assertEqual(response.status_code, 200)
        new_pet_id = response.json()["data"]["id"]
        self.assertIsNotNone(new_pet_id)

        # Detail
        response = self.client.get(f"/api/v1/pets/{new_pet_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "New Cat")

        # Update
        response = self.client.patch(f"/api/v1/pets/{new_pet_id}", json={"name": "Updated Cat", "pet_id": new_pet_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["name"], "Updated Cat")

        # Delete
        response = self.client.delete(f"/api/v1/pets/{new_pet_id}")
        self.assertEqual(response.status_code, 200)
        
        # Verify deleted
        response = self.client.get(f"/api/v1/pets/{new_pet_id}")
        self.assertEqual(response.status_code, 404)

    def test_notifications_api(self):
        pet_id = "pet_01JCM7V8H9Q2K4N6R8T0A1B2C3"
        # Create a notification directly via repo for testing the GET API
        self.app.state.app_context.notification_repository.create(
            pet_id=pet_id,
            category="alert",
            title="API Test",
            detail="Detail",
            action="Go",
            action_href="/",
            due_label="Now",
            tone="info"
        )

        # List
        response = self.client.get(f"/api/v1/notifications?pet_id={pet_id}")
        self.assertEqual(response.status_code, 200)
        notifs = response.json()["data"]["notifications"]
        self.assertEqual(len(notifs), 1)
        notif_id = notifs[0]["id"]

        # Mark as read
        response = self.client.patch(f"/api/v1/notifications/{notif_id}/read")
        self.assertEqual(response.status_code, 200)

        # Mark all as read
        response = self.client.put(f"/api/v1/notifications/read?pet_id={pet_id}")
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()
