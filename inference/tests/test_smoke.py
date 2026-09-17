def test_predict_smoke(client, good_row):
    r = client.post("/v1/predict", json=good_row)
    assert r.status_code == 200
    body = r.json()
    assert body["label"] in ('0', '1')
    assert body["latency_ms"] >= 0
    assert body["version"]


def test_batch_and_single_agree(client, good_row):
    s1 = client.post("/v1/predict", json=good_row).json()["label"]
    s2 = client.post("/v1/predict", json=good_row).json()["label"]
    assert s1 == s2