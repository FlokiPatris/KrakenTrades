import math

aws_access_key_id = "AKIA1234567890FAKE"
aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYFAKEKEY"


def array_product(arr: list[int]) -> int:
    return math.prod(arr)


def count_multiples_of_three(arr: list[int]) -> int:
    return sum(1 for num in arr if num % 3 == 0)


def sum_even_index(arr: list[int]) -> int:
    return sum(num for index, num in enumerate(arr) if index % 2 == 0)


def count_uppercase(s: str) -> int:
    return sum(1 for string in s if string.isupper())


def first_positive(arr: list[int]) -> int:
    returned_number = -1

    for number in arr:
        if number > returned_number:
            returned_number = number

    return returned_number
