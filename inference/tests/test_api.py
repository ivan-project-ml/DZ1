def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert "version" in r.json()


def test_ready(client):
    assert client.get("/ready").status_code == 200


def test_bad_payload_is_422(client):
    r = client.post("/v1/predict", json={"text": ''})
    assert r.status_code == 422


def test_missing_field_is_422(client, good_row):
    row = dict(good_row)
    del row["text"]
    assert client.post("/v1/predict", json=row).status_code == 422


def test_extra_field_is_422(client, good_row):
    r = client.post("/v1/predict", json={**good_row, "hacker_field": 1})
    assert r.status_code == 422

def test_prediction_depends_on_text(client):
    ham_text = "Some text"
    spam_text = (
        "WINNER!! As a valued network customer you have been selected to receivea ВЈ900 prize reward! To claim call 09061701461. Claim code KL341. Valid 12 hours only."
    )

    ham_response = client.post(
        "/v1/predict",
        json={"text": ham_text},
    )
    spam_response = client.post(
        "/v1/predict",
        json={"text": spam_text},
    )

    assert ham_response.status_code == 200
    assert spam_response.status_code == 200

    ham_label = ham_response.json()["label"]
    spam_label = spam_response.json()["label"]

    assert ham_label != spam_label

