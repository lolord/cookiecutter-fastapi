import random
import re
from string import ascii_lowercase, ascii_uppercase, digits, punctuation


def random_password(k: int = 8):
    _k = (k - 4) // 4 + 1
    loss = k - 3 * _k
    values = random.choices(ascii_lowercase, k=_k)
    values.extend(random.choices(ascii_uppercase, k=_k))
    values.extend(random.choices(digits, k=_k))
    values.extend(random.choices(punctuation, k=loss))
    random.shuffle(values)
    return str().join(values)


def snake2camel(snake: str, start_lower: bool = False) -> str:
    camel = snake.title()
    camel = re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)
    if start_lower:
        camel = re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)
    return camel


def camel2snake(camel: str) -> str:
    snake = re.sub(r"([a-zA-Z])([0-9])", lambda m: f"{m.group(1)}_{m.group(2)}", camel)
    snake = re.sub(r"([a-z0-9])([A-Z])", lambda m: f"{m.group(1)}_{m.group(2)}", snake)
    return snake.lower()
