Vamos desenvolver um sistema que auxilie a transferencia de produtos de uma filial para outra. Será uma tela simples que receberá um arquivo xls com um relatorio de vendas de tudo que vendeu da filial naquela semana. ele deve analisar o arquivo e gerar um arquivo xml da danfe com todos os produtos e quantidades do relatorio. Exemplo: o relatorio da filial diz que vendeu 10 pçs do produto x, ele deve criar uma danfe com 10 pçs do produto x. Segue um arquivo de exemplo do relatorio da filial e um exemplo do xml que ele deve gerar

Os campos de destinatario e remetentes devem ser sempre iguais

a empresa é ARBORETHO IMPORTS LTDA
CNPJ: 40.484.774/0001-50
IE: 108282910
Rua 19, 230 Qd.46 Lt.08-a Setor Santo Antonio, Goiania - GO, 74853-320


O xml deve ser gerado com todos os campos preenchidos de acordo com o exemplo. Usando os produtos presentes no relatorio. 

---- Informaçoes de desenvolvimento-- 

O programa será desenvolvido usando Python como linguagem de processamento, utilizando arquitetura SOLID com os classicos padroes de clean arc e clean code. O desenvolvimento deve ser baseado em TDD com testes unitarios para cada função.

é de extrema importancia o cuidado com a segurança, Sendo assim cada função deve ser robusta e segura, utilizando validações de dados e tratamento de erros. Alem de camadas independentemente seguras.

A interface visual deve ser simples e objetiva, A tela Terá um botão para selecionar o relatorio, Após carregado ele deve apresentar os produtos com suas quantidades e um botão para baixar o xml. 

é de extrema importancia o desenvolvimento de uma função para analisar o documento carregado, garantindo que ele seja um arquivo que siga os padroes do relatorio de exemplo e nao possua nenhum tipo de outra informação que pode ser prejudicial ao codigo. 

Para a hospedagem e deploy usaremos a versel, com um banco de dados local no computador do usuario, uma vez que nao sera necessario a reutilização daquelas informações depois que o xml for baixado. Sendo assim, cada novo relatorio deve ser processado do zero.

