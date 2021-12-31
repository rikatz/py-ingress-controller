from unittest.mock import (
    mock_open,
    patch
)

from utils import write_config


def test_write_config():
    mock = mock_open()

    with patch("utils.open", mock, create=True):
        write_config("ingress.conf", "attribute = value")

    mock.assert_called_with("ingress.conf", "w")
    mock.return_value.write.assert_called_once_with("attribute = value")
