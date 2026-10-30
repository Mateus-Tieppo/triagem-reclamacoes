import pandas as pd
import pytest

from triagem.verdade import conferir_atraso


def test_conferir_atraso():
    tri = pd.DataFrame({"review_id": ["a", "b", "c"], "categoria": ["nao_recebido_atraso", "nao_recebido_atraso", "outro"],
                        "order_id": ["1", "2", "3"]})
    ped = pd.DataFrame({"order_id": ["1", "2", "3"], "order_status": ["delivered", "canceled", "delivered"],
                        "order_delivered_customer_date": ["2018-01-10", None, "2018-01-01"],
                        "order_estimated_delivery_date": ["2018-01-05", "2018-01-05", "2018-01-05"]})
    r = conferir_atraso(tri, ped)
    assert r["n_atraso"] == 2
    assert r["pct_atrasado_entre_atraso"] == 1.0
    assert r["pct_atrasado_geral"] == pytest.approx(2 / 3)
