import pytest
from lastcopy.config import Settings
from lastcopy.inventory import ImportRejected,parse_xml
from lastcopy.xml_compare import xml_facts
import lastcopy.inventory as module


@pytest.mark.parametrize('data',[
    ('<'+('r'*200000)+'>'+('<photo>x</photo>'*9000)+'</'+('r'*200000)+'>').encode(),
    ('<r xmlns="'+('n'*200000)+'">'+''.join(f'<p{i}/>' for i in range(3000))+'</r>').encode(),
    ('<root>'+('<'+('n'*240)+'>')*20+('</'+('n'*240)+'>')*20+'</root>').encode(),
],ids=['long_name','expanded_namespace','deep_path'])
def test_compact_xml_cannot_expand_unbounded_names_and_paths(data):
    assert len(data)<1048576
    with pytest.raises(ImportRejected,match='name|namespace|path'):
        parse_xml(data,Settings({'SAMPLE_MODE':'true'}))


def test_ordinary_namespaces_and_ordered_repeats_stay_intact():
    facts=xml_facts(b'<r xmlns="urn:lastcopy:test"><p>one</p><p>two</p></r>',Settings({'SAMPLE_MODE':'true'}))
    assert [(f['path'],f['text']) for f in facts[1:]]==[
        ('/{urn:lastcopy:test}r[1]/{urn:lastcopy:test}p[1]','one'),
        ('/{urn:lastcopy:test}r[1]/{urn:lastcopy:test}p[2]','two')]


def test_namespace_limit_is_checked_before_tree_parser_expansion(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Tree parser reached before namespace bound')
    monkeypatch.setattr(module,'iterparse',forbidden)
    data=('<r xmlns="'+('n'*200000)+'">'+''.join(f'<p{i}/>' for i in range(2000))+'</r>').encode()
    with pytest.raises(ImportRejected,match='namespace'):parse_xml(data,Settings({'SAMPLE_MODE':'true'}))
