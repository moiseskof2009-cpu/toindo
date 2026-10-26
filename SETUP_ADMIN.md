# Toindo: app publico, painel separado e notificacoes

## Separacao dos servicos

- `app.py` atende passageiros e motoristas; nele nao existe rota administrativa.
- `admin_app.py` e um segundo servico Render, com URL propria, por exemplo `toindo-admin.onrender.com`.
- Ambos usam o mesmo PostgreSQL privado, mas com usuarios diferentes. O usuario do app publico deve poder apenas inserir cadastros e eventos; a conta administrativa le e atualiza registros.
- O app publico so chama a rota interna de notificacao com um token servidor-servidor. O corpo dessa chamada leva apenas o identificador do cadastro.
- So o servico administrativo recebe o token do WhatsApp e pode aprovar, pedir correcao, recusar e enviar mensagens.

## Publicar no Render

1. Use/crie um PostgreSQL privado do Toindo. O servico administrativo precisa iniciar primeiro para criar as tabelas.
2. Configure o servico publico com `gunicorn app:app --bind 0.0.0.0:$PORT`.
3. Crie um segundo Web Service no mesmo repositorio para o painel, com `gunicorn admin_app:app --bind 0.0.0.0:$PORT`. Dê a ele URL própria.
4. Configure `TOINDO_DATABASE_URL` nos dois servicos. No servico publico, use um usuario PostgreSQL de permissao restrita, apenas INSERT em `applications` e `events`; no administrativo, use um usuario com permissao de revisao.
5. Em um terminal seguro, rode `pip install -r requirements.txt` e `python admin_setup.py`. O script pede a senha sem exibi-la e gera o hash de senha, as duas chaves de sessao e a chave de criptografia. Cadastre cada valor como secret no servico correspondente; nao o grave no GitHub.
6. Defina `ADMIN_INTERNAL_TOKEN` como uma chave aleatoria forte nos dois servicos. No app publico, configure `ADMIN_INTERNAL_URL` com o endereco interno do servico administrativo, quando o plano permitir conexoes privadas de entrada. Caso contrario, use a URL HTTPS do painel; a rota aceita somente esse token e recebe apenas o ID do cadastro.

### Servico publico

- `TOINDO_DATABASE_URL` (usuario com permissao de insercao apenas)
- `PUBLIC_SESSION_SECRET`
- `PII_ENCRYPTION_KEY`
- `ADMIN_INTERNAL_URL`
- `ADMIN_INTERNAL_TOKEN`

### Servico administrativo

- `TOINDO_DATABASE_URL` (usuario administrativo)
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD_HASH`
- `ADMIN_SESSION_SECRET`
- `PII_ENCRYPTION_KEY` (mesma chave do servico publico)
- `ADMIN_INTERNAL_TOKEN` (mesma chave usada no app publico)
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_API_VERSION`
- `WHATSAPP_STATUS_TEMPLATE`
- `WHATSAPP_TEMPLATE_LANGUAGE` (opcional; padrao `pt_BR`)

Guarde uma copia protegida de `PII_ENCRYPTION_KEY`. Se ela for perdida ou trocada, os dados existentes nao poderao ser lidos.

## Mensagens automaticas e teste

Crie e aprove na Plataforma WhatsApp Business um modelo de atualizacao com tres variaveis no corpo: nome, status e orientacao. O Toindo usa esse modelo no recebimento do cadastro e quando o administrador aprova, pede correcao ou recusa. O botao **Reenviar WhatsApp** tenta enviar novamente o status atual.

O motorista precisa marcar o consentimento no cadastro. Sem consentimento, nenhuma mensagem automatica e enviada. Se o envio falhar ou faltar configuracao, a decisao continua registrada e o painel mostra o estado.

Para enviar uma mensagem de teste, entre no painel administrativo, informe seu proprio numero, marque a confirmacao de que ele e seu e envie. O teste usa o mesmo modelo aprovado e envia uma unica mensagem; nada e enviado enquanto as credenciais e o modelo nao estiverem configurados.

O formulario atual coleta informacoes digitadas sobre CNH e moto; upload de documentos e edicao segura de um cadastro existente ainda nao estao implementados. O motorista pode reenviar o cadastro, que cria uma nova solicitacao.
