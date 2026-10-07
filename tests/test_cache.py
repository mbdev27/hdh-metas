import os
from src.cache import file_version,yaml_versioned,csv_versioned


def test_file_cache_changes_with_file_version(tmp_path):
    file=tmp_path/'rules.yaml';file.write_text('value: 1\n')
    first=file_version(file)
    assert yaml_versioned(first)=={'value':1}
    file.write_text('value: 2\n')
    os.utime(file,ns=(first[1]+1_000_000,first[1]+1_000_000))
    assert file_version(file)!=first
    assert yaml_versioned(file_version(file))=={'value':2}


def test_cached_csv_returns_isolated_copy(tmp_path):
    file=tmp_path/'data.csv';file.write_text('competencia,value\n2026-01,10\n')
    version=file_version(file)
    first=csv_versioned(version);first.loc[0,'value']=0
    assert csv_versioned(version).loc[0,'value']==10
