"""File-versioned caches for public data only. Uploaded/session data are never cached."""
from pathlib import Path
import json
import pandas as pd
import streamlit as st
import yaml


def file_version(path):
    path=Path(path)
    stat=path.stat()
    return (str(path.resolve()),stat.st_mtime_ns,stat.st_size)


def versions(paths):
    return tuple(file_version(path) for path in paths)


@st.cache_data(max_entries=64,show_spinner=False)
def yaml_versioned(version):
    return yaml.safe_load(Path(version[0]).read_text(encoding='utf8'))


@st.cache_data(max_entries=32,show_spinner=False)
def json_versioned(version):
    return json.loads(Path(version[0]).read_text(encoding='utf8'))


@st.cache_data(max_entries=16,show_spinner=False)
def csv_versioned(version):
    return pd.read_csv(version[0],dtype={'competencia':str})


@st.cache_data(max_entries=16,show_spinner=False)
def bytes_versioned(version):
    return Path(version[0]).read_bytes()
