from tortoise.validators import Validator


class RegexValidator(Validator):
    """
    A validator to validate the given value whether match regex or not.
    """

    def __init__(self, pattern: str, flags: Union[int, re.RegexFlag]):
        self.regex = re.compile(pattern, flags)

    def __call__(self, value: Any):
        if not self.regex.match(value):
            raise ValidationError(f"Value '{value}' does not match regex '{self.regex.pattern}'")
