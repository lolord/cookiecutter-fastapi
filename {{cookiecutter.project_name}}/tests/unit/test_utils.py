import re


from {{cookiecutter.project_name}}.settings import settings
from {{cookiecutter.project_name}}.utils import camel2snake, distribute_evenly, random_password, snake2camel


def test_snake2camel():
    assert snake2camel("hello_world") == "HelloWorld"
    assert snake2camel("hello_world", start_lower=True) == "helloWorld"
    assert snake2camel("hello_world_123") == "HelloWorld123"
    assert snake2camel("hello_world_123", start_lower=True) == "helloWorld123"


def test_camel2snake():
    assert camel2snake("HelloWorld") == "hello_world"
    assert camel2snake("helloWorld") == "hello_world"
    assert camel2snake("HelloWorld123") == "hello_world123"
    assert camel2snake("helloWorld123") == "hello_world123"
    assert camel2snake("Hello123World") == "hello123_world"
    assert camel2snake("Hello123World456") == "hello123_world456"


def test_distribute_evenly():
    assert distribute_evenly(7, 4) == [2, 2, 2, 1]
    assert distribute_evenly(10, 3) == [4, 3, 3]
    assert distribute_evenly(5, 5) == [1, 1, 1, 1, 1]
    assert distribute_evenly(9, 2) == [5, 4]
    assert distribute_evenly(12, 5) == [3, 3, 2, 2, 2]
    assert distribute_evenly(1, 1) == [1]


def test_random_password():
    s = random_password(6)
    assert re.match(settings.PASSWORD_REGEX, s), s
    s = random_password(7)
    assert re.match(settings.PASSWORD_REGEX, s), s
    s = random_password(8)
    assert re.match(settings.PASSWORD_REGEX, s), s
