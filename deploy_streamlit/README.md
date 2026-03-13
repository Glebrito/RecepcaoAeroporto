# ✈️ Painel de Gestão - Recepção Aeroporto

Dashboard interativo para análise de serviços de recepção no aeroporto, focado em clientes sem guia.

## 📊 Funcionalidades

- **Análise de Serviços**: Visualização dos principais serviços sem guia
- **Concentração por Dia**: Análise de passageiros por dia da semana
- **Análise de Horários**: Concentração de voos e passageiros por horário
- **Mapa de Calor**: Visualização cruzada de dia da semana vs horário
- **Detalhamento**: Visão detalhada por voo, serviço e horário
- **Recomendações**: Sugestões de horários de trabalho baseadas nos dados

## 🚀 Como Usar Localmente

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements_aeroporto.txt
```

3. Certifique-se de ter o arquivo `planilha_dados.csv` no diretório raiz

4. Execute o aplicativo:
```bash
streamlit run painel_recepcao_aeroporto.py
```

## 📦 Deploy no Streamlit Cloud

### Pré-requisitos
- Conta no GitHub
- Conta no [Streamlit Cloud](https://streamlit.io/cloud)
- Arquivo `planilha_dados.csv` com os dados

### Passos para Deploy

1. **Prepare o repositório no GitHub**:
   - Faça commit dos arquivos necessários:
     - `painel_recepcao_aeroporto.py`
     - `requirements_aeroporto.txt`
     - `planilha_dados.csv`

2. **Configure o Streamlit Cloud**:
   - Acesse https://share.streamlit.io/
   - Faça login com sua conta GitHub
   - Clique em "New app"
   - Selecione seu repositório, branch e arquivo principal
   - Em "Advanced settings":
     - Python version: 3.12
     - Main file path: `painel_recepcao_aeroporto.py`
     - Requirements file path: `requirements_aeroporto.txt`

3. **Deploy**:
   - Clique em "Deploy!"
   - Aguarde alguns minutos para o app ficar online

## 📋 Estrutura de Dados

O arquivo `planilha_dados.csv` deve conter as seguintes colunas:
- `Data`: Data do serviço (formato DD/MM/YYYY)
- `Tipo do Serviço`: IN (chegadas) ou OUT (saídas)
- `Guia`: Nome do guia ou "Sem Guia"
- `Serviço`: Tipo de serviço prestado
- `Voo`: Número do voo
- `Horário de Voo`: Horário (formato HH:MM)
- `Adt`: Número de adultos
- `Chd`: Número de crianças
- `Código`: Código do serviço

## 🔧 Tecnologias

- **Streamlit**: Framework para criação do dashboard
- **Pandas**: Manipulação de dados
- **Plotly**: Visualizações interativas
- **NumPy**: Operações numéricas

## 📝 Notas

- O painel filtra automaticamente apenas serviços IN (chegadas) sem guia
- Exclui serviços de tripulação
- Considera apenas voos a partir das 8:00
