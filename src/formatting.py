def currency(value):
    return 'Não informado para a competência' if value is None else ('R$ '+f'{value:,.2f}'.replace(',','X').replace('.',',').replace('X','.'))
