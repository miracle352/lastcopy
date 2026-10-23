"""Expanded names, ordered occurrences and exact meaningful XML text.

Only whitespace between element-only children is formatting. If any direct text
is non-whitespace, all text/tails in that parent are significant (mixed content).
xml:space is inherited; xml:space=default resets it. No field is ignored.
"""
from itertools import zip_longest
from collections import Counter
from .inventory import parse_xml

SPACE = '{http://www.w3.org/XML/1998/namespace}space'


def xml_facts(data, settings):
    root = parse_xml(data, settings)
    facts = []

    def visit(node, path, indices, preserve=False, tail=None):
        space = node.attrib.get(SPACE)
        preserve = True if space == 'preserve' else False if space == 'default' else preserve
        mixed = any(text and not text.isspace() for text in [node.text, *(child.tail for child in node)])
        formatting = len(node) > 0 and not mixed and not preserve
        facts.append({'path': path, 'indices': indices, 'name': node.tag,
                      'attributes': dict(sorted(node.attrib.items())),
                      'text': None if formatting else node.text, 'tail': tail})
        counts = Counter()
        for child in node:
            counts[child.tag] += 1
            visit(child, f'{path}/{child.tag}[{counts[child.tag]}]',
                  indices + [counts[child.tag]], preserve, None if formatting else child.tail)

    visit(root, f'/{root.tag}[1]', [1])
    return facts


def compare_xml(source, server, settings):
    left, right = xml_facts(source, settings), xml_facts(server, settings)
    differences = []
    count = 0
    for a, b in zip_longest(left, right):
        if a != b:
            count += 1
            if len(differences) < 64:
                location = a or b
                differences.append({'path': location['path'], 'indices': location['indices'],
                                    'source': a, 'server': b})
    return {'equal': count == 0, 'differences': differences,
            'difference_count': count, 'details_truncated': count > 64}
