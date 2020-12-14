# Projeto de Process Mining
Projeto de Process Mining desenvolvendo a descoberta de um modelo de processo utilizando o Alpha Miner como referência.

# Instalando dependências
Todas as dependências destes projeto estão definidas no arquivo `requirements.txt` e devem ser instaladas para a correta execução do projeto. Utilizando o gerenciador de pacotes `pip` é possível executar a instalação das dependências com o seguinte comando:
`pip install -r requirements.txt`

## Graphviz
Também se faz necessário a instalação do recurso Graphviz no sistema operacional. Para instalá-lo basta seguir as instruções de acordo com o sistema operacional. Para mais detalhes, veja na documentação oficial do recurso: https://graphviz.org/download/

### Instalação do Graphviz no Linux

#### Ubuntu 
```commandline
$ sudo apt install graphviz
```

#### Fedora
```commandline
$ sudo yum install graphviz
```

#### Debian
```commandline
$ sudo apt install graphviz
```

#### Outros
```commandline
$ sudo yum install graphviz
```

### Instalação do Graphviz no Mac
```commandline
$ brew install graphviz
```

### Instalação do Graphviz no Windows

#### Utilizando o Chocolatey
```commandline
> choco install graphviz
```

#### Utilizando o Windows Package Manager
```commandline
> winget install graphviz
```

# Executando o projeto
Este projeto considera um log em formato CSV como entrada, a exemplo do arquivo `simulation_logs.csv`. Após a instalação das dependências, é possível executar o projeto utilizando este simples comando:

```commandline
$ python main.py
```

Por padrão este comando utilizará o arquivo `simulation_logs.csv` como entrada e irá gerar uma imagem de uma Petri Net em formato PNG no arquivo `petrinet.png`.

## Definindo o arquivo de log de entrada
É possível definir o caminho do arquivo de entrada. Para isso deve-se substituir `[log_input_file.csv]` com o caminho do arquivo desejado no seguinte comando:
```commandline
$ python main.py [log_input_file.csv]
```

## Definindo o arquivo de log de entrada e o arquivo PNG de saída
É possível definir o caminho do arquivo de saída da imagem Petri Net gerada. Isto deve ser definido junto com o arquivo de entrada, precisando substituir `[log_input_file.csv]` com o caminho do arquivo de entrada e `[petrinet_png_file.png]` com o caminho desejado para o arquivo de saída:
```commandline
$ python main.py [log_input_file.csv] [petrinet_png_file.png]
```

