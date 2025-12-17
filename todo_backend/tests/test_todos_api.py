import os
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

# Ensure we default to memory backend for tests to avoid filesystem dependencies
os.environ.setdefault("PERSISTENCE_BACKEND", "memory")

# Import the FastAPI app
from src.api.main import app  # noqa: E402

client = TestClient(app)


def create_todo_payload(
    title="Test Task",
    description="Do something",
    completed=False,
    due_date=None,
):
    payload = {
        "title": title,
        "description": description,
        "completed": completed,
    }
    if due_date is not None:
        payload["due_date"] = due_date
    return payload


def assert_todo_shape(todo: dict):
    # Basic structure validation
    for key in ["id", "title", "completed", "created_at", "updated_at"]:
        assert key in todo
    # Optional fields
    assert "description" in todo
    assert "due_date" in todo
    # Type-ish checks
    assert isinstance(todo["id"], int)
    assert isinstance(todo["title"], str)
    assert isinstance(todo["completed"], bool)
    # Timestamps are ISO8601 strings parseable by datetime.fromisoformat
    # FastAPI/Pydantic returns strings for datetime fields
    datetime.fromisoformat(todo["created_at"])
    datetime.fromisoformat(todo["updated_at"])
    if todo["due_date"] is not None:
        datetime.fromisoformat(todo["due_date"])


class TestHealth:
    def test_health_check(self):
        res = client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == "Healthy"
        assert data["backend"] in ("memory", "sqlite")


class TestTodosCRUD:
    def test_create_todo_minimal(self):
        payload = create_todo_payload(title="Buy milk", description=None, completed=False)
        res = client.post("/api/v1/todos/", json=payload)
        assert res.status_code == 201
        todo = res.json()
        assert_todo_shape(todo)
        assert todo["title"] == "Buy milk"
        assert todo["description"] is None
        assert todo["completed"] is False

    def test_create_todo_with_due_date_date_string(self):
        payload = create_todo_payload(title="Pay bills", description="Electricity", due_date="2099-12-25")
        res = client.post("/api/v1/todos/", json=payload)
        assert res.status_code == 201
        todo = res.json()
        assert_todo_shape(todo)
        # Due date should be promoted to midnight
        assert todo["due_date"].startswith("2099-12-25")

    def test_get_todo_and_not_found(self):
        # Create new todo
        res_create = client.post("/api/v1/todos/", json=create_todo_payload(title="Read book"))
        assert res_create.status_code == 201
        todo = res_create.json()
        tid = todo["id"]

        # Retrieve
        res_get = client.get(f"/api/v1/todos/{tid}")
        assert res_get.status_code == 200
        fetched = res_get.json()
        assert fetched["id"] == tid
        assert fetched["title"] == "Read book"

        # Not found case
        res_404 = client.get("/api/v1/todos/999999")
        assert res_404.status_code == 404
        assert res_404.json()["detail"] == "Todo not found"

    def test_put_replace_todo(self):
        # Create
        res_create = client.post("/api/v1/todos/", json=create_todo_payload(title="Initial", description="A", completed=False))
        assert res_create.status_code == 201
        tid = res_create.json()["id"]

        # Replace with PUT (uses TodoCreate schema)
        new_payload = create_todo_payload(title="Replaced", description=None, completed=True, due_date="2100-01-01")
        res_put = client.put(f"/api/v1/todos/{tid}", json=new_payload)
        assert res_put.status_code == 200
        updated = res_put.json()
        assert updated["id"] == tid
        assert updated["title"] == "Replaced"
        assert updated["description"] is None
        assert updated["completed"] is True
        assert updated["due_date"].startswith("2100-01-01")

        # PUT not found
        res_put_nf = client.put("/api/v1/todos/424242", json=new_payload)
        assert res_put_nf.status_code == 404
        assert res_put_nf.json()["detail"] == "Todo not found"

    def test_patch_partial_update(self):
        # Create
        res_create = client.post("/api/v1/todos/", json=create_todo_payload(title="Partial", description="X"))
        assert res_create.status_code == 201
        tid = res_create.json()["id"]

        # Partial update: set completed true and change title
        patch_payload = {"title": "Partial Updated", "completed": True}
        res_patch = client.patch(f"/api/v1/todos/{tid}", json=patch_payload)
        assert res_patch.status_code == 200
        patched = res_patch.json()
        assert patched["id"] == tid
        assert patched["title"] == "Partial Updated"
        assert patched["completed"] is True
        # description should remain unchanged
        assert patched["description"] == "X"

        # PATCH not found
        res_patch_nf = client.patch("/api/v1/todos/123456", json={"title": "Nope"})
        assert res_patch_nf.status_code == 404
        assert res_patch_nf.json()["detail"] == "Todo not found"

    def test_delete_todo(self):
        # Create
        res_create = client.post("/api/v1/todos/", json=create_todo_payload(title="ToDelete"))
        tid = res_create.json()["id"]

        # Delete
        res_del = client.delete(f"/api/v1/todos/{tid}")
        assert res_del.status_code == 204
        assert res_del.text == ""

        # Subsequent get is 404
        res_get = client.get(f"/api/v1/todos/{tid}")
        assert res_get.status_code == 404
        # Deleting again should still be 404
        res_del_again = client.delete(f"/api/v1/todos/{tid}")
        assert res_del_again.status_code == 404
        assert res_del_again.json()["detail"] == "Todo not found"


class TestListPaginationFilteringSorting:
    def seed_todos(self, count=10):
        # Clear state isn't exposed; since repository is in-memory and persists within app instance,
        # we'll create a unique set with timestamps spread out.
        base = datetime.now()
        created_ids = []
        for i in range(count):
            due = (base + timedelta(days=i)).date().isoformat()
            payload = create_todo_payload(
                title=f"Task {i}",
                description=f"Desc {i}",
                completed=(i % 2 == 0),
                due_date=due,
            )
            res = client.post("/api/v1/todos/", json=payload)
            assert res.status_code == 201
            created_ids.append(res.json()["id"])
        return created_ids

    def test_list_basic_pagination(self):
        self.seed_todos(7)
        # First page
        res1 = client.get("/api/v1/todos/?limit=3&offset=0")
        assert res1.status_code == 200
        page1 = res1.json()
        assert "items" in page1 and "total" in page1
        assert page1["limit"] == 3
        assert page1["offset"] == 0
        assert isinstance(page1["total"], int)
        assert len(page1["items"]) <= 3

        # Second page
        res2 = client.get("/api/v1/todos/?limit=3&offset=3")
        assert res2.status_code == 200
        page2 = res2.json()
        assert page2["limit"] == 3
        assert page2["offset"] == 3
        # Not asserting equality of items to avoid coupling to sort default besides direction;
        # ensure we get non-empty or empty within bounds.
        assert len(page2["items"]) <= 3

    def test_list_filter_completed_true_false(self):
        self.seed_todos(6)  # creates 0..5, completed for even indices

        # Filter completed=true
        res_true = client.get("/api/v1/todos/?completed=true&limit=100")
        assert res_true.status_code == 200
        data_true = res_true.json()
        assert all(item["completed"] is True for item in data_true["items"])
        # Filter completed=false
        res_false = client.get("/api/v1/todos/?completed=false&limit=100")
        assert res_false.status_code == 200
        data_false = res_false.json()
        assert all(item["completed"] is False for item in data_false["items"])

    def test_list_search_q_matches_title_and_description(self):
        self.seed_todos(5)
        # Search by title "Task 1"
        res_title = client.get("/api/v1/todos/?q=Task 1&limit=100")
        assert res_title.status_code == 200
        data_title = res_title.json()
        assert any("Task 1" in item["title"] for item in data_title["items"])

        # Search by part of description
        res_desc = client.get("/api/v1/todos/?q=Desc 2&limit=100")
        assert res_desc.status_code == 200
        data_desc = res_desc.json()
        assert any("Desc 2" in (item["description"] or "") for item in data_desc["items"])

    def test_list_sort_and_order(self):
        self.seed_todos(5)
        # Default sort is -created_at (desc)
        res_default = client.get("/api/v1/todos/?limit=5")
        assert res_default.status_code == 200
        default_items = res_default.json()["items"]
        # Ensure items are in non-increasing created_at
        created_ts = [datetime.fromisoformat(t["created_at"]) for t in default_items]
        assert created_ts == sorted(created_ts, reverse=True)

        # Sort by created_at asc
        res_asc = client.get("/api/v1/todos/?sort=created_at&limit=5")
        assert res_asc.status_code == 200
        items_asc = res_asc.json()["items"]
        created_ts_asc = [datetime.fromisoformat(t["created_at"]) for t in items_asc]
        assert created_ts_asc == sorted(created_ts_asc, reverse=False)

        # Override order explicitly
        res_order_desc = client.get("/api/v1/todos/?sort=created_at&order=desc&limit=5")
        assert res_order_desc.status_code == 200
        items_order_desc = res_order_desc.json()["items"]
        created_ts_desc = [datetime.fromisoformat(t["created_at"]) for t in items_order_desc]
        assert created_ts_desc == sorted(created_ts_desc, reverse=True)

    def test_list_invalid_order_param(self):
        res = client.get("/api/v1/todos/?order=invalid")
        assert res.status_code == 400
        data = res.json()
        # FastAPI raises HTTPException with detail string
        assert data["detail"] == "order must be 'asc' or 'desc'"


class TestValidationErrors:
    def test_create_validation_error_title_empty(self):
        # Empty title should trigger 422 with our error format handler
        payload = {"title": "  ", "description": "x"}
        res = client.post("/api/v1/todos/", json=payload)
        assert res.status_code == 422
        body = res.json()
        # Our app returns a custom structure for validation errors
        assert body.get("error") == "ValidationError"
        assert body.get("message") == "Request validation failed"
        assert isinstance(body.get("detail"), list)

    def test_patch_validation_error_bad_due_date(self):
        # Create a todo
        res_create = client.post("/api/v1/todos/", json=create_todo_payload(title="Due date bad"))
        assert res_create.status_code == 201
        tid = res_create.json()["id"]

        # Patch with invalid due_date
        res_patch = client.patch(f"/api/v1/todos/{tid}", json={"due_date": "not-a-date"})
        assert res_patch.status_code == 422
        body = res_patch.json()
        assert body.get("error") == "ValidationError"
        assert body.get("message") == "Request validation failed"
        assert isinstance(body.get("detail"), list)
