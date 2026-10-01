from website.tests.factories import TaskFactory


def test_marking_done_sets_finished_date(db):
    task = TaskFactory(is_done=False)
    assert task.finished_date is None

    task.is_done = True
    task.save()
    # Reload to make sure the value was really saved to the database
    task.refresh_from_db()

    assert task.finished_date is not None


def test_unmarking_done_clears_finished_date(db):
    task = TaskFactory(is_done=True)
    task.refresh_from_db()
    assert task.finished_date is not None

    task.is_done = False
    task.save()
    task.refresh_from_db()

    assert task.finished_date is None
