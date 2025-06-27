import random
import re
from string import ascii_lowercase, ascii_uppercase, digits, punctuation


def distribute_evenly(x: int, n: int) -> list:
    """
    Distributes the integer x into a list of n positive integers such that the distribution is as even as possible.

    Parameters:
    x (int): The integer to be distributed.
    n (int): The number of parts to divide x into.

    Returns:
    list: A list of n integers whose sum is x, with each integer greater than zero and the distribution as even as possible.

    Example:
    >>> distribute_evenly(7, 4)
    [2, 2, 2, 1]
    >>> distribute_evenly(10, 3)
    [4, 3, 3]
    """

    base_value = x // n
    remainder = x % n
    result = [base_value] * n
    for i in range(remainder):
        result[i] += 1

    return result


def random_password(k: int = 8) -> str:
    """生成一个包含小写字母、大写字母、数字和标点符号的随机密码

    Args:
        k (int): 密码长度, 默认为8

    Returns:
        str: 随机生成的密码字符串
    """

    counts = distribute_evenly(k, 4)
    values = random.choices(ascii_lowercase, k=counts[0])
    values.extend(random.choices(ascii_uppercase, k=counts[1]))
    values.extend(random.choices(digits, k=counts[2]))
    values.extend(random.choices(punctuation, k=counts[3]))
    random.shuffle(values)
    return str().join(values)


def snake2camel(snake: str, start_lower: bool = False) -> str:
    camel = snake.title()
    camel = re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)
    if start_lower:
        camel = re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)
    return camel


def camel2snake(camel: str) -> str:
    # Insert underscores between lowercase letters and uppercase letters
    snake = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", camel)
    # Insert underscores between numbers and letters
    snake = re.sub(r"(?<=[0-9])(?=[A-Z])", "_", snake)
    return snake.lower()
