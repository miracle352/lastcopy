"""Breaks caught: lost repeats, stripped values, ignored namespaces/mixed text."""
import importlib.util
import pytest
from lastcopy.config import Settings
from lastcopy.inventory import ImportRejected


def compare(a, b):
    assert importlib.util.find_spec('lastcopy.xml_compare'), 'Ordered XML comparator is not implemented'
    from lastcopy.xml_compare import compare_xml
    return compare_xml(a.encode(), b.encode(), Settings({'SAMPLE_MODE': 'true'}))


def test_prefix_attribute_order_and_element_only_formatting_are_equal():
    result = compare('<a:r xmlns:a="urn:x" y="2" x="1"><a:n>001</a:n></a:r>',
                     '<b:r x="1" y="2" xmlns:b="urn:x">\n <b:n>001</b:n>\n</b:r>')
    assert result['equal'] and result['differences'] == []


@pytest.mark.parametrize('a,b', [
    ('<r><v>03</v><v>05</v></r>', '<r><v>03</v></r>'),
    ('<r><v>03</v><v>05</v></r>', '<r><v>05</v><v>03</v></r>'),
    ('<r>  Café </r>', '<r>Café</r>'), ('<r>001</r>', '<r>1</r>'),
    ('<r xmlns="urn:a"/>', '<r xmlns="urn:b"/>'),
    ('<r>A<b/> B</r>', '<r>A<b/>B</r>'),
    ('<r xml:space="preserve"> <v/> </r>', '<r xml:space="preserve"><v/></r>'),
    ('<r a="1"/>', '<r a="2"/>'),
])
def test_meaningful_changes_are_never_preserved(a, b):
    result = compare(a, b)
    assert not result['equal'] and result['differences']


def test_repeat_difference_names_expanded_path_and_occurrence():
    result = compare('<r xmlns="urn:x"><v>03</v><v>05</v></r>', '<r xmlns="urn:x"><v>03</v><v>07</v></r>')
    assert any(d['path'] == '/{urn:x}r[1]/{urn:x}v[2]' and d['indices'] == [1, 2] for d in result['differences'])


def test_hostile_xml_is_rejected_before_comparison():
    with pytest.raises(ImportRejected):
        compare('<!DOCTYPE r [<!ENTITY x "bad">]><r>&x;</r>', '<r/>')
