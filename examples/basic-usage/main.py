"""Basic example demonstrating Lithic-CLI usage."""


def greet(name: str) -> str:
    """Return a greeting message.

    Args:
        name: The name to greet.

    Returns:
        A greeting string.
    """
    return f"Hello, {name}!"


def calculate_sum(numbers: list[int]) -> int:
    """Calculate the sum of a list of numbers.

    Args:
        numbers: List of integers to sum.

    Returns:
        The sum of all numbers.
    """
    return sum(numbers)


class Calculator:
    """Simple calculator class for demonstration."""

    def add(self, a: float, b: float) -> float:
        """Add two numbers.

        Args:
            a: First number.
            b: Second number.

        Returns:
            Sum of a and b.
        """
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a.

        Args:
            a: First number.
            b: Second number.

        Returns:
            Difference of a and b.
        """
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers.

        Args:
            a: First number.
            b: Second number.

        Returns:
            Product of a and b.
        """
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Divide a by b.

        Args:
            a: Numerator.
            b: Denominator.

        Returns:
            Quotient of a and b.

        Raises:
            ValueError: If b is zero.
        """
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b


if __name__ == "__main__":
    print(greet("World"))
    print(f"Sum: {calculate_sum([1, 2, 3, 4, 5])}")

    calc = Calculator()
    print(f"Add: {calc.add(10, 5)}")
    print(f"Divide: {calc.divide(10, 3)}")
