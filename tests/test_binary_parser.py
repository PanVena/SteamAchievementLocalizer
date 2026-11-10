import unittest

from plugins.binary_parser import BinaryParser


class BinaryParserTests(unittest.TestCase):
    def test_splits_numeric_records_at_name_markers(self):
        def record(index, title, description):
            next_index = str(index + 1).encode()
            return (
                b'\x00' + str(index).encode() + b'\x00\x01name\x00' + next_index
                + b'\x00\x00display\x00\x00name\x00\x01english\x00' + title.encode()
                + b'\x00\x01german\x00Titel\x00\x00desc\x00\x01english\x00'
                + description.encode() + b'\x00\x01german\x00Beschreibung\x00'
            )

        data = (
            b'\x001234\x00\x00stats\x00\x001\x00\x00bits\x00'
            + record(0, 'First title', 'First description')
            + record(1, 'Second title', 'Second description')
        )

        rows, _ = BinaryParser().parse_binary_data(data)

        self.assertEqual(
            [(row['key'], row['english']) for row in rows],
            [
                ('1', 'First title'),
                ('1_opis', 'First description'),
                ('2', 'Second title'),
                ('2_opis', 'Second description'),
            ],
        )

    def test_keeps_legacy_numeric_snippet_splitting(self):
        chunks = BinaryParser().split_chunks(b'0\x00first\x001\x00second')

        self.assertEqual(chunks, [b'0\x00first', b'\x001\x00second'])


if __name__ == '__main__':
    unittest.main()
