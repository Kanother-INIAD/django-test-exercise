from django.test import TestCase, Client
from django.utils import timezone, dateparse
from datetime import datetime
from todo.models import Task
from django.urls import reverse


# Create your tests here.
class SampleTestCase(TestCase):
    def test_sample(self):
        self.assertEqual(1 + 2, 3)


class TaskModelTestCase(TestCase):
    def test_create_task1(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title="task1", due_at=due)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, "task1")
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, due)

    def test_create_task2(self):
        task = Task(title="task2")
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, "task2")
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, None)

    def test_is_overdue_future(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 6, 30, 0, 0, 0))
        task = Task(title="task1", due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))

    def test_is_overdue_past(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title="task2", due_at=due)
        task.save()

        self.assertTrue(task.is_overdue(current))

    def test_is_overdue_none(self):
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title="task3", due_at=None)
        task.save()

        self.assertFalse(task.is_overdue(current))


class TodoViewTestCase(TestCase):
    def test_index_get(self):
        client = Client()
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(len(response.context["tasks"]), 0)

    def test_index_post(self):
        client = Client()
        data = {"title": "Test Task", "due_at": "2024-06-30 23:59:59"}
        response = client.post("/", data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(len(response.context["tasks"]), 1)

    def test_index_get_order_post(self):
        task1 = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title="task2", due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get("/?order=post")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(response.context["tasks"][0], task1)
        self.assertEqual(response.context["tasks"][1], task2)

    def test_index_get_order_due(self):
        task1 = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title="task2", due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get("/?order=due")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/index.html")
        self.assertEqual(response.context["tasks"][0], task1)
        self.assertEqual(response.context["tasks"][1], task2)

    def test_detail_get_success(self):
        task = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get("/{}/".format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/detail.html")
        self.assertEqual(response.context["task"], task)

    def test_detail_get_fail(self):
        client = Client()
        response = client.get("/1/")

        self.assertEqual(response.status_code, 404)

    def test_update_get_success(self):
        task = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get("/{}/update".format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "todo/edit.html")
        self.assertEqual(response.context["task"], task)

    def test_update_edit_fail(self):
        task = Task(title="task1", due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        data = {"title": "Test Task", "due_at": "2024-06-30 23:59:59"}
        response = client.post("/{}/update".format(task.pk), data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.get(pk=task.pk).title, "Test Task")
        self.assertEqual(
            Task.objects.get(pk=task.pk).due_at,
            timezone.make_aware(dateparse.parse_datetime("2024-06-30 23:59:59")),
        )


class DeleteViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.task = Task.objects.create(
            title="Test Task", due_at=timezone.make_aware(datetime(2024, 7, 1))
        )

    def test_delete_task_success(self):
        response = self.client.post(reverse("delete", args=[self.task.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("index"))
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_delete_nonexistent_task(self):
        non_existent_task_id = 999
        response = self.client.post(reverse("delete", args=[non_existent_task_id]))
        self.assertEqual(response.status_code, 404)

    def test_delete_task_get_method(self):
        response = self.client.get(reverse("delete", args=[self.task.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("index"))


class TaskCloseTest(TestCase):

    def setUp(self):
        self.task = Task.objects.create(
            title="Close Test Task",
            completed=False,
            posted_at=timezone.now(),
            due_at=timezone.now() + timezone.timedelta(days=1),
        )

    def test_close_existing_task(self):
        response = self.client.post(reverse("close", args=[self.task.id]))
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertTrue(self.task.completed)

    def test_close_nonexistent_task(self):
        nonexistent_task_id = self.task.id + 1
        response = self.client.post(reverse("close", args=[nonexistent_task_id]))
        self.assertEqual(response.status_code, 404)
