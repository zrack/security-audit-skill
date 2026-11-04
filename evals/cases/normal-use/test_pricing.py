import unittest

from pricing import format_price


class PriceTests(unittest.TestCase):
    def test_whole_and_fractional_labels(self):
        self.assertEqual(format_price(0), "USD 0.00")
        self.assertEqual(format_price(7), "USD 0.07")
        self.assertEqual(format_price(1234), "USD 12.34")

    def test_rejects_invalid_values(self):
        for value in (-1, 1.5, True, "100"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    format_price(value)


if __name__ == "__main__":
    unittest.main()
