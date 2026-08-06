# XML automático — RC Caminhões Multimarcas

Este projeto consulta o estoque público do site da RC Caminhões e gera o arquivo:

`docs/estoque.xml`

O GitHub Actions executa a atualização automaticamente a cada hora.

## Como publicar

1. Crie uma conta gratuita no GitHub.
2. Crie um repositório público chamado `estoque-rc`.
3. Envie todos os arquivos deste pacote para o repositório.
4. No repositório, abra **Settings > Actions > General**.
5. Em **Workflow permissions**, marque **Read and write permissions** e salve.
6. Abra **Actions > Atualizar XML do estoque > Run workflow**.
7. Depois abra **Settings > Pages**.
8. Em **Build and deployment**, escolha:
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/docs**
9. Salve.

O link ficará parecido com:

`https://SEU-USUARIO.github.io/estoque-rc/estoque.xml`

## Domínio personalizado opcional

Depois, o domínio pode ser configurado como:

`https://xml.rccaminhoesmultimarcas.com.br/estoque.xml`

Isso exige criar um registro DNS apontando o subdomínio para o GitHub Pages.

## Observações

- O arquivo é atualizado aproximadamente uma vez por hora.
- Veículos retirados do site saem do XML na atualização seguinte.
- Veículos adicionados ao site entram no XML na atualização seguinte.
- Se o fornecedor alterar a estrutura do site, o extrator pode precisar de ajuste.