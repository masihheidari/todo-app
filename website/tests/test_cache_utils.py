from website.cache_utils import task_list_cache_key


class FakeUser:
    class Role:
        ADMIN = 'admin'
        TEACHER = 'teacher'

    def __init__(self, role, id=1):
        self.role, self.id = role, id


def test_admin_and_teacher_share_role_based_key():
    assert task_list_cache_key(FakeUser('admin')) == 'task_list_role_admin'
    assert task_list_cache_key(FakeUser('teacher')) == 'task_list_role_teacher'


def test_student_gets_user_specific_key():
    assert task_list_cache_key(FakeUser('student', id=7)) == 'task_list_user_7'