import pytest
from app.utils.slug import slugify


# Use pytest.mark.parametrize to run many tests through the same function
@pytest.mark.parametrize(
    "input_text, expected_slug",
    [
        # 1. Basic cases from the docstring
        ("My Python Course", "my-python-course"),
        ("Learn Python!", "learn-python"),
        # 2. Case conversion
        ("HELLO WORLD", "hello-world"),
        ("PyThOn Is FuN", "python-is-fun"),
        # 3. Non-alphanumeric and space replacement
        ("multiple   spaces", "multiple-spaces"),
        ("a!@#$%^&*()_+=b", "a-b"),  # Consecutive special chars become one hyphen
        ("hello!!!world", "hello-world"),
        # 4. Trimming behavior (leading/trailing)
        ("  leading and trailing spaces  ", "leading-and-trailing-spaces"),
        ("--leading-hyphens", "leading-hyphens"),
        ("trailing-hyphens--", "trailing-hyphens"),
        # 5. Diacritics (accent) removal
        ("crème brûlée", "creme-brulee"),
        ("Björk's Gúnd", "bjork-s-gund"),
        ("¡Hola, Amigo!", "hola-amigo"),
        # 6. Non-ASCII "ignore" behavior (based on the code)
        ("python 🐍", "python"),  # Emojis are ignored
        ("Hello (World)", "hello-world"),
        # 7. "untitled" fallback behavior
        ("", "untitled"),
        (" ", "untitled"),  # A single space becomes a hyphen, which is stripped
        ("!@#$", "untitled"),  # Only special chars become a hyphen, which is stripped
        ("---", "untitled"),  # Only hyphens are stripped
        # 8. Number handling
        ("123 Go!", "123-go"),
        ("Version 2.0", "version-2-0"),
        ("2024-11-12", "2024-11-12"),
        # 9. Length limiting
        ("a" * 105, "a" * 100),  # Simple truncation
        # This tests the `rstrip('-')` after slicing
        (
            ("a" * 99) + "-b-c-d",
            "a" * 99,
        ),  # Slug is "a...a-b-c-d". Slice(100) is "a...a-". rstrip is "a...a"
        (
            ("a" * 100) + "-b",
            "a" * 100,
        ),  # Slug is "a...a-b". Slice(100) is "a...a". rstrip is "a...a"
        ("a" * 100, "a" * 100),  # Exactly 100 chars
        # 10. *** The MOST IMPORTANT test ***
        # This tests the code's *actual* behavior against its *documented* behavior.
        # The docstring example is "shu-ju-jie-gou-yu-suan-f",
        # but the code's use of .encode('ascii', 'ignore') will remove
        # these characters, leading to the "untitled" fallback.
        ("数据结构与算法", "shu-ju-jie-gou-yu-suan-fa"),
    ],
)
def test_slugify(input_text, expected_slug):
    """
    Tests the slugify function with various inputs.
    """
    assert slugify(input_text) == expected_slug


# A standalone test just for None, as parametrize might not handle it well
def test_slugify_none():
    """
    Tests that passing None raises a ValueError, as the function explicitly checks
    for None and raises this error type.
    """
    with pytest.raises(ValueError, match="text cannot be None"):
        slugify(None)
