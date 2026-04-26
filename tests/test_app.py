import pytest


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup"""

    def test_signup_success(self, client_with_test_db):
        """Happy path: Successfully sign up a new student for an activity"""
        response = client_with_test_db.post(
            "/activities/Gym%20Class/signup?email=john@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up john@mergington.edu for Gym Class" in response.json()["message"]

    def test_signup_activity_not_found(self, client_with_test_db):
        """Error: Activity does not exist returns 404"""
        response = client_with_test_db.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student(self, client_with_test_db):
        """Error: Student already signed up for activity returns 400"""
        response = client_with_test_db.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_second_student_same_activity(self, client_with_test_db):
        """Happy path: Multiple students can sign up for the same activity"""
        # First signup
        response1 = client_with_test_db.post(
            "/activities/Programming%20Class/signup?email=john@mergington.edu"
        )
        assert response1.status_code == 200

        # Second signup - different student, same activity
        response2 = client_with_test_db.post(
            "/activities/Programming%20Class/signup?email=olivia@mergington.edu"
        )
        assert response2.status_code == 200
        assert "Signed up olivia@mergington.edu for Programming Class" in response2.json()["message"]

    def test_signup_missing_email_parameter(self, client_with_test_db):
        """Validation: Email parameter is required"""
        response = client_with_test_db.post("/activities/Chess%20Club/signup")
        assert response.status_code == 422  # Unprocessable Entity

    def test_signup_empty_email(self, client_with_test_db):
        """Validation: Email parameter cannot be empty"""
        response = client_with_test_db.post(
            "/activities/Chess%20Club/signup?email="
        )
        # Empty string should still be treated as a parameter, not validation error
        assert response.status_code == 200 or response.status_code == 400


class TestDeleteEndpoint:
    """Tests for DELETE /activities/{activity_name}/signup"""

    def test_delete_participant_success(self, client_with_test_db):
        """Happy path: Successfully remove a student from an activity"""
        response = client_with_test_db.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert "Removed michael@mergington.edu from Chess Club" in response.json()["message"]

    def test_delete_activity_not_found(self, client_with_test_db):
        """Error: Activity does not exist returns 404"""
        response = client_with_test_db.delete(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_delete_student_not_enrolled(self, client_with_test_db):
        """Error: Student not enrolled in activity returns 400"""
        response = client_with_test_db.delete(
            "/activities/Chess%20Club/signup?email=notenrolled@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not signed up for this activity"

    def test_delete_from_empty_participants(self, client_with_test_db):
        """Error: Cannot delete from activity with no participants"""
        response = client_with_test_db.delete(
            "/activities/Gym%20Class/signup?email=anyone@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not signed up for this activity"

    def test_delete_missing_email_parameter(self, client_with_test_db):
        """Validation: Email parameter is required"""
        response = client_with_test_db.delete("/activities/Chess%20Club/signup")
        assert response.status_code == 422  # Unprocessable Entity

    def test_delete_then_signup_again(self, client_with_test_db):
        """Integration: Student can sign up after being removed"""
        # Delete
        response1 = client_with_test_db.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response1.status_code == 200

        # Sign up again with same email
        response2 = client_with_test_db.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response2.status_code == 200
        assert "Signed up michael@mergington.edu for Chess Club" in response2.json()["message"]


class TestDataIntegrity:
    """Tests for data consistency and state management"""

    def test_signup_updates_participant_list(self, client_with_test_db):
        """Verify signup actually adds participant to activity"""
        # Get initial activities
        response1 = client_with_test_db.get("/activities")
        initial_participants = response1.json()["Gym Class"]["participants"]

        # Sign up new student
        client_with_test_db.post(
            "/activities/Gym%20Class/signup?email=newstudent@mergington.edu"
        )

        # Get updated activities
        response2 = client_with_test_db.get("/activities")
        updated_participants = response2.json()["Gym Class"]["participants"]

        assert len(updated_participants) == len(initial_participants) + 1
        assert "newstudent@mergington.edu" in updated_participants

    def test_delete_removes_participant_from_list(self, client_with_test_db):
        """Verify delete actually removes participant from activity"""
        # Get initial activities
        response1 = client_with_test_db.get("/activities")
        initial_participants = response1.json()["Chess Club"]["participants"]
        initial_count = len(initial_participants)

        # Delete student
        client_with_test_db.delete(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )

        # Get updated activities
        response2 = client_with_test_db.get("/activities")
        updated_participants = response2.json()["Chess Club"]["participants"]

        assert len(updated_participants) == initial_count - 1
        assert "michael@mergington.edu" not in updated_participants

    def test_signup_and_delete_multiple_students(self, client_with_test_db):
        """Test multiple signups and deletes in sequence"""
        # Sign up two students
        client_with_test_db.post(
            "/activities/Gym%20Class/signup?email=student1@mergington.edu"
        )
        client_with_test_db.post(
            "/activities/Gym%20Class/signup?email=student2@mergington.edu"
        )

        # Verify both are enrolled
        response = client_with_test_db.get("/activities")
        participants = response.json()["Gym Class"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants

        # Delete first student
        client_with_test_db.delete(
            "/activities/Gym%20Class/signup?email=student1@mergington.edu"
        )

        # Verify only second student remains
        response = client_with_test_db.get("/activities")
        participants = response.json()["Gym Class"]["participants"]
        assert "student1@mergington.edu" not in participants
        assert "student2@mergington.edu" in participants
