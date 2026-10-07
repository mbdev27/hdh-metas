import pandas as pd
from src.historical import real_data
from src.management import production_summary,quality_summary,comparable_annual
from src.charts import achievement_chart,quality_numeric_chart


def test_summary_preserves_missing_and_separates_statuses():
    p,q=real_data()
    rows=production_summary(p,'018/2022','2026-01')
    assert len(rows)==9
    missing=rows[rows.indicator_id=='Q08'].iloc[0]
    assert missing.situacao=='Sem dados' and pd.isna(missing.atingimento)
    result=quality_summary(q,'018/2022','2026-01')
    assert result[result.indicator_id=='QL01'].iloc[0].situacao=='Inconsistência'
    assert result[result.indicator_id=='QL10'].iloc[0].situacao=='Atingida'


def test_change_not_compared_across_rules():
    p,_=real_data()
    rows=production_summary(p,'018/2022','2024-07')
    assert pd.isna(rows[rows.indicator_id=='Q03'].iloc[0].variacao_pp)
    rows=production_summary(p,'018/2022','2026-02')
    value=rows[rows.indicator_id=='Q03'].iloc[0]
    before=p[(p.indicator_id=='Q03')&(p.competencia=='2026-01')].iloc[0]
    assert abs(value.variacao_pp-(value.atingimento-before.atingimento))<1e-8


def test_same_month_comparison_does_not_extrapolate():
    p,_=real_data()
    rows=comparable_annual(p[(p.indicator_id=='Q01')&(p.contrato=='018/2022')],True)
    assert set(rows.competencia.str[5:7])=={'01','02','03'}
    assert set(rows.competencia.str[:4])=={'2023','2024','2025','2026'}


def test_graph_references_and_missing_values():
    p,q=real_data()
    figure=achievement_chart(p[p.indicator_id=='Q03'])
    assert {shape.y0 for shape in figure.layout.shapes}=={85,100}
    figure=quality_numeric_chart(q[q.indicator_id=='QL10'])
    assert all(trace.connectgaps is False for trace in figure.data)
    assert any(trace.name=='Meta' for trace in figure.data)
