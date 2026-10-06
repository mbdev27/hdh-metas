import getpass,bcrypt
if __name__=='__main__':
    password=getpass.getpass('Senha a configurar: ')
    if not password:raise SystemExit('Senha vazia não permitida')
    if password!=getpass.getpass('Confirme a senha: '):raise SystemExit('Senhas diferentes')
    print(bcrypt.hashpw(password.encode(),bcrypt.gensalt(rounds=12)).decode())
