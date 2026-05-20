import json

from folio_sync.handler import extract_s3_records


def test_extract_s3_records_sqs_sns_s3():
    # Arrange
    s3_event = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {"bucket": {"name": "my-bucket"}, "object": {"key": "test.md"}},
            }
        ]
    }
    sns_message = {"Message": json.dumps(s3_event)}
    sqs_event = {"Records": [{"body": json.dumps(sns_message)}]}

    # Act
    records = extract_s3_records(sqs_event)

    # Assert
    assert len(records) == 1
    assert records[0]["s3"]["bucket"]["name"] == "my-bucket"
    assert records[0]["s3"]["object"]["key"] == "test.md"


def test_extract_s3_records_sqs_s3_direct():
    # Arrange
    s3_event = {
        "Records": [
            {
                "eventSource": "aws:s3",
                "s3": {"bucket": {"name": "my-bucket"}, "object": {"key": "test2.md"}},
            }
        ]
    }
    sqs_event = {"Records": [{"body": json.dumps(s3_event)}]}

    # Act
    records = extract_s3_records(sqs_event)

    # Assert
    assert len(records) == 1
    assert records[0]["s3"]["object"]["key"] == "test2.md"


def test_extract_s3_records_empty():
    assert extract_s3_records({}) == []
    assert extract_s3_records({"Records": []}) == []
