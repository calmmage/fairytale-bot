from fairytale_bot.lib import MyApp


def test_extract_story_parts():
    """
    Test the _extract_story_parts function
    """
    # Arrange
    story_structure = """
    header
    - part 1
    - part 2
    - part 3
    """
    expected_output = ["- part 1", "- part 2", "- part 3"]

    # Act
    output = MyApp._extract_story_parts(story_structure)

    # Assert
    assert output == expected_output, f"Expected {expected_output}, but got {output}"
